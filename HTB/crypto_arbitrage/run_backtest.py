"""Run backtest and launch comparison dashboard."""
import sys
from pathlib import Path
from loguru import logger

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bot.ml_arbitrage_bot import MLArbitrageBot
from bot.benchmark_bot import BenchmarkBot
from bot.backtest_engine import BacktestEngine
from ml_predictor import SpreadPredictor, OpportunityScorer


def main():
    """Run backtest comparing ML bot vs benchmark bot."""
    logger.info("=" * 70)
    logger.info("🤖 CRYPTO ARBITRAGE BOT BACKTEST")
    logger.info("=" * 70)

    # Load trained ML models
    logger.info("Loading ML models...")
    spread_predictor = SpreadPredictor()
    opportunity_scorer = OpportunityScorer()

    predictor_loaded = spread_predictor.load("models/spread_predictor_live.pkl")
    scorer_loaded = opportunity_scorer.load("models/opportunity_scorer_live.pkl")

    if not predictor_loaded:
        logger.warning("⚠️  Spread predictor not loaded - ML bot may underperform")
    else:
        logger.success("✅ Spread predictor loaded")

    if not scorer_loaded:
        logger.warning("⚠️  Opportunity scorer not loaded - ML bot may underperform")
    else:
        logger.success("✅ Opportunity scorer loaded")

    # Create bots
    logger.info("\nInitializing bots...")

    # ML Bot - uses trained models
    # NOTE: Using very lenient thresholds for demonstration/testing
    # In production, you'd want positive profit thresholds
    ml_bot = MLArbitrageBot(
        spread_predictor=spread_predictor,
        opportunity_scorer=opportunity_scorer,
        initial_capital=10000.0,
        min_ml_confidence=0.4,  # 40% confidence threshold (lenient)
        min_spread_threshold=-1.0  # Allow negative spreads for testing
    )
    ml_bot.min_profit_threshold = -2.0  # Allow negative profit for testing
    logger.info("✅ ML Arbitrage Bot initialized")
    logger.info(f"   - ML Confidence Threshold: {ml_bot.min_ml_confidence}")
    logger.info(f"   - Min Spread: {ml_bot.min_spread_threshold}%")
    logger.info(f"   - Min Profit: {ml_bot.min_profit_threshold}%")

    # Benchmark Bot - simple threshold strategy
    # NOTE: Using very lenient thresholds for demonstration/testing
    benchmark_bot = BenchmarkBot(
        initial_capital=10000.0,
        min_spread_threshold=-0.5,  # Allow negative spreads for testing
        position_size_pct=0.05  # 5% per trade
    )
    benchmark_bot.min_profit_threshold = -2.0  # Allow negative profit for testing
    logger.info("✅ Benchmark Bot initialized")
    logger.info(f"   - Min Spread: {benchmark_bot.min_spread_threshold}%")
    logger.info(f"   - Min Profit: {benchmark_bot.min_profit_threshold}%")
    logger.info(f"   - Position Size: {benchmark_bot.position_size_pct * 100}%")

    # Create backtest engine
    logger.info("\nInitializing backtest engine...")
    engine = BacktestEngine(
        bots=[ml_bot, benchmark_bot],
        slippage_pct=0.1,  # 0.1% slippage
        execution_time_ms=100.0  # 100ms execution time
    )
    logger.info("✅ Backtest engine ready")

    # Load opportunities
    logger.info("\nLoading historical opportunities...")
    opportunities = engine.load_latest_opportunities()

    if not opportunities:
        logger.error("❌ No opportunities found! Please run data collection first.")
        logger.info("   Run: python main.py")
        logger.info("   Wait for data collection, then run this script again.")
        return

    logger.success(f"✅ Loaded {len(opportunities)} opportunities")

    # Run backtest
    logger.info("\n" + "=" * 70)
    logger.info("🚀 STARTING BACKTEST")
    logger.info("=" * 70)

    results = engine.run_backtest(opportunities=opportunities)

    if not results:
        logger.error("❌ Backtest failed - no results")
        return

    # Display comparison
    logger.info("\n" + "=" * 70)
    logger.info("📊 BOT COMPARISON")
    logger.info("=" * 70)

    comparison_df = engine.compare_bots()
    print("\n" + comparison_df.to_string(index=False))

    # Determine winner
    ml_return = results['ML_Arbitrage_Bot']['return_pct']
    benchmark_return = results['Benchmark_Bot']['return_pct']

    logger.info("\n" + "=" * 70)
    if ml_return > benchmark_return:
        improvement = ml_return - benchmark_return
        logger.success(
            f"🏆 ML BOT WINS! Outperformed benchmark by {improvement:.2f}% return"
        )
    elif benchmark_return > ml_return:
        difference = benchmark_return - ml_return
        logger.warning(
            f"📉 Benchmark bot performed better by {difference:.2f}% return"
        )
    else:
        logger.info("🤝 Both bots performed equally")

    logger.info("=" * 70)

    # Show trade logs location
    logger.info(f"\n📁 Trade logs saved to: {engine.trade_logger.csv_path}")
    logger.info(f"📁 Summary saved to: {engine.trade_logger.json_path}")

    # Launch dashboard
    logger.info("\n" + "=" * 70)
    logger.info("🌐 LAUNCHING BACKTEST DASHBOARD")
    logger.info("=" * 70)
    logger.info("Dashboard will be available at: http://localhost:8052")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70 + "\n")

    try:
        from backtest_dashboard import BacktestDashboard

        dashboard = BacktestDashboard(engine)
        dashboard.run(host='0.0.0.0', port=8052, debug=False)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Dashboard stopped by user")
    except Exception as e:
        logger.error(f"❌ Error launching dashboard: {e}")
        logger.info("You can still view results in the CSV/JSON files above")


if __name__ == "__main__":
    # Configure logger
    logger.add(
        "logs/backtest_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )

    try:
        main()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise
