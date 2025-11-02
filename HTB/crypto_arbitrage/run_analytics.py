"""Launch Analytics Dashboard on Port 8051"""
import asyncio
from loguru import logger

from data_ingestion import MultiExchangeAggregator
from arbitrage_detector import ArbitrageDetector
from analytics_dashboard import AnalyticsDashboard


async def run_system():
    """Run data collection and analytics dashboard together."""
    logger.info("="*70)
    logger.info("🔬 ANALYTICS DASHBOARD + DATA COLLECTION")
    logger.info("="*70)
    logger.info("Main Dashboard: http://localhost:8050")
    logger.info("Analytics Dashboard: http://localhost:8051")
    logger.info("="*70)

    # Create components
    detector = ArbitrageDetector()
    aggregator = MultiExchangeAggregator(detector.update_price)
    analytics = AnalyticsDashboard(detector)

    # Start data collection in background
    asyncio.create_task(aggregator.start())

    # Start analytics dashboard (blocking)
    logger.info("Starting analytics dashboard on http://0.0.0.0:8051")
    analytics.run(host='0.0.0.0', port=8051, debug=False)


if __name__ == "__main__":
    try:
        asyncio.run(run_system())
    except KeyboardInterrupt:
        logger.info("\nShutting down analytics dashboard...")
