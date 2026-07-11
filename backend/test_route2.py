#!/usr/bin/env python
"""
Test the routing service with given coordinates.
"""
import sys
import os
from unittest.mock import Mock, patch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate
from sqlalchemy.orm import Session

def test_routing_with_mock_data():
    """Test the routing service with mock data to avoid database dependency."""
    # Mock the database session
    db = Mock(spec=Session)

    # Create the routing service
    routing_service = SafetyRoutingService(db)

    # Mock the safety data to return some dummy data
    # We'll create a few safety nodes along a path from Delhi to the destination
    # For simplicity, we'll make the safety data return empty so that penalties are zero
    # and the safest and fastest routes should be the same (straight line)
    # But we want to see the coordinates.

    # We'll mock get_nearby_safety_data to return empty lists
    with patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data') as mock_get_data:
        mock_get_data.return_value = ([], [], [])

        # Also mock the AI safety score to return -1 (so it falls back to rule-based)
        with patch('app.services.routing.SafetyRoutingService.calculate_ai_safety_score') as mock_ai:
            mock_ai.return_value = -1.0

            # Create dummy source and destination
            source = Coordinate(latitude=28.6315, longitude=77.2167)
            destination = Coordinate(latitude=29.9660, longitude=77.5540)

            # Call the routing function
            result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

            # Print the results
            print("Safest route coordinate count:", len(result['safest_route']))
            print("Fastest route coordinate count:", len(result['fastest_route']))
            print("Safest route safety score:", result['safest_safety_score'])
            print("Fastest route safety score:", result['fastest_safety_score'])
            print("Are the routes different?", result['safest_route'] != result['fastest_route'])

            # Print all coordinates of safest route for inspection
            print("\nSafest route coordinates:")
            for i, coord in enumerate(result['safest_route']):
                print(f"  {i}: {coord}")
            print("\nFastest route coordinates:")
            for i, coord in enumerate(result['fastest_route']):
                print(f"  {i}: {coord}")

if __name__ == '__main__':
    test_routing_with_mock_data()