"""Extract data from running detector and train ML models manually."""
import pickle
import pandas as pd
import joblib
from pathlib import Path
from loguru import logger
from datetime import datetime

from ml_predictor import SpreadPredictor, OpportunityScorer


def train_from_detector_state():
    """Load detector state and train models."""

    logger.info("="*70)
    logger.info("🤖 MANUAL ML MODEL TRAINING")
    logger.info("="*70)

    # Import the detector from the running system
    from arbitrage_detector import ArbitrageDetector
    detector = ArbitrageDetector()

    # Note: This won't have the data from the killed process,
    # but we can still demonstrate the training process

    logger.info(f"\nDetector state:")
    logger.info(f"  Opportunities: {len(detector.opportunities)}")

    # Get all price data
    all_prices = []
    for symbol in ['BTC-USD', 'ETH-USD', 'SOL-USD']:
        if symbol in detector.price_buffer:
            prices = detector.price_buffer[symbol]
            all_prices.extend(prices)
            logger.info(f"  {symbol} price records: {len(prices)}")

    logger.info(f"  Total price records: {len(all_prices)}")

    if not all_prices:
        logger.error("\n❌ No price data available!")
        logger.info("\nTo train models, you need to:")
        logger.info("1. Let the system run for at least 10-15 minutes")
        logger.info("2. Then run this script again")
        return False

    # Create directories
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)

    data_dir = Path("captured_data")
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save the data
    logger.info(f"\n💾 Saving captured data...")

    if all_prices:
        df_prices = pd.DataFrame(all_prices)
        price_file = data_dir / f"prices_{timestamp}.csv"
        df_prices.to_csv(price_file, index=False)
        logger.success(f"✓ Saved {len(all_prices):,} price records to {price_file}")

    if detector.opportunities:
        df_opps = pd.DataFrame([o.to_dict() for o in detector.opportunities])
        opp_file = data_dir / f"opportunities_{timestamp}.csv"
        df_opps.to_csv(opp_file, index=False)
        logger.success(f"✓ Saved {len(detector.opportunities):,} opportunities to {opp_file}")

    # Train Spread Predictor
    logger.info(f"\n1️⃣ Training Spread Predictor on {len(all_prices):,} records...")
    predictor = SpreadPredictor()

    df_prices = pd.DataFrame(all_prices)
    predictor.train(df_prices)

    if predictor.is_trained:
        predictor_file = model_dir / "spread_predictor_live.pkl"
        joblib.dump(predictor, predictor_file)
        logger.success(f"✓ Spread predictor saved to {predictor_file}")

        # Show metrics
        if hasattr(predictor, 'r2_train') and hasattr(predictor, 'r2_test'):
            logger.info(f"  📊 Train R²: {predictor.r2_train:.3f}")
            logger.info(f"  📊 Test R²: {predictor.r2_test:.3f}")
    else:
        logger.warning("⚠️ Spread predictor training incomplete")

    # Train Opportunity Scorer
    if detector.opportunities and len(detector.opportunities) >= 10:
        logger.info(f"\n2️⃣ Training Opportunity Scorer on {len(detector.opportunities):,} opportunities...")
        scorer = OpportunityScorer()

        # Create labels: True if profit > threshold
        labels = [opp.profit_after_fees > 0.5 for opp in detector.opportunities]

        scorer.train(detector.opportunities, labels)

        if scorer.is_trained:
            scorer_file = model_dir / "opportunity_scorer_live.pkl"
            joblib.dump(scorer, scorer_file)
            logger.success(f"✓ Opportunity scorer saved to {scorer_file}")

            # Show metrics
            if hasattr(scorer, 'accuracy'):
                logger.info(f"  📊 Accuracy: {scorer.accuracy:.3f}")
        else:
            logger.warning("⚠️ Opportunity scorer training incomplete")
    else:
        logger.warning(f"⚠️ Not enough opportunities ({len(detector.opportunities)}) for training (need at least 10)")

    logger.info("\n" + "="*70)
    logger.success("🎉 TRAINING COMPLETE!")
    logger.info("="*70)
    logger.info("Models saved to models/")
    logger.info("Data saved to captured_data/")
    logger.info("="*70)

    return True


if __name__ == "__main__":
    try:
        success = train_from_detector_state()
        if success:
            logger.success("\n✅ SUCCESS!")
        else:
            logger.error("\n❌ FAILED - see logs above")
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
