#!/usr/bin/env python
"""
Test the routing service with given coordinates against the current GIS
routing implementation using an in-memory graph.
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


def test_routing_with_mock_data():
    """Test the routing service on an in-memory graph (no DB dependency)."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        assert_valid_route_result(result)
        assert len(result["safest_route"]) >= 2
        assert len(result["fastest_route"]) >= 2

        # Every returned coordinate is a real Coordinate object with numeric fields
        for coord in result["safest_route"]:
            assert isinstance(coord.latitude, float)
            assert isinstance(coord.longitude, float)
    finally:
        db.close()


if __name__ == '__main__':
    test_routing_with_mock_data()
