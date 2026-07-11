#!/usr/bin/env python
"""
Quick check to see if the routes are identical.
"""
import sys
import os
from unittest.mock import Mock, patch

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate
from sqlalchemy.orm import Session

def compare_routes():
    db = Mock(spec=Session)
    routing_service = SafetyRoutingService(db)

    source = Coordinate(latitude=28.6315, longitude=77.2167)
    destination = Coordinate(latitude=29.9660, longitude=77.5540)

    def mock_get_nearby_safety_data(lat, lon, radius_meters=None):
        return ([], [], [])

    with patch('app.services.routing.SafetyRoutingService.get_nearby_safety_data') as mock_get_data:
        mock_get_data.side_effect = mock_get_nearby_safety_data
        with patch('app.services.routing.SafetyRoutingService.calculate_ai_safety_score') as mock_ai:
            mock_ai.return_value = -1.0

            result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

            safest = result['safest_route']
            fastest = result['fastest_route']

            print(f"Safest length: {len(safest)}")
            print(f"Fastest length: {len(fastest)}")

            if len(safest) != len(fastest):
                print("Lengths differ")
                return

            for i in range(len(safest)):
                if safest[i]['latitude'] != fastest[i]['latitude'] or safest[i]['longitude'] != fastest[i]['longitude']:
                    print(f"Difference at index {i}: safest={safest[i]}, fastest={fastest[i]}")
                    return

            print("Routes are identical")

if __name__ == '__main__':
    compare_routes()