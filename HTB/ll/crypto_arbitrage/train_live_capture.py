"""Capture 2 hours of LIVE data and train ML models - Optimized approach."""
import asyncio
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import pandas as pd
import joblib
from loguru import logger

from data_ingestion import MultiExchangeAggregator
from arbitrage_detector import ArbitrageDetector
from ml_predictor import SpreadPredictor, OpportunityScorer
from config import ArbitrageOpportunity


class LiveDataCapture:
    """Capture live data for training without heavy computation."""

    def __init__(self, capture_hours: int = 2):
        self.capture_hours = capture_hours
        self.detector = ArbitrageDetector()
        self.aggregator = MultiExchangeAggregator(self.detector.update_price)

        self.start_time = None
        self.end_time = None
        self.running = True

        # Lightweight data storage
        self.price_records = []  # Store raw prices
        self.opportunities = []  # Store opportunities

    async def capture_data(self):
        """Capture live data for specified hours."""
        self.start_time = datetime.now(timezone.utc)
        self.end_time = self.start_time + timedelta(hours=self.capture_hours)

        logger.info("="*70)
        logger.info(f"🚀 LIVE DATA CAPTURE - {self.capture_hours} HOURS")
        logger.info("="*70)
        logger.info(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"End:   {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Exchanges: Coinbase, Binance, Bitstamp")
        logger.info(f"Symbols: BTC-USD, ETH-USD, SOL-USD")
        logger.info("="*70)

        # Start data collection in background task
        aggregator_task = asyncio.create_task(self.aggregator.start())

        # Monitor progress
        last_update = datetime.now(timezone.utc)
        update_interval = 300  # Log every 5 minutes

        try:
            while self.running:
                now = datetime.now(timezone.utc)

                # Check if capture period is over
                if now >= self.end_time:
                    logger.success(f"\n✅ Capture complete! {self.capture_hours} hours elapsed")
                    break

                # Periodic status update
                if (now - last_update).total_seconds() >= update_interval:
                    elapsed = (now - self.start_time).total_seconds() / 3600
                    remaining = (self.end_time - now).total_seconds() / 3600

                    # Get current stats
                    price_count = len(self.detector.price_buffer.get('BTC-USD', [])) + \
                                  len(self.detector.price_buffer.get('ETH-USD', [])) + \
                                  len(self.detector.price_buffer.get('SOL-USD', []))
                    opp_count = len(self.detector.opportunities)

                    logger.info(f"\n📊 Progress Update:")
                    logger.info(f"  Elapsed: {elapsed:.1f}h / {self.capture_hours}h ({elapsed/self.capture_hours*100:.1f}%)")
                    logger.info(f"  Remaining: {remaining:.1f}h")
                    logger.info(f"  Price updates: {price_count:,}")
                    logger.info(f"  Opportunities: {opp_count:,}")
                    logger.info(f"  Avg opportunities/hour: {opp_count/elapsed:.1f}")

                    last_update = now

                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.warning("\n⚠️ Capture interrupted by user")

        # Cancel the aggregator task and stop it
        aggregator_task.cancel()
        try:
            await aggregator_task
        except asyncio.CancelledError:
            pass
        await self.aggregator.stop()

    def save_captured_data(self):
        """Save captured data to disk."""
        logger.info("\n" + "="*70)
        logger.info("💾 SAVING CAPTURED DATA")
        logger.info("="*70)

        # Create directory
        data_dir = Path("captured_data")
        data_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save price data
        all_prices = []
        for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            if symbol in self.detector.price_buffer:
                all_prices.extend(self.detector.price_buffer[symbol])

        if all_prices:
            df_prices = pd.DataFrame(all_prices)
            price_file = data_dir / f"prices_{timestamp}.csv"
            df_prices.to_csv(price_file, index=False)
            logger.success(f"✓ Saved {len(all_prices):,} price records to {price_file}")

        # Save opportunities
        if self.detector.opportunities:
            df_opps = pd.DataFrame([o.to_dict() for o in self.detector.opportunities])
            opp_file = data_dir / f"opportunities_{timestamp}.csv"
            df_opps.to_csv(opp_file, index=False)
            logger.success(f"✓ Saved {len(self.detector.opportunities):,} opportunities to {opp_file}")

        logger.info("="*70)

        return all_prices, self.detector.opportunities

    def train_models(self):
        """Train ML models on captured data."""
        logger.info("\n" + "="*70)
        logger.info("🤖 TRAINING ML MODELS")
        logger.info("="*70)

        # Get training data
        all_prices = []
        for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
            if symbol in self.detector.price_buffer:
                all_prices.extend(self.detector.price_buffer[symbol])

        if not all_prices:
            logger.error("❌ No data captured for training!")
            return False

        model_dir = Path("models")
        model_dir.mkdir(exist_ok=True)

        # Train Spread Predictor
        logger.info(f"\n1️⃣ Training Spread Predictor on {len(all_prices):,} records...")
        predictor = SpreadPredictor()

        df_prices = pd.DataFrame(all_prices)
        predictor.train(df_prices)

        if predictor.is_trained:
            predictor_file = model_dir / "spread_predictor_live.pkl"
            joblib.dump(predictor, predictor_file)
            logger.success(f"✓ Spread predictor saved to {predictor_file}")
        else:
            logger.warning("⚠️ Spread predictor training incomplete")

        # Train Opportunity Scorer
        if self.detector.opportunities:
            logger.info(f"\n2️⃣ Training Opportunity Scorer on {len(self.detector.opportunities):,} opportunities...")
            scorer = OpportunityScorer()

            # Create labels: True if profit > threshold
            labels = [opp.profit_after_fees > 0.5 for opp in self.detector.opportunities]

            scorer.train(self.detector.opportunities, labels)

            if scorer.is_trained:
                scorer_file = model_dir / "opportunity_scorer_live.pkl"
                joblib.dump(scorer, scorer_file)
                logger.success(f"✓ Opportunity scorer saved to {scorer_file}")
            else:
                logger.warning("⚠️ Opportunity scorer training incomplete")
        else:
            logger.warning("⚠️ No opportunities captured, skipping scorer training")

        logger.info("="*70)
        return True

    def show_summary(self):
        """Show capture and training summary."""
        logger.info("\n" + "="*70)
        logger.info("📈 CAPTURE SUMMARY")
        logger.info("="*70)

        # Calculate total prices
        total_prices = sum(len(self.detector.price_buffer.get(symbol, []))
                          for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD'])

        # Calculate duration
        if self.start_time and self.end_time:
            duration = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
        else:
            duration = 0

        logger.info(f"Duration: {duration:.2f} hours")
        logger.info(f"Price updates: {total_prices:,}")
        logger.info(f"Opportunities detected: {len(self.detector.opportunities):,}")

        if self.detector.opportunities:
            profits = [o.profit_after_fees for o in self.detector.opportunities]
            logger.info(f"\nOpportunity Statistics:")
            logger.info(f"  Average profit: {sum(profits)/len(profits):.3f}%")
            logger.info(f"  Max profit: {max(profits):.3f}%")
            logger.info(f"  Min profit: {min(profits):.3f}%")
            logger.info(f"  Opportunities/hour: {len(self.detector.opportunities)/duration:.1f}")

        # Show stats by exchange pair
        stats = self.detector.get_statistics()
        if stats.get('top_pairs'):
            logger.info(f"\nTop Exchange Pairs:")
            for pair_info in stats['top_pairs'][:5]:
                logger.info(f"  {pair_info['pair']}: {pair_info['count']} opportunities")

        logger.info("="*70)


def run_capture(hours: int = 2):
    """Run the live data capture and training."""

    # Setup signal handler for graceful shutdown
    capture = None

    def signal_handler(sig, frame):
        logger.warning("\n\n⚠️ Received interrupt signal, stopping capture...")
        if capture:
            capture.running = False

    signal.signal(signal.SIGINT, signal_handler)

    # Create capture instance
    capture = LiveDataCapture(capture_hours=hours)

    # Run capture
    logger.info(f"\n🎯 Starting {hours}-hour live data capture...")
    logger.info("Press Ctrl+C to stop early\n")

    try:
        asyncio.run(capture.capture_data())
    except Exception as e:
        logger.error(f"Error during capture: {e}")
        return False

    # Save data
    capture.save_captured_data()

    # Show summary
    capture.show_summary()

    # Train models
    success = capture.train_models()

    if success:
        logger.info("\n" + "="*70)
        logger.success("🎉 TRAINING COMPLETE!")
        logger.info("="*70)
        logger.info("Models trained on live data and saved to models/")
        logger.info("\nYou can now use these models in your main application:")
        logger.info("  python main.py")
        logger.info("="*70)
        
        # Generate performance report
        logger.info("Generating performance metrics report...")
        subprocess.run([sys.executable, 'generate_report.py'], check=True)
        logger.success("Performance report generated in models/model_performance_metrics.csv")


    return success


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Capture live data and train ML models (optimized approach)"
    )
    parser.add_argument(
        '--hours',
        type=float,
        default=2.0,
        help='Hours to capture data (default: 2.0, min: 0.5, max: 24)'
    )

    args = parser.parse_args()

    # Validate hours
    if args.hours < 0.5:
        logger.error("Minimum capture time is 0.5 hours (30 minutes)")
        sys.exit(1)
    if args.hours > 24:
        logger.error("Maximum capture time is 24 hours")
        sys.exit(1)

    logger.info("="*70)
    logger.info("🚀 LIVE DATA CAPTURE & TRAINING")
    logger.info("="*70)
    logger.info(f"Capture duration: {args.hours} hours")
    logger.info(f"Expected data points: ~{int(args.hours * 60 * 9):,} price updates")
    logger.info(f"Expected opportunities: ~{int(args.hours * 20):,} (estimate)")
    logger.info("="*70)

    success = run_capture(hours=args.hours)

    if success:
        logger.success("\n✅ SUCCESS! Models ready to use")
        sys.exit(0)
    else:
        logger.error("\n❌ FAILED! Check logs for errors")
        sys.exit(1)
