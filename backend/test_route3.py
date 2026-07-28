#!/usr/bin/env python
"""
Test the routing service with safety nodes along the path.
"""
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate
from sqlalchemy.orm import Session

def test_routing_with_safety_nodes():
    """Test the routing service with safety nodes along the path."""
    # Mock the database session
    db = Mock(spec=Session)

    # Mock the database queries for black_spots and accident_records
    def mock_query(*args, **kwargs):
        # args[0] is self, args[1] is the model class
        if len(args) >= 2:
            model = args[1]
        else:
            # If we can't get the model, return empty list
            query_mock = MagicMock()
            query_mock.all.return_value = []
            return query_mock

        query_mock = MagicMock()
        if model.__name__ == 'HighwayBlackSpot':
            query_mock.all.return_value = []
        elif model.__name__ == 'AccidentRecord':
            query_mock.all.return_value = []
        else:
            # For other models (SafetyNode, CrimeHotspot, UserReport, RoadSegmentRisk, etc.)
            # we'll handle this in the specific method mocks below
            query_mock.all.return_value = []
        return query_mock

    db.query.side_effect = mock_query

    # Create the routing service
    routing_service = SafetyRoutingService(db)

    # We'll mock the safety data to return some safety nodes along a straight line from source to destination
    source = Coordinate(latitude=28.6315, longitude=77.2167)
    destination = Coordinate(latitude=29.9660, longitude=77.5540)

    # Create some safety nodes along the path
    import math
    def interpolate(start, end, fraction):
        lat = start.latitude + fraction * (end.latitude - start.latitude)
        lon = start.longitude + fraction * (end.longitude - start.longitude)
        return Coordinate(latitude=lat, longitude=lon)

    node1 = interpolate(source, destination, 0.25)
    node2 = interpolate(source, destination, 0.5)
    node3 = interpolate(source, destination, 0.75)

    # Create SafetyNode objects
    safety_nodes = [
        SafetyNode(id=1, latitude=node1.latitude, longitude=node1.longitude, safety_score=0.9,
                   lighting_level=LightingLevel.HIGH, crowd_density=CrowdDensity.DENSE, updated_at=None),
        SafetyNode(id=2, latitude=node2.latitude, longitude=node2.longitude, safety_score=0.9,
                   lighting_level=LightingLevel.HIGH, crowd_density=CrowdDensity.DENSE, updated_at=None),
        SafetyNode(id=3, latitude=node3.latitude, longitude=node3.longitude, safety_score=0.9,
                   lighting_level=LightingLevel.HIGH, crowd_density=CrowdDensity.DENSE, updated_at=None),
    ]

    # Mock the safety data to return these safety nodes, and empty for others
    def mock_get_nearby_safety_data_bounding_box(min_lat, max_lat, min_lon, max_lon):
        # For simplicity, we return the same safety nodes regardless of location
        # In reality, we would filter by the bounding box, but for this test we want to see if they are used
        return (safety_nodes, [], [], [])

    # Also mock the radius-based version for completeness
    def mock_get_nearby_safety_data(lat, lon, radius_meters=None):
        return (safety_nodes, [], [], [])

    # Patch both methods
    with patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data_bounding_box') as mock_bounding_box, \
         patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data') as mock_radius:
        mock_bounding_box.side_effect = mock_get_nearby_safety_data_bounding_box
        mock_radius.side_effect = mock_get_nearby_safety_data

        # Mock the AI safety score to return a valid value so we don't need to calculate penalty
        with patch('app.services.routing.SafetyRoutingService.calculate_ai_safety_score') as mock_ai:
            mock_ai.return_value = 0.9  # Valid safety score

            # Call the routing function
            result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

            # Print the results
            print("Safest route coordinate count:", len(result['safest_route']))
            print("Fastest route coordinate count:", len(result['fastest_route']))
            print("Safest route safety score:", result['safest_safety_score'])
            print("Fastest route safety score:", result['fastest_safety_score'])
            print("Are the routes different?", result['safest_route'] != result['fastest_route'])

            # Check if the safety nodes are in the route (approximately)
            def is_close(coord1, coord2, tolerance=0.01):  # tolerance in degrees (~1km)
                return abs(coord1['latitude'] - coord2['latitude']) < tolerance and abs(coord1['longitude'] - coord2['longitude']) < tolerance

            safety_points = [
                {'latitude': node1.latitude, 'longitude': node1.longitude},
                {'latitude': node2.latitude, 'longitude': node2.longitude},
                {'latitude': node3.latitude, 'longitude': node3.longitude}
            ]

            safest_route = result['safest_route']
            fastest_route = result['fastest_route']

            print("\nChecking if safety nodes are in the routes:")
            for i, safety_point in enumerate(safety_points):
                found_in_safest = any(is_close(point, safety_point) for point in safest_route)
                found_in_fastest = any(is_close(point, safety_point) for point in fastest_route)
                print(f"  Safety node {i+1}: safest={found_in_safest}, fastest={found_in_fastest}")

            # Print first and last few coordinates of each route
            print("\nSafest route (first 3 and last 3):")
            for i in range(min(3, len(safest_route))):
                print(f"  {i}: {safest_route[i]}")
            for i in range(max(0, len(safest_route)-3), len(safest_route)):
                print(f"  {i}: {safest_route[i]}")

            print("\nFastest route (first 3 and last 3):")
            for i in range(min(3, len(fastest_route))):
                print(f"  {i}: {fastest_route[i]}")
            for i in range(max(0, len(fastest_route)-3), len(fastest_route)):
                print(f"  {i}: {fastest_route[i]}")

if __name__ == '__main__':
    test_routing_with_safety_nodes()