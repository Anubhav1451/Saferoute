#!/usr/bin/env python
"""
Quick check to see if the safest and fastest routes are identical.

Uses the shared in-memory GIS graph so it exercises the current production
implementation (SafetyRoutingService.find_safest_route) without mocking
any removed methods.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.routing import SafetyRoutingService
from routing_test_helpers import create_graph_session, default_source, default_destination


def compare_routes():
    db = create_graph_session()
    try:
        routing_service = SafetyRoutingService(db)

        source = default_source()
        destination = default_destination()

        result = routing_service.find_safest_route(source, destination, safety_weight=0.5)

        safest = result['safest_route']
        fastest = result['fastest_route']

        print(f"Safest length: {len(safest)}")
        print(f"Fastest length: {len(fastest)}")

        if len(safest) != len(fastest):
            print("Lengths differ")
            return

        for i in range(len(safest)):
            if safest[i].latitude != fastest[i].latitude or safest[i].longitude != fastest[i].longitude:
                print(f"Difference at index {i}: safest=({safest[i].latitude}, {safest[i].longitude}), "
                      f"fastest=({fastest[i].latitude}, {fastest[i].longitude})")
                return

        print("Routes are identical")
    finally:
        db.close()


if __name__ == '__main__':
    compare_routes()
