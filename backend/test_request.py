import os
import requests

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
token = os.getenv('MAPBOX_TOKEN')
print('Token:', token[:20] + '...' if token else None)

coords = "-77.03653,38.89767;-77.00905,38.88993"
url = f"https://api.mapbox.com/matching/v5/mapbox/driving/{coords}.json"
params = {
    "access_token": token,
    "geometries": "geojson",
    "overview": "full",
    "steps": "true"
}
resp = requests.get(url, params=params, timeout=10)
print('Status:', resp.status_code)
print('Response:', resp.text)