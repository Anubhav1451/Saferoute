#!/usr/bin/env python
"""
Test the safety score API endpoint.
"""
import sys
import os
from fastapi.testclient import TestClient

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.main import app  # Assuming the FastAPI app is in app/main.py

def test_safety_score_endpoint():
    """Test the /api/v1/ai/safety-score endpoint."""
    client = TestClient(app)

    # Make a request to the endpoint
    response = client.get(
        "/api/v1/ai/safety-score",
        params={
            "latitude": 28.6315,
            "longitude": 77.2167,
            "radius_meters": 1000.0
        }
    )

    # Check that the request was successful
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Check the response JSON
    data = response.json()
    assert "safety_score" in data, "Response missing 'safety_score'"
    assert "timestamp" in data, "Response missing 'timestamp'"
    assert "risk_factors" in data, "Response missing 'risk_factors'"
    assert 0.0 <= data["safety_score"] <= 1.0, f"Safety score {data['safety_score']} not in [0, 1]"

    print("API endpoint test passed!")

if __name__ == "__main__":
    test_safety_score_endpoint()