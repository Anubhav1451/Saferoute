#!/usr/bin/env python
"""
Test the routing service functionality against the current GIS routing
implementation using an in-memory graph.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from routing_test_helpers import (
    create_graph_session,
    default_source,
    default_destination,
    assert_valid_route_result,
)


def test_routing_service_with_mock_data():
    """Test the routing service against a small in-memory GIS graph."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        assert_valid_route_result(result)
        assert len(result["safest_route"]) >= 2
        assert len(result["fastest_route"]) >= 2
        assert len(result["route_segments"]) >= 1

        # _calculate_safety_score now derives each segment's score from the
        # nearby RoadSegmentRisk record (risk_score 0.2 on edge 1 -> 0.8,
        # risk_score 0.5 on edge 2 -> 0.5), so the route average is 0.65.
        assert abs(result["safest_safety_score"] - 0.65) < 0.001
        assert abs(result["fastest_safety_score"] - 0.65) < 0.001

        # Distance is computed via Haversine over the returned coordinates.
        assert result["safest_distance"] > 0
        assert result["fastest_distance"] > 0
    finally:
        db.close()


def test_routing_service_different_safety_weights():
    """Test the routing service with different safety weights."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        # Test with safety_weight = 0.0 (prioritize speed)
        result_fast = routing_service.find_safest_route(source, destination, safety_weight=0.0)
        # Test with safety_weight = 1.0 (prioritize safety)
        result_safe = routing_service.find_safest_route(source, destination, safety_weight=1.0)
        # Test with safety_weight = 0.5 (balanced)
        result_balanced = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        for result in (result_fast, result_safe, result_balanced):
            assert_valid_route_result(result)
            assert len(result["safest_route"]) >= 2
            assert len(result["fastest_route"]) >= 2

        # The safety_weight is accepted by the service; on a linear graph the
        # fastest and safest routes coincide, but both must remain valid.
        # Scores are data-driven from the nearby RoadSegmentRisk records (0.65).
        assert abs(result_fast["safest_safety_score"] - 0.65) < 0.001
        assert abs(result_safe["safest_safety_score"] - 0.65) < 0.001
        assert abs(result_fast["fastest_safety_score"] - 0.65) < 0.001
        assert abs(result_safe["fastest_safety_score"] - 0.65) < 0.001
    finally:
        db.close()


if __name__ == "__main__":
    test_routing_service_with_mock_data()
    test_routing_service_different_safety_weights()
    print("All tests passed!")
