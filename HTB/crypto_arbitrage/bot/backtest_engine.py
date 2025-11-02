"""Backtesting engine for arbitrage bots."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from .base_bot import BaseBot, Trade
from .trade_logger import TradeLogger
from config import ArbitrageOpportunity


class BacktestEngine:
    """
    Backtesting engine that runs bots on historical data.

    Supports:
    - Multiple bots running in parallel
    - Realistic execution simulation
    - Performance comparison
    - Trade logging
    """

    def __init__(
        self,
        bots: List[BaseBot],
        slippage_pct: float = 0.1,
        execution_time_ms: float = 100.0
    ):
        """
        Initialize backtest engine.

        Args:
            bots: List of bots to backtest
            slippage_pct: Price slippage percentage
            execution_time_ms: Simulated execution time
        """
        self.bots = bots
        self.slippage_pct = slippage_pct
        self.execution_time_ms = execution_time_ms

        self.trade_logger = TradeLogger()
        self.opportunities_processed = 0

    def load_opportunities_from_csv(self, csv_path: str) -> List[ArbitrageOpportunity]:
        """
        Load arbitrage opportunities from CSV file.

        Args:
            csv_path: Path to opportunities CSV

        Returns:
            List of ArbitrageOpportunity objects
        """
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} opportunities from {csv_path}")

            opportunities = []
            for _, row in df.iterrows():
                opp = ArbitrageOpportunity(
                    symbol=row['symbol'],
                    buy_exchange=row['buy_exchange'],
                    sell_exchange=row['sell_exchange'],
                    buy_price=row['buy_price'],
                    sell_price=row['sell_price'],
                    spread_pct=row['spread_pct'],
                    profit_after_fees=row['profit_after_fees'],
                    timestamp=pd.to_datetime(row['timestamp'])
                )
                opportunities.append(opp)

            return opportunities

        except Exception as e:
            logger.error(f"Error loading opportunities from CSV: {e}")
            return []

    def load_latest_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Load opportunities from the latest CSV in captured_data/.

        Returns:
            List of ArbitrageOpportunity objects
        """
        try:
            captured_dir = Path('captured_data')
            if not captured_dir.exists():
                logger.error("captured_data/ directory not found")
                return []

            # Find latest opportunities CSV
            opp_files = list(captured_dir.glob('opportunities_*.csv'))
            if not opp_files:
                logger.error("No opportunities CSV files found")
                return []

            latest_file = max(opp_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Loading latest opportunities from {latest_file.name}")

            return self.load_opportunities_from_csv(str(latest_file))

        except Exception as e:
            logger.error(f"Error loading latest opportunities: {e}")
            return []

    def run_backtest(
        self,
        opportunities: Optional[List[ArbitrageOpportunity]] = None,
        max_opportunities: Optional[int] = None
    ) -> Dict[str, dict]:
        """
        Run backtest on opportunities.

        Args:
            opportunities: List of opportunities (loads latest if None)
            max_opportunities: Maximum number of opportunities to process

        Returns:
            Dictionary of bot performance metrics
        """
        # Load opportunities if not provided
        if opportunities is None:
            opportunities = self.load_latest_opportunities()

        if not opportunities:
            logger.error("No opportunities to backtest")
            return {}

        # Sort by timestamp
        opportunities = sorted(opportunities, key=lambda x: x.timestamp)

        # Limit if specified
        if max_opportunities:
            opportunities = opportunities[:max_opportunities]

        logger.info(f"Starting backtest with {len(opportunities)} opportunities")
        logger.info(f"Testing {len(self.bots)} bots")

        # Reset all bots
        for bot in self.bots:
            bot.reset()

        # Process each opportunity
        start_time = datetime.now()

        for i, opportunity in enumerate(opportunities):
            self.opportunities_processed = i + 1

            # Let each bot decide whether to trade
            for bot in self.bots:
                trade = bot.execute_trade(
                    opportunity,
                    slippage_pct=self.slippage_pct,
                    execution_time_ms=self.execution_time_ms
                )

                # Log trade if executed
                if trade:
                    self.trade_logger.log_trade(trade)

            # Progress logging
            if (i + 1) % 10000 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = (i + 1) / elapsed
                logger.info(
                    f"Processed {i + 1}/{len(opportunities)} opportunities "
                    f"({rate:.1f} opp/sec)"
                )

        # Calculate final metrics
        results = {}
        for bot in self.bots:
            metrics = bot.get_performance_metrics()
            results[bot.name] = metrics

            logger.info(f"\n{bot.name} Results:")
            logger.info(f"  Total Trades: {metrics['total_trades']}")
            logger.info(f"  Win Rate: {metrics['win_rate']:.2f}%")
            logger.info(f"  Net Profit: ${metrics['net_profit']:.2f}")
            logger.info(f"  Return: {metrics['return_pct']:.2f}%")
            logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
            logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")

        # Save trade logs and summary
        self.trade_logger.save_summary(results)

        elapsed_total = (datetime.now() - start_time).total_seconds()
        logger.success(
            f"Backtest complete! Processed {len(opportunities)} opportunities "
            f"in {elapsed_total:.1f} seconds"
        )

        return results

    def compare_bots(self) -> pd.DataFrame:
        """
        Create comparison DataFrame of bot performance.

        Returns:
            DataFrame with bot comparison metrics
        """
        comparison_data = []

        for bot in self.bots:
            metrics = bot.get_performance_metrics()
            comparison_data.append({
                'Bot': metrics['bot_name'],
                'Total Trades': metrics['total_trades'],
                'Win Rate (%)': metrics['win_rate'],
                'Net Profit ($)': metrics['net_profit'],
                'Return (%)': metrics['return_pct'],
                'Avg Profit/Trade ($)': metrics['avg_profit_per_trade'],
                'Sharpe Ratio': metrics['sharpe_ratio'],
                'Max Drawdown (%)': metrics['max_drawdown'],
                'Profit Factor': metrics['profit_factor'],
                'Total Fees ($)': metrics['total_fees'],
                'Total Slippage ($)': metrics['total_slippage'],
            })

        df = pd.DataFrame(comparison_data)
        return df

    def get_trade_history(self, bot_name: Optional[str] = None) -> List[Trade]:
        """
        Get trade history for a specific bot or all bots.

        Args:
            bot_name: Name of bot (None for all bots)

        Returns:
            List of trades
        """
        if bot_name:
            return [t for t in self.trade_logger.trades if t.bot_name == bot_name]
        return self.trade_logger.trades

    def get_capital_curve(self, bot_name: str) -> pd.DataFrame:
        """
        Get capital curve over time for a bot.

        Args:
            bot_name: Name of bot

        Returns:
            DataFrame with timestamp and capital columns
        """
        bot = next((b for b in self.bots if b.name == bot_name), None)
        if not bot:
            return pd.DataFrame()

        # Reconstruct capital curve from trades
        capital_data = []
        running_capital = bot.initial_capital

        capital_data.append({
            'timestamp': bot.trades[0].timestamp if bot.trades else datetime.now(),
            'capital': running_capital
        })

        for trade in bot.trades:
            running_capital += trade.profit_usd
            capital_data.append({
                'timestamp': trade.timestamp,
                'capital': running_capital
            })

        return pd.DataFrame(capital_data)
