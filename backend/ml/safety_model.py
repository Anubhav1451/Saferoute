"""
Safety score prediction model.
Uses engineered features to predict a safety score between 0.0 and 1.0.
"""
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import joblib
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import logging
import csv
import json
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SafetyScoreModel:
    """
    A model for predicting safety scores based on environmental features.
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the model.

        Args:
            model_path: Path to a pre-trained model file. If None, a new model is created.
        """
        self.model_path = model_path
        self.feature_names = []
        self.pipeline = None
        self.train_stats = None  # Will store {'mean': [...], 'std': [...]}

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
            # Try to load training statistics
            model_dir = os.path.dirname(model_path)
            stats_file = os.path.join(model_dir, "train_stats.json")
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    self.train_stats = json.load(f)
                logger.info(f"Loaded training statistics from {stats_file}")
        else:
            # Create a pipeline for a new model
            self.pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                ))
            ])

    def prepare_features(self, features_dict: Dict[str, Any]) -> np.ndarray:
        """
        Convert a feature dictionary to a numpy array for model input.

        Args:
            features_dict: Dictionary of feature names to values

        Returns:
            Numpy array of features in the correct order
        """
        if not self.feature_names:
            # If we haven't seen features yet, use the keys from the dict
            # sorted to ensure consistent ordering
            self.feature_names = sorted(features_dict.keys())

        # Create array in the order of self.feature_names
        feature_array = np.array([
            features_dict.get(name, 0.0) for name in self.feature_names
        ]).reshape(1, -1)

        return feature_array

    def predict(self, features_dict: Dict[str, Any]) -> float:
        """
        Predict safety score for given features.

        Args:
            features_dict: Dictionary of feature names to values

        Returns:
            Safety score between 0.0 and 1.0
        """
        # Prepare features
        X = self.prepare_features(features_dict)

        # Make prediction
        prediction = self.pipeline.predict(X)[0]

        # Clamp to [0, 1] range
        prediction = max(0.0, min(1.0, prediction))

        # Log the prediction for monitoring
        self._log_prediction(features_dict, float(prediction))

        # Check for data drift (if we have training statistics)
        if self.train_stats is not None:
            self._check_drift(features_dict)

        return float(prediction)

    def _log_prediction(self, features_dict: Dict[str, Any], prediction: float):
        """
        Log the prediction to a CSV file for monitoring.

        Args:
            features_dict: The input features
            prediction: The predicted safety score
        """
        try:
            # Get the directory of the model (if available) or use current directory
            if self.model_path:
                log_dir = os.path.dirname(self.model_path)
            else:
                log_dir = os.getcwd()
            log_file = os.path.join(log_dir, "prediction_log.csv")

            # Prepare the log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'prediction': prediction
            }
            # Add all features
            for key, value in features_dict.items():
                log_entry[key] = value

            # Write to CSV
            file_exists = os.path.isfile(log_file)
            with open(log_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=log_entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)
        except Exception as e:
            logger.warning(f"Failed to log prediction: {e}")

    def _check_drift(self, features_dict: Dict[str, Any]):
        """
        Check for data drift by comparing input features to training statistics.
        Logs a warning if any feature is beyond 3 standard deviations from the mean.

        Args:
            features_dict: Dictionary of feature names to values
        """
        try:
            if not self.feature_names or not self.train_stats:
                return

            mean = np.array(self.train_stats['mean'])
            std = np.array(self.train_stats['std'])

            # Convert features_dict to array in the same order as feature_names
            feature_array = np.array([
                features_dict.get(name, 0.0) for name in self.feature_names
            ])

            # Calculate z-scores, avoiding division by zero
            # where std is zero, we set z-score to 0 (since all values are equal to mean)
            z_scores = np.zeros_like(feature_array)
            mask = std != 0
            z_scores[mask] = (feature_array[mask] - mean[mask]) / std[mask]

            # Check for any feature beyond 3 standard deviations
            if np.any(np.abs(z_scores) > 3):
                logger.warning(f"Potential data drift detected. Feature z-scores: {dict(zip(self.feature_names, z_scores))}")
        except Exception as e:
            logger.warning(f"Error during drift check: {e}")

    def train(
        self,
        features_list: List[Dict[str, Any]],
        labels: List[float],
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, float]:
        """
        Train the model on a dataset.

        Args:
            features_list: List of feature dictionaries
            labels: List of safety scores (float between 0.0 and 1.0)
            test_size: Proportion of data to use for testing
            random_state: Random seed for reproducibility

        Returns:
            Dictionary of training metrics
        """
        # Extract feature names from the first sample
        if features_list:
            self.feature_names = sorted(features_list[0].keys())

        # Convert list of dicts to numpy array
        X = np.array([
            [feat.get(name, 0.0) for name in self.feature_names]
            for feat in features_list
        ])

        y = np.array(labels)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Compute and store training statistics for drift detection
        train_mean = np.mean(X_train, axis=0)
        train_std = np.std(X_train, axis=0)
        # Avoid division by zero in std (set zero std to 1)
        train_std = np.where(train_std == 0, 1, train_std)
        self.train_stats = {
            'mean': train_mean.tolist(),
            'std': train_std.tolist()
        }

        # Create and train pipeline
        self.pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                n_jobs=-1
            ))
        ])

        self.pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        metrics = {
            "mae": mae,
            "r2": r2
        }

        logger.info(f"Model trained. MAE: {mae:.4f}, R2: {r2:.4f}")

        return metrics

    def save_model(self, path: str):
        """
        Save the model to disk.

        Args:
            path: Path to save the model
        """
        if self.pipeline is None:
            raise ValueError("No trained model to save")

        # Save both the pipeline and feature names
        model_data = {
            'pipeline': self.pipeline,
            'feature_names': self.feature_names
        }
        joblib.dump(model_data, path)
        self.model_path = path
        logger.info(f"Model saved to {path}")

        # Also save the training statistics if available
        if self.train_stats is not None:
            model_dir = os.path.dirname(path)
            stats_file = os.path.join(model_dir, "train_stats.json")
            with open(stats_file, 'w') as f:
                json.dump(self.train_stats, f, indent=2)
            logger.info(f"Saved training statistics to {stats_file}")

    def load_model(self, path: str):
        """
        Load a model from disk.

        Args:
            path: Path to the saved model
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        # Load the dictionary containing pipeline and feature names
        model_data = joblib.load(path)
        self.pipeline = model_data['pipeline']
        self.feature_names = model_data['feature_names']
        self.model_path = path
        logger.info(f"Model loaded from {path}")

        # Try to load training statistics
        model_dir = os.path.dirname(path)
        stats_file = os.path.join(model_dir, "train_stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                self.train_stats = json.load(f)
            logger.info(f"Loaded training statistics from {stats_file}")

# Global model instance
_safety_model = None

def get_safety_model() -> SafetyScoreModel:
    """
    Get or create the global safety score model instance.
    Uses lazy initialization.
    """
    global _safety_model
    if _safety_model is None:
        # Try to load a pre-trained model, otherwise create a new one
        model_path = os.path.join(os.path.dirname(__file__), "models", "safety_model.joblib")
        _safety_model = SafetyScoreModel(model_path)
    return _safety_model

def predict_safety_score(
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None,
    radius_meters: float = 1000.0,
    db: Optional[Session] = None
) -> float:
    """
    Convenience function to predict safety score for a location.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        timestamp: Time for which to predict safety (defaults to now)
        radius_meters: Radius to consider for features (defaults to 1000m)
        db: Database session (optional, will create one if not provided)

    Returns:
        Safety score between 0.0 and 1.0
    """
    from .feature_engineering import engineer_features
    from .data_ingestion import get_safety_data_for_location

    # Get a database session if not provided
    if db is None:
        from app.db.session import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    try:
        # Engineer features
        features = engineer_features(
            latitude, longitude, timestamp, radius_meters, db
        )

        # Get model and predict
        model = get_safety_model()
        # Convert dataclass to dictionary for the predict method
        from dataclasses import asdict
        features_dict = asdict(features)
        safety_score = model.predict(features_dict)

        return safety_score
    except Exception as e:
        logger.error(f"Error predicting safety score: {e}")
        # Return neutral score on error
        return 0.5
    finally:
        if close_db:
            db.close()