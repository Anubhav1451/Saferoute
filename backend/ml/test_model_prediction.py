#!/usr/bin/env python
"""
Test the safety score model prediction.
"""
import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.ml.safety_model import predict_safety_score
from app.ml.feature_engineering import engineer_features

def test_predict_safety_score():
    """Test that the predict_safety_score function returns a value between 0 and 1."""
    # Mock the database session and the feature engineering function
    with patch('app.ml.safety_model.get_safety_model') as mock_get_model, \
         patch('app.ml.safety_model.engineer_features') as mock_engineer:

        # Mock the model to return a fixed value
        mock_model = Mock()
        mock_model.predict.return_value = 0.7
        mock_get_model.return_value = mock_model

        # Mock the feature engineering to return a dummy feature dict
        mock_engineer.return_value = {
            'hour': 12, 'day_of_week': 1, 'day_of_month': 15, 'month': 6,
            'is_weekend': 0, 'is_night': 0, 'latitude': 28.6315, 'longitude': 77.2167,
            'crime_density_weighted': 0.1, 'crime_high_count': 0, 'crime_medium_count': 1,
            'crime_low_count': 2, 'crime_weighted_severity_avg': 1.5,
            'lighting_avg': 0.8, 'low_lighting_count': 0, 'total_safety_nodes': 10,
            'crowd_density_avg': 0.6, 'sparse_crowd_count': 2, 'total_safety_nodes_2': 10,
            'report_density_weighted': 0.5
        }

        # Call the function
        score = predict_safety_score(latitude=28.6315, longitude=77.2167)

        # Assertions
        assert 0.0 <= score <= 1.0, f"Safety score {score} is not in [0, 1]"
        assert score == 0.7, f"Expected 0.7, got {score}"

        print("Model prediction test passed!")

if __name__ == "__main__":
    test_predict_safety_score()