"""
Training script for the safety score model.
Generates realistic training data and trains a machine learning model to predict safety scores.
"""
import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import logging
import csv
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import math

# Add the parent directory to the path so we can import app and ml modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ml.data_ingestion import (
    get_recent_safety_nodes,
    get_recent_crime_hotspots,
    get_recent_user_reports,
    get_safety_data_for_location
)
from ml.feature_engineering import engineer_features
from ml.safety_model import SafetyScoreModel
from app.db.session import SessionLocal
from app.services.routing import SafetyRoutingService
from app.schemas.routing import Coordinate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = 6371000 * c  # Earth's radius in meters

    return distance

def generate_realistic_training_data(
    num_samples: int = 10000,
    center_lat: float = 28.6315,
    center_lon: float = 77.2167,
    lat_spread: float = 0.05,
    lon_spread: float = 0.05,
    time_range_days: int = 30
) -> Tuple[List[Dict[str, Any]], List[float]]:
    """
    Generate realistic training data by sampling locations and times
    and computing safety scores using a hybrid approach.

    Returns:
        Tuple of (features_list, labels)
    """
    # Create a database session
    db = SessionLocal()

    try:
        # Initialize the routing service for ground truth safety scores
        routing_service = SafetyRoutingService(db)

        features_list = []
        labels = []

        # Current time for reference
        now = datetime.utcnow()

        for i in range(num_samples):
            if i % 1000 == 0:
                logger.info(f"Generated {i}/{num_samples} samples")

            # Generate random location near center
            latitude = center_lat + np.random.uniform(-lat_spread, lat_spread)
            longitude = center_lon + np.random.uniform(-lon_spread, lon_spread)

            # Generate random time within the last N days
            days_ago = np.random.uniform(0, time_range_days)
            hours_ago = np.random.uniform(0, 24)
            minutes_ago = np.random.uniform(0, 60)
            seconds_ago = np.random.uniform(0, 60)

            # Calculate timestamp (in the past)
            delta = timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago, seconds=seconds_ago)
            timestamp = now - delta

            # Engineer features for this point
            try:
                features = engineer_features(
                    latitude, longitude, timestamp, radius_meters=1000.0, db=db
                )
            except Exception as e:
                logger.warning(f"Error engineering features for point {i}: {e}")
                continue

            # Get ground truth safety score from routing service
            try:
                # Create a small route around the point to get a safety score
                # We'll use a dummy destination very close by
                dest_lat = latitude + 0.0001  # ~11 meters north
                dest_lon = longitude  # Same longitude

                source = Coordinate(latitude=latitude, longitude=longitude)
                destination = Coordinate(latitude=dest_lat, longitude=dest_lon)

                # Get safety score for this short route
                result = routing_service.find_safest_route(
                    source=source,
                    destination=destination,
                    safety_weight=0.7  # Favor safety
                )

                # Extract the safety score from the result
                # For a very short route, this should be representative of the point
                safety_score = result.get('safest_safety_score', 0.5)

                # Add some noise to make learning more realistic
                noise = np.random.normal(0, 0.05)
                safety_score = max(0.0, min(1.0, safety_score + noise))

            except Exception as e:
                logger.warning(f"Error getting ground truth for point {i}: {e}")
                # Fallback to a heuristic based on features
                # More sophisticated heuristic using multiple factors
                crime_density = features.get('crime_density_weighted', 0)
                crime_high = features.get('crime_high_count', 0)
                lighting_avg = features.get('lighting_avg', 0.5)
                low_lighting = features.get('low_lighting_count', 0)
                sparse_crowd = features.get('sparse_crowd_count', 0)
                report_recent = features.get('report_weighted_recent', 0)
                report_severity = features.get('report_weighted_severity', 0)

                # Normalize features (approximate max values)
                crime_density_norm = min(1.0, crime_density / 5.0)  # Assume max 5 weighted crimes
                crime_risk = min(1.0, (crime_high * 2 + crime_density) / 10.0)  # Weight high severity more
                lighting_risk = 1.0 - lighting_avg  # Invert so higher = worse
                darkness_risk = min(1.0, low_lighting / 10.0)
                crowd_risk = min(1.0, sparse_crowd / 10.0)
                report_risk = min(1.0, report_recent / 5.0)
                severity_risk = min(1.0, report_severity / 3.0)  # Assume max severity 3

                # Combine risks with weights
                risk_score = (
                    0.25 * crime_risk +
                    0.20 * lighting_risk +
                    0.15 * darkness_risk +
                    0.15 * crowd_risk +
                    0.15 * report_risk +
                    0.10 * severity_risk
                )

                # Safety is inverse of risk
                safety_score = 1.0 - risk_score
                # Add noise
                safety_score = max(0.0, min(1.0, safety_score + np.random.normal(0, 0.1)))

            features_list.append(features)
            labels.append(safety_score)

        logger.info(f"Generated {len(features_list)} training samples")
        return features_list, labels

    finally:
        db.close()

