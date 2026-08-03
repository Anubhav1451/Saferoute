# Replicates the API endpoint flow: build the routing service, call
# find_safest_route, wrap the result in the standard success_response,
# and assert on the exact response shape the API returns.
#
# Uses the current GIS routing implementation (A* over the graph).
# The old get_nearby_safety_data_bounding_box / calculate_ai_safety_score /
# calculate_route_analytics methods no longer exist and are not mocked here.
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from app.api.responses import success_response
from routing_test_helpers import (
    create_graph_session,
    default_source,
    default_destination,
    assert_valid_route_result,
)


def test_api_exact():
    # This is exactly what the API endpoint does
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)
        source = default_source()
        destination = default_destination()

        result = routing_service.find_safest_route(
            source=source,
            destination=destination,
            safety_weight=0.7  # default from API
        )

        # Validate the underlying production routing contract first
        assert_valid_route_result(result)

        # This is exactly what the API returns
        response = success_response(
            data={
                "safest_route": result["safest_route"],
                "fastest_route": result["fastest_route"],
                "safest_distance": result["safest_distance"],
                "fastest_distance": result["fastest_distance"],
                "safest_safety_score": result["safest_safety_score"],
                "fastest_safety_score": result["fastest_safety_score"],
                "route_segments": result["route_segments"]
            },
            message="Route calculation completed successfully"
        )

        assert response["success"] is True
        assert response["message"] == "Route calculation completed successfully"
        assert "safest_route" in response["data"]
        assert "fastest_route" in response["data"]
        assert "safest_safety_score" in response["data"]
        assert "fastest_safety_score" in response["data"]
        assert "safest_distance" in response["data"]
        assert "fastest_distance" in response["data"]
        assert "route_segments" in response["data"]
        assert len(response["data"]["safest_route"]) >= 2
        assert len(response["data"]["fastest_route"]) >= 2

        return response
    finally:
        db.close()


if __name__ == "__main__":
    test_api_exact()
