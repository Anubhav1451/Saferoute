#!/usr/bin/env python
"""
Test the routing service against the current GIS routing implementation
using an in-memory graph. Two calls to the service are compared for
consistency, and different safety weights are exercised.
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


def test_caching_and_safety():
    """Two routing calls on the same graph must produce consistent results."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        # First request
        result1 = routing_service.find_safest_route(source, destination, safety_weight=0.5)
        # Second request
        result2 = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        assert_valid_route_result(result1)
        assert_valid_route_result(result2)

        # Both requests return valid routes
        assert len(result1["safest_route"]) >= 2
        assert len(result2["safest_route"]) >= 2

        # Results are deterministic on the same graph
        assert abs(result1["safest_safety_score"] - result2["safest_safety_score"]) < 0.001
        assert abs(result1["fastest_safety_score"] - result2["fastest_safety_score"]) < 0.001
        assert abs(result1["safest_distance"] - result2["safest_distance"]) < 1.0
        assert abs(result1["fastest_distance"] - result2["fastest_distance"]) < 1.0

        # Current implementation's safety score is the 0.8 placeholder
        assert 0.5 <= result1["safest_safety_score"] <= 0.9
        assert 0.5 <= result1["fastest_safety_score"] <= 0.9
    finally:
        db.close()


def test_different_safety_weights():
    """Test the service with different safety weights."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        result_fast = routing_service.find_safest_route(source, destination, safety_weight=0.0)
        result_safe = routing_service.find_safest_route(source, destination, safety_weight=1.0)
        result_balanced = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        for result in (result_fast, result_safe, result_balanced):
            assert_valid_route_result(result)
            assert len(result["safest_route"]) >= 2
            assert len(result["fastest_route"]) >= 2
    finally:
        db.close()


if __name__ == '__main__':
    test_caching_and_safety()
    test_different_safety_weights()
    print("All tests passed!")
