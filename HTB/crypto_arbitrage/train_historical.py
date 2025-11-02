"""Train ML models on 30 days of historical data from all exchanges."""
import sys
from pathlib import Path
from loguru import logger

from historical_data import fetch_and_prepare_training_data
from ml_predictor import SpreadPredictor, OpportunityClassifier


def train_models_on_historical_data(days: int = 30, force_refetch: bool = False):
    """
    Fetch 30 days of historical data and train ML models.

    Args:
        days: Number of days of historical data (default 30)
        force_refetch: If True, refetch data even if cached (default False)

    Data Volume Calculation:
    - 30 days = 43,200 minutes of data
    - 3 exchanges × 3 symbols = 9 data streams
    - Total: ~388,800 data points (43,200 × 9)
    - With 1-minute OHLCV candles, this gives us rich training data

    Expected file sizes:
    - Each symbol per exchange: ~1-2 MB CSV
    - Total: ~27 MB for all data
    """
    logger.info("="*70)
    logger.info("TRAINING ML MODELS ON 30-DAY HISTORICAL DATA")
    logger.info("="*70)

    # Step 1: Fetch/load historical data
    logger.info(f"\nStep 1: Fetching {days} days of historical data...")
    logger.info(f"Expected data volume: ~{days * 1440 * 9:,} records")
    logger.info(f"Symbols: BTC-USD, ETH-USD, SOL-USD")
    logger.info(f"Exchanges: Coinbase, Binance, Bitstamp")

    if force_refetch:
        # Clear cache
        import shutil
        cache_dir = Path("historical_data")
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            logger.info("Cleared historical data cache")

    training_data = fetch_and_prepare_training_data(days=days)

    if training_data.empty:
        logger.error("Failed to fetch historical data!")
        return False

    # Step 2: Display data summary
    logger.info("\n" + "="*70)
    logger.info("DATA SUMMARY")
    logger.info("="*70)
    logger.info(f"Total records: {len(training_data):,}")
    logger.info(f"Date range: {training_data['timestamp'].min()} to {training_data['timestamp'].max()}")
    logger.info(f"Duration: {(training_data['timestamp'].max() - training_data['timestamp'].min()).days} days")
    logger.info(f"\nColumns: {list(training_data.columns)}")

    # Show spread statistics
    spread_cols = [col for col in training_data.columns if col.startswith('spread_')]
    if spread_cols:
        logger.info(f"\nSpread columns: {spread_cols}")
        logger.info("\nSpread Statistics (%):")
        stats = training_data[spread_cols].describe()
        logger.info(f"\n{stats}")

        # Show profitable opportunities
        for col in spread_cols:
            profitable = (training_data[col].abs() > 0.5).sum()
            pct_profitable = (profitable / len(training_data)) * 100
            logger.info(f"  {col}: {profitable:,} profitable records ({pct_profitable:.2f}%)")

    # Step 3: Train Spread Predictor
    logger.info("\n" + "="*70)
    logger.info("TRAINING SPREAD PREDICTOR")
    logger.info("="*70)

    predictor = SpreadPredictor()

    # Convert spread data to format expected by predictor
    # The predictor expects data in exchange-price format
    training_records = []
    for _, row in training_data.iterrows():
        for exchange in ['Coinbase', 'Binance', 'Bitstamp']:
            price_col = f'{exchange}_price'
            volume_col = f'{exchange}_volume'

            if price_col in training_data.columns and volume_col in training_data.columns:
                if not pd.isna(row[price_col]):
                    training_records.append({
                        'timestamp': row['timestamp'],
                        'exchange': exchange,
                        'price': row[price_col],
                        'volume': row[volume_col],
                        'bid': row[price_col] * 0.999,  # Approximate
                        'ask': row[price_col] * 1.001   # Approximate
                    })

    import pandas as pd
    predictor_df = pd.DataFrame(training_records)

    if not predictor_df.empty:
        logger.info(f"Training spread predictor on {len(predictor_df):,} records...")
        predictor.train(predictor_df)

        if predictor.is_trained:
            # Save model
            import joblib
            model_path = Path("models")
            model_path.mkdir(exist_ok=True)

            predictor_file = model_path / "spread_predictor.pkl"
            joblib.dump(predictor, predictor_file)
            logger.success(f"Spread predictor saved to {predictor_file}")

            # Test prediction
            if len(predictor_df) > 100:
                test_sample = predictor_df.tail(50)
                predictions = predictor.predict(test_sample)
                logger.info(f"\nSample predictions on recent data:")
                logger.info(f"  Mean predicted spread: {predictions.mean():.4f}%")
                logger.info(f"  Prediction range: [{predictions.min():.4f}%, {predictions.max():.4f}%]")

    # Step 4: Train Opportunity Classifier
    logger.info("\n" + "="*70)
    logger.info("TRAINING OPPORTUNITY CLASSIFIER")
    logger.info("="*70)

    classifier = OpportunityClassifier()

    # Create synthetic opportunities from spread data
    opportunities = []
    for _, row in training_data.iterrows():
        for col in spread_cols:
            spread_pct = row[col]
            if pd.notna(spread_pct):
                # Extract exchanges from column name (e.g., "spread_Coinbase_Binance")
                parts = col.replace("spread_", "").split("_")
                if len(parts) >= 2:
                    # Simulate fees (Coinbase 0.6%, Binance 0.1%, Bitstamp 0.5%)
                    fees = {'Coinbase': 0.6, 'Binance': 0.1, 'Bitstamp': 0.5}
                    total_fee = fees.get(parts[0], 0.5) + fees.get(parts[1], 0.5)
                    profit_after_fees = abs(spread_pct) - total_fee

                    opportunities.append({
                        'buy_exchange': parts[0] if spread_pct > 0 else parts[1],
                        'sell_exchange': parts[1] if spread_pct > 0 else parts[0],
                        'symbol': row.get('symbol', 'BTC-USD'),
                        'spread_pct': abs(spread_pct),
                        'profit_after_fees': profit_after_fees,
                        'is_profitable': profit_after_fees > 0.5
                    })

    if opportunities:
        from config import ArbitrageOpportunity
        import datetime

        opp_objects = [
            ArbitrageOpportunity(
                buy_exchange=o['buy_exchange'],
                sell_exchange=o['sell_exchange'],
                symbol=o['symbol'],
                buy_price=100.0,  # Dummy value
                sell_price=100.0 + o['spread_pct'],
                spread_pct=o['spread_pct'],
                profit_after_fees=o['profit_after_fees'],
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            for o in opportunities[:10000]  # Limit to 10k for training
        ]

        logger.info(f"Training opportunity classifier on {len(opp_objects):,} opportunities...")
        classifier.train(opp_objects)

        if classifier.is_trained:
            # Save model
            classifier_file = model_path / "opportunity_classifier.pkl"
            joblib.dump(classifier, classifier_file)
            logger.success(f"Opportunity classifier saved to {classifier_file}")

            # Show training results
            profitable = sum(1 for o in opportunities if o['is_profitable'])
            logger.info(f"\nTraining data statistics:")
            logger.info(f"  Total opportunities: {len(opportunities):,}")
            logger.info(f"  Profitable (>0.5% after fees): {profitable:,} ({profitable/len(opportunities)*100:.1f}%)")

    # Step 5: Summary
    logger.info("\n" + "="*70)
    logger.info("TRAINING COMPLETE!")
    logger.info("="*70)
    logger.info(f"✓ Fetched {len(training_data):,} historical records")
    logger.info(f"✓ Trained spread predictor: {'Yes' if predictor.is_trained else 'No'}")
    logger.info(f"✓ Trained opportunity classifier: {'Yes' if classifier.is_trained else 'No'}")
    logger.info(f"✓ Models saved to: models/")
    logger.info("\nYou can now run the main system with pre-trained models:")
    logger.info("  python main.py")
    logger.info("\nThe dashboard will load these models automatically!")
    logger.info("="*70)

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train ML models on historical crypto data")
    parser.add_argument('--days', type=int, default=30, help='Number of days of historical data (default: 30)')
    parser.add_argument('--force', action='store_true', help='Force refetch data even if cached')

    args = parser.parse_args()

    logger.info(f"Starting historical data training...")
    logger.info(f"Days: {args.days}")
    logger.info(f"Force refetch: {args.force}")

    success = train_models_on_historical_data(days=args.days, force_refetch=args.force)

    if success:
        logger.success("\n🎉 SUCCESS! Models trained and ready to use!")
        sys.exit(0)
    else:
        logger.error("\n❌ FAILED! Check logs for errors")
        sys.exit(1)
