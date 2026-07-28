#!/usr/bin/env python
"""
Test the caching of safety data and graph in the routing service.
"""
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate
from sqlalchemy.orm import Session

def create_mock_safety_node(lat, lon, safety_score=0.5, lighting_level=LightingLevel.MEDIUM, crowd_density=CrowdDensity.NORMAL):
    """Create a mock safety node."""
    node = Mock(spec=SafetyNode)
    node.latitude = lat
    node.longitude = lon
    node.safety_score = safety_score
    node.lighting_level = lighting_level
    node.crowd_density = crowd_density
    node.updated_at = datetime.utcnow()
    return node

def create_mock_crime_hotspot(lat, lon, radius, severity=SeverityLevel.MEDIUM):
    """Create a mock crime hotspot."""
    hotspot = Mock(spec=CrimeHotspot)
    hotspot.latitude = lat
    hotspot.longitude = lon
    hotspot.radius = radius
    hotspot.severity = severity
    return hotspot

def create_mock_user_report(lat, lon, days_ago=0, is_active=True):
    """Create a mock user report."""
    report = Mock(spec=UserReport)
    report.latitude = lat
    report.longitude = lon
    report.timestamp = datetime.utcnow() - timedelta(days=days_ago)
    report.is_active = is_active
    return report

def test_caching():
    """Test that the second request for the same corridor uses the cache."""
    # Mock the database session
    db = Mock(spec=Session)

    # Create the routing service
    routing_service = SafetyRoutingService(db)

    # Delhi and Saharanpur coordinates
    source = Coordinate(latitude=28.6315, longitude=77.2167)  # Delhi
    destination = Coordinate(latitude=29.9660, longitude=77.5540)  # Saharanpur

    # We'll create some mock safety data for the corridor
    # We'll create a few safety nodes along the path
    import math

    # Function to generate points between source and destination
    def generate_points(start_lat, start_lon, end_lat, end_lon, num_points=10):
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            lat = start_lat + t * (end_lat - start_lat)
            lon = start_lon + t * (end_lon - start_lon)
            points.append((lat, lon))
        return points

    # Generate 5 safety nodes along the corridor
    safety_points = generate_points(28.6315, 77.2167, 29.9660, 77.5540, 5)
    mock_safety_nodes = []
    for lat, lon in safety_points:
        node = create_mock_safety_node(lat, lon, safety_score=0.7, lighting_level=LightingLevel.MEDIUM, crowd_density=CrowdDensity.NORMAL)
        mock_safety_nodes.append(node)

    # Create a few mock crime hotspots
    mock_crime_hotspots = [
        create_mock_crime_hotspot(29.0, 77.3, radius=5000, severity=SeverityLevel.HIGH),
        create_mock_crime_hotspot(29.5, 77.4, radius=3000, severity=SeverityLevel.MEDIUM)
    ]

    # Create a few mock user reports
    mock_user_reports = [
        create_mock_user_report(28.8, 77.25, days_ago=2),
        create_mock_user_report(29.2, 77.4, days_ago=5)
    ]

    # Create empty lists for the other types of data
    mock_segment_risks = []
    mock_black_spots = []
    mock_accident_records = []

    # Now, we need to mock the database methods to return this data
    def mock_get_nearby_safety_data_bounding_box(min_lat, max_lat, min_lon, max_lon):
        # Filter the mock data to those within the bounding box
        nodes = [n for n in mock_safety_nodes if min_lat <= n.latitude <= max_lat and min_lon <= n.longitude <= max_lon]
        hotspots = [h for h in mock_crime_hotspots if min_lat <= h.latitude <= max_lat and min_lon <= h.longitude <= max_lon]
        reports = [r for r in mock_user_reports if min_lat <= r.latitude <= max_lat and min_lon <= r.longitude <= max_lon]
        return (nodes, hotspots, reports, mock_segment_risks)

    def mock_get_nearby_safety_data(lat, lon, radius_meters=None):
        # Use a default radius if not provided
        if radius_meters is None:
            radius_meters = 10000  # 10km
        # Convert radius to degrees (approx)
        radius_deg = radius_meters / 111000.0
        min_lat = lat - radius_deg
        max_lat = lat + radius_deg
        min_lon = lon - radius_deg / math.cos(math.radians(lat))
        max_lon = lon + radius_deg / math.cos(math.radians(lat))
        nodes = [n for n in mock_safety_nodes if min_lat <= n.latitude <= max_lat and min_lon <= n.longitude <= max_lon]
        hotspots = [h for h in mock_crime_hotspots if min_lat <= h.latitude <= max_lat and min_lon <= h.longitude <= max_lon]
        reports = [r for r in mock_user_reports if min_lat <= r.latitude <= max_lat and min_lon <= r.longitude <= max_lon]
        return (nodes, hotspots, reports, mock_segment_risks)

    # Also mock the AI safety score to return a valid value
    def mock_calculate_ai_safety_score(latitude, longitude, timestamp=None):
        # Return a safety score based on latitude for variation
        return 0.5 + 0.5 * (latitude - 28) / (30 - 28)  # ranges from 0.5 to 1.0

    # Mock the database queries for black spots and accident records
    def mock_query(model):
        query_mock = MagicMock()
        if model.__name__ == 'HighwayBlackSpot':
            query_mock.all.return_value = mock_black_spots
        elif model.__name__ == 'AccidentRecord':
            query_mock.all.return_value = mock_accident_records
        else:
            # For other models (SafetyNode, CrimeHotspot, UserReport, RoadSegmentRisk)
            # we'll handle this in the specific method mocks above
            query_mock.all.return_value = []
        return query_mock

    db.query.side_effect = mock_query

    # Patch the methods
    with patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data_bounding_box') as mock_bounding_box, \
         patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data') as mock_radius, \
         patch('app.services.routing.SafetyRoutingService.calculate_ai_safety_score') as mock_ai, \
         patch('app.services.graph_utils.GraphSpatialIndex') as mock_gsi:
        mock_bounding_box.side_effect = mock_get_nearby_safety_data_bounding_box
        mock_radius.side_effect = mock_get_nearby_safety_data
        mock_ai.side_effect = mock_calculate_ai_safety_score
        # Mock the GraphSpatialIndex to avoid database queries
        mock_gsi_instance = MagicMock()
        mock_gsi_instance._node_grid = {}
        mock_gsi_instance._edge_grid = {}
        mock_gsi.return_value = mock_gsi_instance

        # First request
        print("=== First request ===")
        start_time = time.time()
        result1 = routing_service.find_safest_route(source, destination, safety_weight=0.5)
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.3f} seconds")
        print(f"Safest route safety score: {result1['safest_safety_score']:.4f}")
        print(f"Fastest route safety score: {result1['fastest_safety_score']:.4f}")

        # Second request (should hit cache)
        print("\n=== Second request ===")
        start_time = time.time()
        result2 = routing_service.find_safest_route(source, destination, safety_weight=0.5)
        end_time = time.time()
        print(f"Time taken: {end_time - start_time:.3f} seconds")
        print(f"Safest route safety score: {result2['safest_safety_score']:.4f}")
        print(f"Fastest route safety score: {result2['fastest_safety_score']:.4f}")

        # Check that the results are the same (or at least the safety scores are close)
        print("\n=== Comparison ===")
        print(f"Safest safety scores equal? {abs(result1['safest_safety_score'] - result2['safest_safety_score']) < 0.001}")
        print(f"Fastest safety scores equal? {abs(result1['fastest_safety_score'] - result2['fastest_safety_score']) < 0.001}")
        print(f"Safest route coord count: {len(result1['safest_route'])} vs {len(result2['safest_route'])}")
        print(f"Fastest route coord count: {len(result1['fastest_route'])} vs {len(result2['fastest_route'])}")

if __name__ == '__main__':
    test_caching()