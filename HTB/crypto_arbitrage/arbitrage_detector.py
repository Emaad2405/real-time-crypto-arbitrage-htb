"""Arbitrage opportunity detection and analysis."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from collections import deque
import pandas as pd
from loguru import logger

from config import (
    PriceData, ArbitrageOpportunity, EXCHANGE_CONFIGS,
    MIN_PROFIT_THRESHOLD, MAX_SPREAD_AGE_SECONDS, DATA_BUFFER_SIZE
)


class ArbitrageDetector:
    """Detects arbitrage opportunities across exchanges."""

    def __init__(self):
        self.price_buffer: Dict[str, deque] = {}  # {symbol: deque of (exchange, PriceData)}
        self.opportunities: List[ArbitrageOpportunity] = []
        self.latest_prices: Dict[tuple, PriceData] = {}  # {(exchange, symbol): PriceData} - conveneient reference to latest prices for ongoing arbitrage calculations

        # Count total opportunities found and opportunities by pair of exchanges
        self.total_opportunities_found = 0
        self.opportunities_by_pair = {}

    def update_price(self, price_data: PriceData):
        """Update latest price and check for arbitrage."""
        key = (price_data.exchange, price_data.symbol)
        self.latest_prices[key] = price_data

        # IF subscribed to a new symbol, initialize its thread-safe deque buffer
        if price_data.symbol not in self.price_buffer:
            self.price_buffer[price_data.symbol] = deque(maxlen=DATA_BUFFER_SIZE)

        self.price_buffer[price_data.symbol].append({
            'exchange': price_data.exchange,
            'symbol': price_data.symbol,  
            'price': price_data.price,
            'timestamp': price_data.timestamp,
            'bid': price_data.bid,
            'ask': price_data.ask,
            'volume': price_data.volume
        })

        # Check for arbitrage opportunities for one crytpocurrency across multiple exchanges
        self._check_arbitrage(price_data.symbol)

    def _check_arbitrage(self, symbol: str):
        """Check for arbitrage opportunities for a given symbol."""
        # Get all recent prices for this symbol
        relevant_prices = [
            (exchange, data)
            for (exchange, sym), data in self.latest_prices.items()
            if sym == symbol
        ]

        if len(relevant_prices) < 2:
            return  # Need at least 2 exchanges

        # Filter out stale prices
        now = datetime.now(timezone.utc)
        fresh_prices = [
            (exchange, data)
            for exchange, data in relevant_prices
            if (now - data.timestamp).total_seconds() < MAX_SPREAD_AGE_SECONDS
        ]
        if len(fresh_prices) < 2:
            return

        # Find all profitable pairs
        for i, (exchange1, data1) in enumerate(fresh_prices):
            for exchange2, data2 in fresh_prices[i + 1:]:
                # Check both directions
                self._analyze_pair(exchange1, data1, exchange2, data2)
                self._analyze_pair(exchange2, data2, exchange1, data1)

    def _analyze_pair(
        self,
        buy_exchange: str,
        buy_data: PriceData,
        sell_exchange: str,
        sell_data: PriceData
    ):
        """Analyze a specific buy/sell pair for arbitrage."""
        # Use ask price for buying, bid price for selling (if available)
        buy_price = buy_data.ask if buy_data.ask > 0 else buy_data.price
        sell_price = sell_data.bid if sell_data.bid > 0 else sell_data.price

        # Calculate spread
        if buy_price <= 0 or sell_price <= 0:
            return

        spread_pct = ((sell_price - buy_price) / buy_price) * 100

        # Get exchange fees
        buy_fee = self._get_exchange_fee(buy_exchange)
        sell_fee = self._get_exchange_fee(sell_exchange)

        # Calculate profit after fees
        total_fee_pct = buy_fee + sell_fee
        profit_after_fees = spread_pct - total_fee_pct

        # Check if profitable
        if profit_after_fees >= MIN_PROFIT_THRESHOLD:
            opportunity = ArbitrageOpportunity(
                buy_exchange=buy_exchange,
                sell_exchange=sell_exchange,
                symbol=buy_data.symbol,
                buy_price=buy_price,
                sell_price=sell_price,
                spread_pct=spread_pct,
                profit_after_fees=profit_after_fees,
                timestamp=datetime.now(timezone.utc)
            )

            self.opportunities.append(opportunity)
            self.total_opportunities_found += 1

            # Track by pair
            pair_key = f"{buy_exchange}->{sell_exchange}:{buy_data.symbol}"
            self.opportunities_by_pair[pair_key] = \
                self.opportunities_by_pair.get(pair_key, 0) + 1

            logger.success(
                f"ARBITRAGE FOUND: Buy {buy_data.symbol} on {buy_exchange} @ ${buy_price:.2f}, "
                f"Sell on {sell_exchange} @ ${sell_price:.2f} | "
                f"Profit: {profit_after_fees:.2f}%"
            )

    def _get_exchange_fee(self, exchange_name: str) -> float:
        """Get fee percentage for an exchange."""
        for exchange, config in EXCHANGE_CONFIGS.items():
            if config.name == exchange_name:
                return config.fee_pct
        return 0.5  # Default conservative estimate

    def get_recent_opportunities(self, minutes: int = 5) -> List[ArbitrageOpportunity]:
        """Get opportunities from the last N minutes."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            opp for opp in self.opportunities
            if opp.timestamp >= cutoff_time
        ]

    def get_best_opportunity(self) -> Optional[ArbitrageOpportunity]:
        """Get the most profitable recent opportunity."""
        recent = self.get_recent_opportunities(minutes=1)
        if not recent:
            return None
        return max(recent, key=lambda x: x.profit_after_fees)

    def get_latest_prices(self, symbol: str) -> Dict[str, PriceData]:
        """Get latest prices for a specific symbol across all exchanges."""
        prices = {}
        for (exchange, sym), price_data in self.latest_prices.items():
            if sym == symbol:
                prices[exchange] = price_data
        return prices

    def get_statistics(self) -> Dict:
        """Get detection statistics."""
        recent_opps = self.get_recent_opportunities(minutes=60)

        if not recent_opps:
            return {
                'total_opportunities': self.total_opportunities_found,
                'recent_count': 0,
                'avg_profit': 0,
                'max_profit': 0,
                'top_pairs': []
            }

        profits = [opp.profit_after_fees for opp in recent_opps]

        # Top 5 exchange pairs
        top_pairs = sorted(
            self.opportunities_by_pair.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_opportunities': self.total_opportunities_found,
            'recent_count': len(recent_opps),
            'avg_profit': sum(profits) / len(profits),
            'max_profit': max(profits),
            'min_profit': min(profits),
            'top_pairs': [{'pair': pair, 'count': count} for pair, count in top_pairs]
        }

    def get_historical_data(self, symbol: str) -> pd.DataFrame:
        """Get historical price data for ML training."""
        if symbol not in self.price_buffer:
            return pd.DataFrame()

        data = list(self.price_buffer[symbol])
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        return df

    def calculate_spread_metrics(self, symbol: str) -> Dict:
        """Calculate spread statistics for a symbol."""
        df = self.get_historical_data(symbol)

        if df.empty or len(df) < 2:
            return {}

        # Pivot to get prices by exchange
        pivot = df.pivot_table(
            index='timestamp',
            columns='exchange',
            values='price',
            aggfunc='mean'
        ).ffill()

        if len(pivot.columns) < 2:
            return {}

        # Calculate spreads between all exchange pairs
        spreads = {}
        exchanges = list(pivot.columns)

        for i, ex1 in enumerate(exchanges):
            for ex2 in exchanges[i + 1:]:
                spread = ((pivot[ex2] - pivot[ex1]) / pivot[ex1]) * 100
                spreads[f"{ex1}->{ex2}"] = {
                    'mean': spread.mean(),
                    'std': spread.std(),
                    'max': spread.max(),
                    'min': spread.min(),
                    'current': spread.iloc[-1] if len(spread) > 0 else 0
                }

        return spreads


