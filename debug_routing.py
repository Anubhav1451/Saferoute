#!/usr/bin/env python
"""
Test script to debug routing graph after loading real safety nodes.
"""
import sys
import os
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.routing import SafetyRoutingService
from app.db.session import SessionLocal
from app.schemas.routing import Coordinate

def main():
    db = SessionLocal()
    try:
        routing_service = SafetyRoutingService(db)
        source = Coordinate(latitude=28.6315, longitude=77.2167)  # Delhi
        destination = Coordinate(latitude=29.9660, longitude=77.5540)  # Saharanpur
        print(f"Testing route from Delhi ({source.latitude}, {source.longitude}) to Saharanpur ({destination.latitude}, {destination.longitude})")
        result = routing_service.find_safest_route(source, destination)
        print("\n=== Results ===")
        print(f"Fastest route coordinates count: {len(result['fastest_route'])}")
        print(f"Safest route coordinates count: {len(result['safest_route'])}")
        print(f"Fastest distance: {result['fastest_distance']/1000:.2f} km")
        print(f"Safest distance: {result['safest_distance']/1000:.2f} km")
        print(f"Fastest safety score: {result['fastest_safety_score']:.3f}")
        print(f"Safest safety score: {result['safest_safety_score']:.3f}")
        # Check if routes differ
        def routes_equal(r1, r2, tol=0.0001):
            if len(r1) != len(r2):
                return False
            for c1, c2 in zip(r1, r2):
                if abs(c1['latitude'] - c2['latitude']) > tol or abs(c1['longitude'] - c2['longitude']) > tol:
                    return False
            return True
        if routes_equal(result['fastest_route'], result['safest_route']):
            print("\nRESULT: Fastest and safest routes are IDENTICAL")
        else:
            print("\nRESULT: Fastest and safest routes are DIFFERENT")
    finally:
        db.close()

if __name__ == "__main__":
    main()