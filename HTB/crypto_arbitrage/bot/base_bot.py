"""Abstract base class for arbitrage trading bots."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass
from loguru import logger

from config import ArbitrageOpportunity


@dataclass
class Trade:
    """Represents a completed trade."""
    timestamp: datetime
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    amount: float
    spread_pct: float
    predicted_profit_pct: float
    actual_profit_pct: float
    profit_usd: float
    fees_usd: float
    slippage_usd: float
    success: bool
    execution_time_ms: float
    bot_name: str

    def to_dict(self) -> Dict:
        """Convert trade to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'amount': self.amount,
            'spread_pct': self.spread_pct,
            'predicted_profit_pct': self.predicted_profit_pct,
            'actual_profit_pct': self.actual_profit_pct,
            'profit_usd': self.profit_usd,
            'fees_usd': self.fees_usd,
            'slippage_usd': self.slippage_usd,
            'success': self.success,
            'execution_time_ms': self.execution_time_ms,
            'bot_name': self.bot_name,
        }


class BaseBot(ABC):
    """Abstract base class for all arbitrage bots."""

    def __init__(self, name: str, initial_capital: float = 10000.0):
        """
        Initialize bot.

        Args:
            name: Bot name
            initial_capital: Starting capital in USD
        """
        self.name = name
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades: List[Trade] = []
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0

        # Performance metrics
        self.total_profit = 0.0
        self.total_fees = 0.0
        self.total_slippage = 0.0

        # Risk management
        self.max_position_size = 0.1  # Max 10% of capital per trade
        self.min_profit_threshold = 0.5  # Min 0.5% profit after fees

    @abstractmethod
    def should_execute_trade(self, opportunity: ArbitrageOpportunity) -> bool:
        """
        Decide whether to execute a trade based on the opportunity.

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            True if should execute, False otherwise
        """
        pass

    @abstractmethod
    def calculate_position_size(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Calculate position size for the trade.

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            Amount in USD to trade
        """
        pass

    def execute_trade(
        self,
        opportunity: ArbitrageOpportunity,
        slippage_pct: float = 0.1,
        execution_time_ms: float = 100.0
    ) -> Optional[Trade]:
        """
        Execute a trade with realistic simulation.

        Args:
            opportunity: Arbitrage opportunity
            slippage_pct: Price slippage percentage
            execution_time_ms: Simulated execution time

        Returns:
            Trade object if executed, None otherwise
        """
        # Check if we should execute
        if not self.should_execute_trade(opportunity):
            return None

        # Calculate position size
        position_size_usd = self.calculate_position_size(opportunity)

        if position_size_usd <= 0 or position_size_usd > self.current_capital:
            logger.warning(f"{self.name}: Insufficient capital for trade")
            return None

        # Simulate slippage
        slippage_factor = slippage_pct / 100.0
        actual_buy_price = opportunity.buy_price * (1 + slippage_factor)
        actual_sell_price = opportunity.sell_price * (1 - slippage_factor)

        # Calculate amounts
        amount_crypto = position_size_usd / actual_buy_price

        # Calculate costs
        buy_cost = amount_crypto * actual_buy_price
        sell_revenue = amount_crypto * actual_sell_price

        # Fees (0.1% per side = 0.2% total)
        fees = (buy_cost + sell_revenue) * 0.001

        # Slippage cost
        ideal_buy = amount_crypto * opportunity.buy_price
        ideal_sell = amount_crypto * opportunity.sell_price
        slippage_cost = (ideal_sell - ideal_buy) - (sell_revenue - buy_cost)

        # Net profit
        gross_profit = sell_revenue - buy_cost
        net_profit = gross_profit - fees

        # Actual profit percentage
        actual_profit_pct = (net_profit / buy_cost) * 100

        # Success criteria
        success = actual_profit_pct >= self.min_profit_threshold

        # Create trade record
        trade = Trade(
            timestamp=opportunity.timestamp,
            symbol=opportunity.symbol,
            buy_exchange=opportunity.buy_exchange,
            sell_exchange=opportunity.sell_exchange,
            buy_price=actual_buy_price,
            sell_price=actual_sell_price,
            amount=amount_crypto,
            spread_pct=opportunity.spread_pct,
            predicted_profit_pct=opportunity.profit_after_fees,
            actual_profit_pct=actual_profit_pct,
            profit_usd=net_profit,
            fees_usd=fees,
            slippage_usd=slippage_cost,
            success=success,
            execution_time_ms=execution_time_ms,
            bot_name=self.name
        )

        # Update bot state
        if success:
            self.current_capital += net_profit
            self.successful_trades += 1
        else:
            self.current_capital -= abs(net_profit)
            self.failed_trades += 1

        self.total_trades += 1
        self.total_profit += net_profit
        self.total_fees += fees
        self.total_slippage += slippage_cost
        self.trades.append(trade)

        return trade

    def get_performance_metrics(self) -> Dict:
        """Calculate and return performance metrics."""
        if not self.trades:
            return {
                'bot_name': self.name,
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'total_fees': 0.0,
                'total_slippage': 0.0,
                'net_profit': 0.0,
                'return_pct': 0.0,
                'avg_profit_per_trade': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': 0.0,
                'final_capital': self.initial_capital,
            }

        # Basic metrics
        win_rate = (self.successful_trades / self.total_trades) * 100
        net_profit = self.current_capital - self.initial_capital
        return_pct = (net_profit / self.initial_capital) * 100
        avg_profit_per_trade = net_profit / self.total_trades

        # Calculate drawdown
        capital_curve = [self.initial_capital]
        running_capital = self.initial_capital
        for trade in self.trades:
            running_capital += trade.profit_usd
            capital_curve.append(running_capital)

        peak = capital_curve[0]
        max_drawdown = 0.0
        for capital in capital_curve:
            if capital > peak:
                peak = capital
            drawdown = ((peak - capital) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate Sharpe ratio (simplified)
        returns = [trade.actual_profit_pct for trade in self.trades]
        if len(returns) > 1:
            import numpy as np
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (mean_return / std_return) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Profit factor
        winning_trades = [t.profit_usd for t in self.trades if t.success]
        losing_trades = [abs(t.profit_usd) for t in self.trades if not t.success]
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = sum(losing_trades) if losing_trades else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0.0

        return {
            'bot_name': self.name,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'total_fees': self.total_fees,
            'total_slippage': self.total_slippage,
            'net_profit': net_profit,
            'return_pct': return_pct,
            'avg_profit_per_trade': avg_profit_per_trade,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'final_capital': self.current_capital,
        }

    def reset(self):
        """Reset bot to initial state."""
        self.current_capital = self.initial_capital
        self.trades = []
        self.total_trades = 0
        self.successful_trades = 0
        self.failed_trades = 0
        self.total_profit = 0.0
        self.total_fees = 0.0
        self.total_slippage = 0.0