class BacktestEngine:
    """Backtest arbitrage strategies on historical data."""

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.portfolio = {}

    def execute_opportunity(self, opportunity: ArbitrageOpportunity):
        """Simulate executing an arbitrage trade."""
        # Simple simulation: invest 10% of capital per trade
        investment = self.capital * 0.1

        if investment < 100:  # Minimum trade size
            return

        # Calculate returns
        profit = investment * (opportunity.profit_after_fees / 100)

        self.capital += profit
        self.trades.append({
            'timestamp': opportunity.timestamp,
            'symbol': opportunity.symbol,
            'profit': profit,
            'profit_pct': opportunity.profit_after_fees,
            'capital_after': self.capital
        })

    def get_results(self) -> Dict:
        """Get backtest results."""
        if not self.trades:
            return {
                'total_trades': 0,
                'total_return': 0,
                'total_return_pct': 0,
                'win_rate': 0,
                'avg_profit_per_trade': 0
            }

        total_return = self.capital - self.initial_capital
        winning_trades = [t for t in self.trades if t['profit'] > 0]

        return {
            'total_trades': len(self.trades),
            'total_return': total_return,
            'total_return_pct': (total_return / self.initial_capital) * 100,
            'win_rate': (len(winning_trades) / len(self.trades)) * 100,
            'avg_profit_per_trade': sum(t['profit'] for t in self.trades) / len(self.trades),
            'final_capital': self.capital
        }
