#!/usr/bin/env python
"""
Test the routing integration with the current GIS-based implementation.
"""
import sys
import os

# Add the backend directory to the path so `app` and the routing test
# helpers can be imported regardless of CWD.
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.routing import SafetyRoutingService
from routing_test_helpers import (
    create_graph_session,
    default_source,
    default_destination,
    assert_valid_route_result,
)


def test_routing_service_basic_functionality():
    """Test that the routing service works against a real in-memory graph."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        # Basic assertions on the current production response contract
        assert_valid_route_result(result)
        assert len(result["safest_route"]) >= 2
        assert len(result["fastest_route"]) >= 2
        assert 0.0 <= result["safest_safety_score"] <= 1.0
        assert 0.0 <= result["fastest_safety_score"] <= 1.0
        assert result["safest_distance"] >= 0
        assert result["fastest_distance"] >= 0
        assert isinstance(result["route_segments"], list)
        assert len(result["route_segments"]) >= 1
    finally:
        db.close()


def test_routing_service_safety_weight_extremes():
    """Test routing service with extreme safety weights (0.0 and 1.0)."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        # Test with safety_weight = 0.0 (prioritize speed)
        result_fast = routing_service.find_safest_route(source, destination, safety_weight=0.0)
        # Test with safety_weight = 1.0 (prioritize safety)
        result_safe = routing_service.find_safest_route(source, destination, safety_weight=1.0)

        # Both should return valid routes
        assert_valid_route_result(result_fast)
        assert_valid_route_result(result_safe)
        assert len(result_fast["safest_route"]) >= 2
        assert len(result_safe["safest_route"]) >= 2
        assert 0.0 <= result_fast["safest_safety_score"] <= 1.0
        assert 0.0 <= result_safe["safest_safety_score"] <= 1.0
    finally:
        db.close()


if __name__ == "__main__":
    test_routing_service_basic_functionality()
    test_routing_service_safety_weight_extremes()
    print("All tests passed!")