def train_and_evaluate_models(
    features_list: List[Dict[str, Any]],
    labels: List[float],
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[Any, dict, list, dict]:
    """
    Train multiple models, evaluate them, and return the best one.

    Returns:
        Tuple of (best_model, metrics, feature_names, train_stats)
    """
    # Extract feature names from the first sample
    if not features_list:
        raise ValueError("No features provided")

    feature_names = sorted(features_list[0].keys())

    # Convert list of dicts to numpy array
    X = np.array([[feat.get(name, 0.0) for name in feature_names] for feat in features_list])
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
    train_stats = {
        'mean': train_mean.tolist(),
        'std': train_std.tolist()
    }

    # Define models to try
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=random_state
        )
    }

    # Track best model
    best_score = float('inf')  # For MAE, lower is better
    best_model_name = None
    best_model = None
    all_metrics = {}

    # Train and evaluate each model
    for name, model in models.items():
        # Create pipeline with scaling
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', model)
        ])

        # Train
        pipeline.fit(X_train, y_train)

        # Predict
        y_pred = pipeline.predict(X_test)

        # Calculate metrics
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)

        # Mean Absolute Percentage Error (MAPE) - avoid division by zero
        epsilon = 1e-10
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + epsilon))) * 100

        # Percentage of predictions within 0.05 and 0.1 of true value
        within_05 = np.mean(np.abs(y_test - y_pred) < 0.05) * 100
        within_10 = np.mean(np.abs(y_test - y_pred) < 0.1) * 100

        # Cross-validation score
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5,
                                  scoring='neg_mean_absolute_error')
        cv_mae = -np.mean(cv_scores)

        metrics = {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "mape": mape,
            "within_05": within_05,
            "within_10": within_10,
            "cv_mae": cv_mae
        }

        all_metrics[name] = metrics

        logger.info(f"{name} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}, MAPE: {mape:.2f}%, "
                   f"Within 0.05: {within_05:.2f}%, Within 0.1: {within_10:.2f}%, CV-MAE: {cv_mae:.4f}")

        # Update best model
        if mae < best_score:
            best_score = mae
            best_model_name = name
            best_model = pipeline

    logger.info(f"Best model: {best_model_name} with MAE: {best_score:.4f}")

    return best_model, all_metrics[best_model_name], feature_names, train_stats

def train_model(
    model_output_path: str = "models/safety_model.joblib",
    num_samples: int = 10000
) -> None:
    """
    Train the safety score model and save it to disk.

    Args:
        model_output_path: Path where to save the trained model
        num_samples: Number of training samples to generate
    """
    # Create models directory if it doesn't exist
    model_dir = os.path.dirname(model_output_path)
    if model_dir:
        os.makedirs(model_dir, exist_ok=True)

    # Backup existing model if present
    if os.path.exists(model_output_path):
        backup_dir = os.path.join(model_dir, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"safety_model_{timestamp}.joblib")
        import shutil
        shutil.copy2(model_output_path, backup_path)
        logger.info(f"Backed up existing model to {backup_path}")

    # Generate training data
    logger.info("Generating training data...")
    features_list, labels = generate_realistic_training_data(num_samples=num_samples)

    if len(features_list) == 0:
        raise ValueError("No training data generated")

    # Train and evaluate models
    logger.info("Training models...")
    best_model, metrics, feature_names, train_stats = train_and_evaluate_models(
        features_list, labels
    )

    # Prepare model data for saving
    model_data = {
        'pipeline': best_model,
        'feature_names': feature_names
    }

    # Save model
    logger.info(f"Saving model to {model_output_path}")
    joblib.dump(model_data, model_output_path)

    # Save training statistics for drift detection
    stats_file = os.path.join(model_dir, "train_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(train_stats, f, indent=2)
    logger.info(f"Saved training statistics to {stats_file}")

    # Log metrics to a file for tracking
    log_file = os.path.join(model_dir, "training_log.csv")
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'model_type': type(best_model.named_steps['regressor']).__name__,
        'num_samples': len(features_list),
        'mae': metrics['mae'],
        'rmse': metrics['rmse'],
        'r2': metrics['r2'],
        'mape': metrics['mape'],
        'within_05': metrics['within_05'],
        'within_10': metrics['within_10'],
        'cv_mae': metrics['cv_mae']
    }

    # Write to CSV without pandas
    file_exists = os.path.isfile(log_file)
    with open(log_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

    # Print metrics
    print(f"\nTraining completed!")
    print(f"  Model type: {log_entry['model_type']}")
    print(f"  Samples: {len(features_list)}")
    print(f"  MAE: {metrics['mae']:.4f}")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  R2: {metrics['r2']:.4f}")
    print(f"  MAPE: {metrics['mape']:.2f}%")
    print(f"  Within 0.05: {metrics['within_05']:.2f}%")
    print(f"  Within 0.1: {metrics['within_10']:.2f}%")
    print(f"  CV-MAE: {metrics['cv_mae']:.4f}")
    print(f"  Model saved to: {model_output_path}")
    print(f"  Training stats saved to: {stats_file}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train safety score model")
    parser.add_argument(
        "--samples",
        type=int,
        default=10000,
        help="Number of training samples to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/safety_model.joblib",
        help="Path to save the trained model"
    )

    args = parser.parse_args()

    # Convert relative path to absolute if needed
    if not os.path.isabs(args.output):
        # Make it relative to the backend/ml directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_output_path = os.path.join(script_dir, args.output)
    else:
        model_output_path = args.output

    train_model(model_output_path=model_output_path, num_samples=args.samples)