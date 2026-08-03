#!/usr/bin/env python
"""
Test the routing service with a small 3-node linear graph (A -> B -> C)
against the current GIS routing implementation.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from routing_test_helpers import (
    create_graph_session,
    SOURCE_LAT, SOURCE_LON,
    MID_LAT, MID_LON,
    DEST_LAT, DEST_LON,
    assert_valid_route_result,
)


def test_routing_service_with_mock_graph():
    """A 3-node linear graph produces a 3-point route from A to C."""
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)

        # Source near node A, destination near node C
        from app.schemas.routing import Coordinate
        source = Coordinate(latitude=SOURCE_LAT, longitude=SOURCE_LON)
        destination = Coordinate(latitude=DEST_LAT, longitude=DEST_LON)

        result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        assert_valid_route_result(result)
        assert len(result["safest_route"]) >= 2
        assert len(result["fastest_route"]) >= 2
        assert result["safest_distance"] >= 0
        assert result["fastest_distance"] >= 0

        # The graph is a single path A->B->C, so both weight modes find the
        # same 3-point route through the middle node.
        safest = result["safest_route"]
        assert len(safest) == 3
        assert abs(safest[0].latitude - SOURCE_LAT) < 0.01
        assert abs(safest[1].latitude - MID_LAT) < 0.01
        assert abs(safest[2].latitude - DEST_LAT) < 0.01
    finally:
        db.close()


if __name__ == '__main__':
    test_routing_service_with_mock_graph()
