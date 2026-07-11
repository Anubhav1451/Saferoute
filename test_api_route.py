from app.db.session import SessionLocal
from app.services.routing import SafetyRoutingService
from app.schemas.routing import Coordinate

def test_api_route():
    db = SessionLocal()
    try:
        routing_service = SafetyRoutingService(db)
        source = Coordinate(latitude=28.6315, longitude=77.2167)
        destination = Coordinate(latitude=29.9660, longitude=77.5540)

        print('Calling routing service via API-like method...')
        result = routing_service.find_safest_route(source, destination)

        print(f'Safest route nodes: {len(result["safest_route"])}')
        print(f'Fastest route nodes: {len(result["fastest_route"])}')
        print(f'Safest distance: {result["safest_distance"]}')
        print(f'Fastest distance: {result["fastest_distance"]}')
        print(f'Safest safety score: {result["safest_safety_score"]}')
        print(f'Fastest safety score: {result["fastest_safety_score"]}')

    except Exception as e:
        print(f'Error: {e}')
        raise
    finally:
        db.close()

if __name__ == '__main__':
    test_api_route()