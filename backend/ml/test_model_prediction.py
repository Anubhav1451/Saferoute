#!/usr/bin/env python
"""
Test the safety score model prediction.
"""
import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
print("sys.path:", sys.path)

from ml.safety_model import predict_safety_score
from ml.feature_engineering import engineer_features

def test_predict_safety_score():
    """Test that the predict_safety_score function returns a value between 0 and 1."""
    # Mock the database session and the feature engineering function
    with patch('ml.safety_model.get_safety_model') as mock_get_model, \
         patch('ml.feature_engineering.engineer_features') as mock_engineer:

        # Mock the model to return a fixed value
        mock_model = Mock()
        mock_model.predict.return_value = 0.7
        mock_get_model.return_value = mock_model

        # Mock the feature engineering to return a RoadSegmentFeatures object
        from ml.feature_engineering import RoadSegmentFeatures
        mock_features = RoadSegmentFeatures(
            road_class=0.5, lanes=0.5, speed_limit=0.5, one_way=0.0, junction=0.0,
            bridge=0.0, tunnel=0.0, curvature=0.5, elevation=0.5, urban_rural=0.5,
            lighting=0.5, surface=0.5, smoothness=0.5,
            accident_count=0.1, fatal_count=0.0, grievous_count=0.2, blackspot_count=0.0,
            accident_density=0.1, severity_index=0.2, recency_weight=0.5, confidence=0.8,
            weather=0.5, traffic=0.5, visibility=0.5, construction=0.5,
            degree=0.5, betweenness=0.5, closeness=0.5, connectivity=0.5
        )
        mock_engineer.return_value = mock_features

        # Call the function
        score = predict_safety_score(latitude=28.6315, longitude=77.2167)

        # Assertions
        assert 0.0 <= score <= 1.0, f"Safety score {score} is not in [0, 1]"
        assert score == 0.7, f"Expected 0.7, got {score}"

        print("Model prediction test passed!")

if __name__ == "__main__":
    test_predict_safety_score()