import os
import sys
sys.path.insert(0, '.')

def load_env_file(env_path='.env'):
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('\"\'')
                os.environ[key] = value

load_env_file()

from app.services.routing import SafetyRoutingService
# Mock db session (not used in _map_match_segment)
class MockDb:
    pass

service = SafetyRoutingService(db=MockDb())
print("MAPBOX_TOKEN from service:", service.mapbox_token)
if not service.mapbox_token:
    print("ERROR: MAPBOX_TOKEN is empty")
else:
    # Test map matching with a simple coordinate pair (maybe not on road)
    from app.schemas.routing import Coordinate
    start = Coordinate(latitude=38.89767, longitude=-77.03653)
    end = Coordinate(latitude=38.88993, longitude=-77.00905)
    result = service._map_match_segment(start, end)
    print("Map match result:", result)
    if result is None:
        print("Map matching returned None (could be token issue or no segment)")
    else:
        print("Map matching succeeded with", len(result), "points")