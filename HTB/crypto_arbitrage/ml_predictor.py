"""Machine learning models for spread prediction and opportunity scoring."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from loguru import logger

from config import ArbitrageOpportunity


class SpreadPredictor:
    """Predicts future spreads using historical data."""

    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
        self.r2_train = 0.0
        self.r2_test = 0.0

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features from raw price data."""
        if df.empty:
            return pd.DataFrame()

        # Ensure timestamp is datetime
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Create features by exchange
        features_list = []

        for exchange in df['exchange'].unique():
            ex_df = df[df['exchange'] == exchange].copy()

            if len(ex_df) < 10:
                continue

            # Price-based features
            ex_df['price_change'] = ex_df['price'].pct_change()
            ex_df['price_ma_5'] = ex_df['price'].rolling(window=5).mean()
            ex_df['price_ma_20'] = ex_df['price'].rolling(window=20).mean()
            ex_df['price_std_5'] = ex_df['price'].rolling(window=5).std()

            # Volatility
            ex_df['volatility'] = ex_df['price_change'].rolling(window=10).std()

            # Bid-ask spread (if available)
            if 'bid' in ex_df.columns and 'ask' in ex_df.columns:
                ex_df['bid_ask_spread'] = (ex_df['ask'] - ex_df['bid']) / ex_df['bid']
            else:
                ex_df['bid_ask_spread'] = 0

            # Volume features
            if 'volume' in ex_df.columns:
                ex_df['volume_ma'] = ex_df['volume'].rolling(window=5).mean()
            else:
                ex_df['volume_ma'] = 0

            # Time features
            ex_df['hour'] = ex_df['timestamp'].dt.hour
            ex_df['minute'] = ex_df['timestamp'].dt.minute

            # Prefix with exchange name
            feature_cols = [
                'price', 'price_change', 'price_ma_5', 'price_ma_20',
                'price_std_5', 'volatility', 'bid_ask_spread', 'volume_ma',
                'hour', 'minute'
            ]

            ex_df = ex_df[['timestamp'] + feature_cols].copy()
            ex_df.columns = ['timestamp'] + [f"{exchange}_{col}" for col in feature_cols]

            features_list.append(ex_df)

        if not features_list:
            return pd.DataFrame()

        # Merge all exchange features on timestamp
        merged = features_list[0]
        for ex_features in features_list[1:]:
            merged = pd.merge(merged, ex_features, on='timestamp', how='outer')

        # Forward fill missing values
        # Use ffill() which is the modern equivalent of fillna(method='ffill')
        # Crucially, dropna() is too aggressive. We will handle NaNs later.
        merged = merged.sort_values('timestamp').ffill()


        return merged

    def create_target(self, df: pd.DataFrame, exchanges: List[str]) -> pd.Series:
        """Create target variable: future spread between exchanges."""
        if df.empty or len(exchanges) < 2:
            return pd.Series()

        # Calculate spread between first two exchanges
        ex1, ex2 = exchanges[0], exchanges[1]
        price_col1 = f"{ex1}_price"
        price_col2 = f"{ex2}_price"

        if price_col1 not in df.columns or price_col2 not in df.columns:
            return pd.Series()

        # Future spread (1 step ahead)
        spread = ((df[price_col2] - df[price_col1]) / df[price_col1]) * 100
        target = spread.shift(-1)  # Predict next spread

        return target

    def train(self, historical_df: pd.DataFrame):
        """Train the spread prediction model."""
        try:
            # Engineer features
            features_df = self.engineer_features(historical_df)

            if features_df.empty or len(features_df) < 50:
                logger.warning("Insufficient data for training")
                return False

            # Get unique exchanges
            exchanges = historical_df['exchange'].unique().tolist()

            if len(exchanges) < 2:
                logger.warning("Need at least 2 exchanges for training")
                return False

            # Create target
            target = self.create_target(features_df, exchanges)

            if target.empty:
                logger.warning("Failed to create target variable")
                return False

            # Align features and target
            features_df = features_df.iloc[:-1]  # Remove last row (no future target)
            target = target.iloc[:-1]  # Remove last row

            # Remove timestamp column
            if 'timestamp' in features_df.columns:
                features_df = features_df.drop('timestamp', axis=1)

            # Drop rows with NaN
            # A more robust way to handle NaNs after feature engineering
            combined = features_df.join(target.rename('target'))
            combined = combined.dropna()

            if len(combined) < 20:
                logger.warning("Not enough valid samples for training")
                return False

            X = combined.drop('target', axis=1)
            y = combined['target']

            # Store feature names
            self.feature_names = X.columns.tolist()

            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model.fit(X_train_scaled, y_train)

            # Evaluate
            self.r2_train = self.model.score(X_train_scaled, y_train)
            self.r2_test = self.model.score(X_test_scaled, y_test)

            logger.info(
                f"Model trained | Train R²: {self.r2_train:.3f} | Test R²: {self.r2_test:.3f}"
            )

            self.is_trained = True
            return True

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False

    def predict_spread(self, current_df: pd.DataFrame) -> Optional[float]:
        """Predict future spread from current data."""
        if not self.is_trained:
            return None

        try:
            features_df = self.engineer_features(current_df)

            if features_df.empty:
                return None

            # Get latest features
            latest = features_df.iloc[-1:]

            if 'timestamp' in latest.columns:
                latest = latest.drop('timestamp', axis=1)

            # Ensure same features as training
            missing_features = set(self.feature_names) - set(latest.columns)
            for feature in missing_features:
                latest[feature] = 0

            latest = latest[self.feature_names]

            # Fill any remaining NaNs that might occur with live data
            latest = latest.fillna(0)

            # Scale and predict
            X_scaled = self.scaler.transform(latest)
            prediction = self.model.predict(X_scaled)[0]

            return prediction

        except Exception as e:
            logger.error(f"Error predicting spread: {e}")
            return None

    def save(self, filepath: str):
        """Save model to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }, filepath)
        logger.info(f"Model saved to {filepath}")

    def load(self, filepath: str):
        """Load model from disk."""
        try:
            loaded_data = joblib.load(filepath)

            # Handle both dictionary and direct object saving for backward compatibility
            if isinstance(loaded_data, dict):
                # New format (dictionary of components)
                self.model = loaded_data['model']
                self.scaler = loaded_data['scaler']
                self.feature_names = loaded_data['feature_names']
                self.is_trained = loaded_data['is_trained']
            else:
                # Old format (direct object)
                logger.warning("Loading model from legacy object format. Consider retraining for consistency.")
                self.model = loaded_data.model
                self.scaler = loaded_data.scaler
                self.feature_names = loaded_data.feature_names
                self.is_trained = loaded_data.is_trained
                self.r2_train = getattr(loaded_data, 'r2_train', 0.0)
                self.r2_test = getattr(loaded_data, 'r2_test', 0.0)

            logger.success(f"Spread predictor loaded from {filepath}")
            return True
        except FileNotFoundError:
            logger.error(f"Predictor model file not found at {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error loading spread predictor: {e}")
            return False


class OpportunityScorer:
    """Scores arbitrage opportunities using ML."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.accuracy = 0.0

    def prepare_features(self, opportunity: ArbitrageOpportunity) -> np.ndarray:
        """Extract features from an arbitrage opportunity."""
        features = [
            opportunity.spread_pct,
            opportunity.profit_after_fees,
            opportunity.buy_price,
            opportunity.sell_price,
            opportunity.timestamp.hour,
            opportunity.timestamp.minute,
            hash(opportunity.buy_exchange) % 100,  # Simple encoding
            hash(opportunity.sell_exchange) % 100,
        ]
        return np.array(features).reshape(1, -1)

    def train(self, opportunities: List[ArbitrageOpportunity], labels: List[bool]):
        """
        Train classifier to predict if opportunity will persist.
        labels: True if opportunity was profitable, False otherwise
        """
        if len(opportunities) < 10:
            logger.warning("Insufficient data for training opportunity scorer")
            return False

        try:
            X = np.vstack([self.prepare_features(opp) for opp in opportunities])
            y = np.array(labels)

            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)

            self.accuracy = self.model.score(X_scaled, y)
            logger.info(f"Opportunity scorer trained | Accuracy: {self.accuracy:.3f}")

            self.is_trained = True
            return True

        except Exception as e:
            logger.error(f"Error training opportunity scorer: {e}")
            return False

    def score(self, opportunity: ArbitrageOpportunity) -> float:
        """Return confidence score (0-1) for an opportunity."""
        if not self.is_trained:
            return 0.5  # Neutral score

        try:
            X = self.prepare_features(opportunity)
            X_scaled = self.scaler.transform(X)
            proba = self.model.predict_proba(X_scaled)[0]

            # Handle both binary and single-class cases
            if len(proba) > 1:
                return proba[1]  # Probability of positive class
            else:
                # Only one class - return high confidence if it's the positive class
                return proba[0]
        except Exception as e:
            logger.error(f"Error scoring opportunity: {e}")
            return 0.5

    def save(self, filepath: str):
        """Save the scorer model and scaler to disk."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_trained': self.is_trained,
            'accuracy': self.accuracy
        }, filepath)
        logger.info(f"Opportunity scorer saved to {filepath}")

    def load(self, filepath: str):
        """Load the scorer model and scaler from disk."""
        try:
            loaded_data = joblib.load(filepath)

            # Handle both dictionary and direct object saving for backward compatibility
            if isinstance(loaded_data, dict):
                # New format (dictionary of components)
                self.model = loaded_data['model']
                self.scaler = loaded_data['scaler']
                self.is_trained = loaded_data['is_trained']
                self.accuracy = loaded_data.get('accuracy', 0.0)
            else:
                # Old format (direct object)
                logger.warning("Loading scorer from legacy object format. Consider retraining for consistency.")
                self.model = loaded_data.model
                self.scaler = loaded_data.scaler
                self.is_trained = loaded_data.is_trained
                self.accuracy = getattr(loaded_data, 'accuracy', 0.0)

            logger.success(f"Opportunity scorer loaded from {filepath}")
            return True
        except FileNotFoundError:
            logger.error(f"Scorer model file not found at {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error loading opportunity scorer: {e}")
            return False
