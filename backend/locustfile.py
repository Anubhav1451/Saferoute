import random
from datetime import datetime

from locust import HttpUser, between, task


class SafeRouteUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        # When a user starts, check the health endpoint
        self.client.get("/health")

    @task(3)
    def calculate_route(self):
        # Generate random coordinates within a reasonable bounding box (Delhi area)
        lat_min, lat_max = 28.4, 28.9
        lon_min, lon_max = 77.0, 77.5

        start_lat = random.uniform(lat_min, lat_max)
        start_lon = random.uniform(lon_min, lon_max)
        end_lat = random.uniform(lat_min, lat_max)
        end_lon = random.uniform(lon_min, lon_max)

        # Ensure start and end are not too close (at least ~100m apart)
        # Simple approximation: 0.001 degrees ~ 111 meters at equator
        while abs(start_lat - end_lat) < 0.001 and abs(start_lon - end_lon) < 0.001:
            end_lat = random.uniform(lat_min, lat_max)
            end_lon = random.uniform(lon_min, lon_max)

        # Map route preference to safety_weight: safest -> 0.9, balanced -> 0.5, fastest -> 0.1
        preference_to_weight = {
            "safest": 0.9,
            "balanced": 0.5,
            "fastest": 0.1
        }
        preference = random.choice(["safest", "balanced", "fastest"])
        safety_weight = preference_to_weight[preference]

        payload = {
            "source": {
                "latitude": start_lat,
                "longitude": start_lon
            },
            "destination": {
                "latitude": end_lat,
                "longitude": end_lon
            },
            "safety_weight": safety_weight
        }

        with self.client.post("/api/v1/calculate", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}: {response.text}")

    @task(1)
    def trigger_sos(self):
        payload = {
            "latitude": random.uniform(28.4, 28.9),
            "longitude": random.uniform(77.0, 77.5),
            "emergency_type": random.choice(["medical", "police", "fire"]),
            "description": "Emergency situation reported via load test",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        with self.client.post("/api/v1/sos/trigger", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}: {response.text}")

    @task(1)
    def health_check(self):
        self.client.get("/health")