"""Test the corridor-preserving Mapbox strategy."""
import sys, os
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, os.getcwd())

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

payload = {
    "source": {"latitude": 28.6139, "longitude": 77.2090},
    "destination": {"latitude": 29.9679, "longitude": 77.5450}
}

print("=" * 60, flush=True)
print("ROUTE: Delhi (28.6139, 77.2090) -> Saharanpur (29.9679, 77.5450)", flush=True)
print("=" * 60, flush=True)

resp = client.post("/api/v1/calculate", json=payload)
print(f"\nHTTP Status: {resp.status_code}", flush=True)
data = resp.json()
print(f"API success: {data.get('success')}", flush=True)

if data.get("data"):
    d = data["data"]
    print(f"\n=== Final API Response ===", flush=True)
    print(f"  safest_score:  {d.get('safest_safety_score', 'N/A')}", flush=True)
    print(f"  fastest_score: {d.get('fastest_safety_score', 'N/A')}", flush=True)
    print(f"  safest_dist:   {d.get('safest_distance', 'N/A'):.2f}m", flush=True)
    print(f"  fastest_dist:  {d.get('fastest_distance', 'N/A'):.2f}m", flush=True)
    safe_pts = len(d.get('safest_route', []))
    fast_pts = len(d.get('fastest_route', []))
    print(f"  safest pts:    {safe_pts}", flush=True)
    print(f"  fastest pts:   {fast_pts}", flush=True)
    print(f"\n  Routes DIFFERENT after Mapbox: {safe_pts != fast_pts or d.get('safest_distance') != d.get('fastest_distance')}", flush=True)

print("\nDONE", flush=True)
