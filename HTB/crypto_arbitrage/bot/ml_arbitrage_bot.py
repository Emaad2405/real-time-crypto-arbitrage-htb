"""ML-powered arbitrage bot using trained models."""
from typing import Optional
from loguru import logger

from .base_bot import BaseBot
from config import ArbitrageOpportunity
from ml_predictor import SpreadPredictor, OpportunityScorer


class MLArbitrageBot(BaseBot):
    """
    Arbitrage bot that uses machine learning models for decision making.

    Uses:
    - SpreadPredictor: Predicts future spread movements
    - OpportunityScorer: Scores opportunities based on success probability
    """

    def __init__(
        self,
        spread_predictor: SpreadPredictor,
        opportunity_scorer: OpportunityScorer,
        initial_capital: float = 10000.0,
        min_ml_confidence: float = 0.6,
        min_spread_threshold: float = 0.5
    ):
        """
        Initialize ML arbitrage bot.

        Args:
            spread_predictor: Trained spread prediction model
            opportunity_scorer: Trained opportunity scoring model
            initial_capital: Starting capital in USD
            min_ml_confidence: Minimum ML confidence score (0-1)
            min_spread_threshold: Minimum spread percentage
        """
        super().__init__(name="ML_Arbitrage_Bot", initial_capital=initial_capital)

        self.spread_predictor = spread_predictor
        self.opportunity_scorer = opportunity_scorer

        # ML-specific parameters
        self.min_ml_confidence = min_ml_confidence
        self.min_spread_threshold = min_spread_threshold

        # Track ML predictions
        self.predictions_made = 0
        self.high_confidence_trades = 0

    def should_execute_trade(self, opportunity: ArbitrageOpportunity) -> bool:
        """
        Use ML models to decide whether to execute trade.

        Decision factors:
        1. Opportunity scorer confidence > threshold
        2. Predicted profit after fees > minimum threshold
        3. Spread meets minimum threshold
        4. Models are trained and ready

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            True if should execute, False otherwise
        """
        # Check basic profit threshold
        if opportunity.profit_after_fees < self.min_profit_threshold:
            return False

        # Check spread threshold
        if opportunity.spread_pct < self.min_spread_threshold:
            return False

        # Use opportunity scorer if trained
        ml_confidence = 0.5  # Default neutral confidence
        if self.opportunity_scorer.is_trained:
            try:
                ml_confidence = self.opportunity_scorer.score(opportunity)
                self.predictions_made += 1
            except Exception as e:
                logger.warning(f"Error scoring opportunity: {e}")
                # Fall back to basic threshold check
                return opportunity.profit_after_fees >= self.min_profit_threshold

        # Decision based on ML confidence
        should_trade = ml_confidence >= self.min_ml_confidence

        if should_trade:
            self.high_confidence_trades += 1

        return should_trade

    def calculate_position_size(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Calculate position size using ML confidence and Kelly criterion.

        Higher ML confidence → larger position size (within limits)

        Args:
            opportunity: Arbitrage opportunity

        Returns:
            Position size in USD
        """
        # Get ML confidence score
        ml_confidence = 0.5
        if self.opportunity_scorer.is_trained:
            try:
                ml_confidence = self.opportunity_scorer.score(opportunity)
            except Exception as e:
                logger.warning(f"Error calculating position size: {e}")

        # Base position size (conservative)
        base_size = self.current_capital * 0.05  # 5% of capital

        # Scale by ML confidence (0.5 to 1.0 → 0% to 100% of base)
        confidence_multiplier = (ml_confidence - 0.5) * 2  # Maps 0.5-1.0 to 0-1
        confidence_multiplier = max(0, min(confidence_multiplier, 1))  # Clamp

        position_size = base_size * (1 + confidence_multiplier)

        # Apply maximum position limit
        max_position = self.current_capital * self.max_position_size
        position_size = min(position_size, max_position)

        # Ensure we don't exceed current capital
        position_size = min(position_size, self.current_capital * 0.95)

        return position_size

    def get_performance_metrics(self) -> dict:
        """Get performance metrics including ML-specific stats."""
        metrics = super().get_performance_metrics()

        # Add ML-specific metrics
        metrics.update({
            'predictions_made': self.predictions_made,
            'high_confidence_trades': self.high_confidence_trades,
            'ml_confidence_rate': (
                (self.high_confidence_trades / self.predictions_made * 100)
                if self.predictions_made > 0 else 0.0
            ),
            'spread_predictor_trained': self.spread_predictor.is_trained,
            'opportunity_scorer_trained': self.opportunity_scorer.is_trained,
            'min_ml_confidence': self.min_ml_confidence,
            'min_spread_threshold': self.min_spread_threshold,
        })

        return metrics

    def reset(self):
        """Reset bot to initial state."""
        super().reset()
        self.predictions_made = 0
        self.high_confidence_trades = 0
