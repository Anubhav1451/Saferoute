# This replicates exactly what happens in the API endpoint
from app.db.session import SessionLocal
from app.services.routing import SafetyRoutingService
from app.schemas.routing import Coordinate
from app.api.responses import success_response

def test_api_exact():
    # This is exactly what the API endpoint does
    db = SessionLocal()
    try:
        routing_service = SafetyRoutingService(db)
        source = Coordinate(latitude=28.6315, longitude=77.2167)
        destination = Coordinate(latitude=29.9660, longitude=77.5540)
        
        result = routing_service.find_safest_route(
            source=source,
            destination=destination,
            safety_weight=0.7  # default from API
        )
        
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
        
        print("Response from API-like call:")
        print(f"  Success: {response['success']}")
        print(f"  Message: {response['message']}")
        print(f"  Safest safety score: {response['data']['safest_safety_score']}")
        print(f"  Fastest safety score: {response['data']['fastest_safety_score']}")
        print(f"  Safest nodes: {len(response['data']['safest_route'])}")
        print(f"  Fastest nodes: {len(response['data']['fastest_route'])}")
        
        return response
    finally:
        db.close()

if __name__ == "__main__":
    test_api_exact()
