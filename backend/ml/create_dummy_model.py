#!/usr/bin/env python
"""
Create a dummy safety model for testing purposes.
This model returns a constant safety score of 0.5 for any input.
"""
import os
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

class DummyRegressor:
    """A dummy regressor that always returns 0.5"""
    def fit(self, X, y):
        return self

    def predict(self, X):
        return np.full((X.shape[0],), 0.5)

# Create a pipeline with the dummy regressor
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', DummyRegressor())
])

# Feature names must match what the feature engineering produces
# We'll use the same list as in the feature engineering function (after fixing duplicates)
feature_names = [
    'hour', 'day_of_week', 'day_of_month', 'month', 'is_weekend', 'is_night',
    'latitude', 'longitude',
    'crime_density_weighted', 'crime_high_count', 'crime_medium_count', 'crime_low_count',
    'crime_weighted_severity_avg',
    'lighting_avg', 'low_lighting_count', 'total_safety_nodes',
    'crowd_density_avg', 'sparse_crowd_count', 'total_safety_nodes',  # Note: removed duplicate
    'report_density_weighted'
]

# Create a model data dictionary
model_data = {
    'pipeline': pipeline,
    'feature_names': feature_names
}

# Ensure the models directory exists
model_dir = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(model_dir, exist_ok=True)

# Save the model
model_path = os.path.join(model_dir, 'safety_model.joblib')
joblib.dump(model_data, model_path)
print(f"Dummy model saved to {model_path}")