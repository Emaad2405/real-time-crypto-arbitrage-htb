"""Generate a CSV report of model performance metrics."""
import pandas as pd
import joblib
import os
from pathlib import Path
from loguru import logger


def generate_performance_report():
    """Load trained models and generate a performance CSV."""
    model_dir = Path('models')
    predictor_path = model_dir / 'spread_predictor_live.pkl'
    scorer_path = model_dir / 'opportunity_scorer_live.pkl'
    output_csv_path = model_dir / 'model_performance_metrics.csv'

    if not predictor_path.exists() or not scorer_path.exists():
        logger.error("One or more model .pkl files not found. Cannot generate report.")
        return

    # Load models
    predictor = joblib.load(predictor_path)
    scorer = joblib.load(scorer_path)

    # Get file sizes
    predictor_size = predictor_path.stat().st_size / 1024
    scorer_size = scorer_path.stat().st_size / 1024

    # Create metrics DataFrame
    metrics_data = [
        {
            'Model': 'Spread Predictor',
            'Status': 'TRAINED SUCCESSFULLY',
            'Method': 'Gradient Boosting Regressor',
            'Train_R2': f'{getattr(predictor, "r2_train", 0.0):.3f}',
            'Test_R2': f'{getattr(predictor, "r2_test", 0.0):.3f}',
            'Accuracy': 'N/A',
            'Model_File': str(predictor_path),
            'Model_Size_KB': int(predictor_size),
        },
        {
            'Model': 'Opportunity Classifier',
            'Status': 'TRAINED SUCCESSFULLY',
            'Method': 'Random Forest Classifier',
            'Train_R2': 'N/A',
            'Test_R2': 'N/A',
            'Accuracy': f'{getattr(scorer, "accuracy", 0.0):.3f}',
            'Model_File': str(scorer_path),
            'Model_Size_KB': int(scorer_size),
        }
    ]

    df = pd.DataFrame(metrics_data)

    # Save to CSV
    try:
        df.to_csv(output_csv_path, index=False)
        logger.success(f"Performance metrics successfully saved to {output_csv_path}")
    except Exception as e:
        logger.error(f"Failed to save performance report: {e}")
        return

    # --- Display Results ---
    logger.info("="*120)
    logger.info("ML MODEL PERFORMANCE METRICS")
    logger.info("="*120)
    # Use to_string() to ensure the table is printed to the log correctly
    for line in df.to_string(index=False).split('\n'):
        logger.info(line)
    logger.info("="*120)
    logger.info(f"Spread Predictor: R2_train={getattr(predictor, 'r2_train', 0.0):.3f} | R2_test={getattr(predictor, 'r2_test', 0.0):.3f}")
    logger.info(f"Opportunity Classifier: Accuracy={getattr(scorer, 'accuracy', 0.0):.3f}")
    logger.info("="*120)


if __name__ == "__main__":
    logger.add("logs/reporting_{time}.log", rotation="1 day", level="INFO")
    logger.info("Generating model performance report...")
    generate_performance_report()
    logger.info("Report generation complete.")