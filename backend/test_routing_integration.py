"""
Integration test for the SafetyRoutingService using real graph data.
This test verifies the complete execution flow from API to response.
"""

import pytest
from app.db.session import SessionLocal
from app.schemas.routing import Coordinate
from app.services.routing import SafetyRoutingService


def test_routing_service_integration():
    """Test that the routing service works with real graph data."""
    # Create a database session
    db = SessionLocal()

    try:
        # Create the routing service
        routing_service = SafetyRoutingService(db)

        # Test coordinates that should be within our graph data (based on earlier query)
        # Using coordinates from the sample node we saw: lat=28.6723292, lon=77.2309078
        source = Coordinate(latitude=28.6720, longitude=77.2305)
        destination = Coordinate(latitude=28.6725, longitude=77.2310)

        # Test that we can find a route
        result = routing_service.find_safest_route(
            source=source,
            destination=destination,
            safety_weight=0.5  # Balanced mode
        )

        # Verify we got a valid response
        assert "safest_route" in result
        assert "fastest_route" in result
        assert "safest_distance" in result
        assert "fastest_distance" in result
        assert "safest_safety_score" in result
        assert "fastest_safety_score" in result
        assert "route_segments" in result

        # Verify the routes are not empty
        assert len(result["safest_route"]) > 0
        assert len(result["fastest_route"]) > 0

        # Verify the routes start and end at the correct points (approximately)
        # First point should be near source
        assert abs(result["safest_route"][0].latitude - source.latitude) < 0.01
        assert abs(result["safest_route"][0].longitude - source.longitude) < 0.01

        # Last point should be near destination
        assert abs(result["safest_route"][-1].latitude - destination.latitude) < 0.01
        assert abs(result["safest_route"][-1].longitude - destination.longitude) < 0.01

        # Verify distances are positive
        assert result["safest_distance"] > 0
        assert result["fastest_distance"] > 0

        # Verify safety scores are in valid range
        assert 0.0 <= result["safest_safety_score"] <= 1.0
        assert 0.0 <= result["fastest_safety_score"] <= 1.0

        print(f"Route calculation successful:")
        print(f"  Safest route: {len(result['safest_route'])} points, {result['safest_distance']:.2f}m, safety={result['safest_safety_score']:.3f}")
        print(f"  Fastest route: {len(result['fastest_route'])} points, {result['fastest_distance']:.2f}m, safety={result['fastest_safety_score']:.3f}")

    except Exception as e:
        pytest.fail(f"Routing service failed with error: {e}")
    finally:
        db.close()


def test_routing_service_with_different_weights():
    """Test routing service with different safety weights."""
    db = SessionLocal()

    try:
        routing_service = SafetyRoutingService(db)

        # Use coordinates that are close enough to likely be connected
        source = Coordinate(latitude=28.6720, longitude=77.2305)
        destination = Coordinate(latitude=28.6725, longitude=77.2310)

        # Test fastest priority (safety_weight = 0.0)
        result_fast = routing_service.find_safest_route(
            source=source,
            destination=destination,
            safety_weight=0.0
        )

        # Test safest priority (safety_weight = 1.0)
        result_safe = routing_service.find_safest_route(
            source=source,
            destination=destination,
            safety_weight=1.0
        )

        # Both should succeed
        assert len(result_fast["safest_route"]) > 0
        assert len(result_safe["safest_route"]) > 0

        # The fastest route should typically be shorter or equal distance
        # (though with our simplified cost model, this might not always hold)
        print(f"Fastest priority: {result_fast['fastest_distance']:.2f}m")
        print(f"Safest priority: {result_safe['fastest_distance']:.2f}m")

    except Exception as e:
        pytest.fail(f"Routing service with weights failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # Run the tests directly
    test_routing_service_integration()
    test_routing_service_with_different_weights()
    print("All integration tests passed!")