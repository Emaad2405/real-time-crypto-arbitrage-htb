"""Benchmark bot using simple threshold-based strategy."""
from loguru import logger

from .base_bot import BaseBot
from config import ArbitrageOpportunity


class BenchmarkBot(BaseBot):
    """
    Simple benchmark bot using naive threshold strategy.

    This bot serves as a baseline for comparing ML bot performance.
    It uses simple rules without any ML models:
    - Execute if spread > threshold
    - Execute if profit after fees > minimum
    - Fixed position sizing
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        min_spread_threshold: float = 1.0,
        position_size_pct: float = 0.05
    ):
        """
        Initialize benchmark bot.

        Args:
            initial_capital: Starting capital in USD
            min_spread_threshold: Minimum spread percentage to execute
            position_size_pct: Fixed percentage of capital per trade
        """
        super().__init__(name="Benchmark_Bot", initial_capital=initial_capital)

        self.min_spread_threshold = min_spread_threshold
        self.position_size_pct = position_size_pct

        # Override base class thresholds for benchmark
        self.min_profit_threshold = 0.3  # Lower threshold - more aggressive

    def should_execute_trade(self, opportunity: ArbitrageOpportunity) -> bool:
        """
        Simple threshold-based decision.

        Execute if:
        1. Spread > minimum threshold
        2. Profit after fees > minimum threshold

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            True if should execute, False otherwise
        """
        # Check spread threshold
        if opportunity.spread_pct < self.min_spread_threshold:
            return False

        # Check profit threshold
        if opportunity.profit_after_fees < self.min_profit_threshold:
            return False

        return True

    def calculate_position_size(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Fixed percentage position sizing.

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            Position size in USD
        """
        # Simple fixed percentage of capital
        position_size = self.current_capital * self.position_size_pct

        # Apply maximum position limit
        max_position = self.current_capital * self.max_position_size
        position_size = min(position_size, max_position)

        # Ensure we don't exceed current capital
        position_size = min(position_size, self.current_capital * 0.95)

        return position_size

    def get_performance_metrics(self) -> dict:
        """Get performance metrics including benchmark-specific parameters."""
        metrics = super().get_performance_metrics()

        # Add benchmark-specific parameters
        metrics.update({
            'min_spread_threshold': self.min_spread_threshold,
            'position_size_pct': self.position_size_pct,
            'strategy': 'threshold_based',
        })

        return metrics
