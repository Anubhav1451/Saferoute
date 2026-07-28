#!/usr/bin/env python
"""
Test script for the AI safety score API endpoint.
"""
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient
from backend.app.main import app

def test_safety_score_endpoint():
    """Test the /api/v1/ai/safety-score endpoint."""
    print("Testing /api/v1/ai/safety-score endpoint...")

    client = TestClient(app)

    # Test with valid parameters
    response = client.get(
        "/api/v1/ai/safety-score",
        params={
            "latitude": 28.6315,
            "longitude": 77.2167,
            "radius_meters": 1000.0
        }
    )

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")

        # Check required fields
        required_fields = ["safety_score", "timestamp", "risk_factors"]
        for field in required_fields:
            if field not in data:
                print(f"✗ Missing field: {field}")
                return False

        # Check safety_score is a float between 0 and 1
        score = data["safety_score"]
        if not isinstance(score, (int, float)):
            print(f"✗ safety_score is not a number: {score}")
            return False

        if not (0.0 <= score <= 1.0):
            print(f"✗ safety_score out of range [0,1]: {score}")
            return False

        print("✓ Safety score is valid float in [0,1]")

        # Check timestamp is string
        if not isinstance(data["timestamp"], str):
            print("✗ timestamp is not a string")
            return False
        print("✓ Timestamp is string")

        # Check risk_factors is dict
        if not isinstance(data["risk_factors"], dict):
            print("✗ risk_factors is not a dictionary")
            return False
        print("✓ Risk factors is dictionary")

        print("✓ All checks passed!")
        return True
    else:
        print(f"✗ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_safety_score_endpoint_defaults():
    """Test the endpoint with default parameters."""
    print("\nTesting /api/v1/ai/safety-score endpoint with defaults...")

    client = TestClient(app)

    # Test with minimal parameters (should use defaults)
    response = client.get("/api/v1/ai/safety-score")

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data}")
        print("✓ Default parameters work")
        return True
    else:
        print(f"✗ Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("AI Safety Score API Endpoint Test")
    print("=" * 50)

    all_passed = True

    all_passed &= test_safety_score_endpoint()
    all_passed &= test_safety_score_endpoint_defaults()

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All API tests passed!")
    else:
        print("✗ Some API tests failed.")
    print("=" * 50)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())