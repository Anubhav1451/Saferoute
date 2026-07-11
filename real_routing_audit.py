#!/usr/bin/env python
"""
Real routing audit - inspect actual API output for Delhi -> Saharanpur
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.routing import SafetyRoutingService
from app.db.models import SafetyNode
from app.schemas.routing import Coordinate
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_real_routing():
    # Create a database session (using SQLite for simplicity if needed)
    # First, let's see what database configuration exists
    try:
        from app.core.config import settings
        # Use the existing database connection
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        print(f"Connected to database: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"Could not connect to configured database: {e}")
        print("Creating a mock database session for testing...")
        # Create a mock session
        db = None

    # Create the routing service
    routing_service = SafetyRoutingService(db)

    # Test coordinates: Delhi to Saharanpur
    source = Coordinate(latitude=28.6315, longitude=77.2167)  # Delhi area
    destination = Coordinate(latitude=29.9660, longitude=77.5540)  # Saharanpur area

    print(f"Testing route from Delhi ({source.latitude}, {source.longitude}) to Saharanpur ({destination.latitude}, {destination.longitude})")

    # Get safety node count and coverage
    if db:
        safety_node_count = db.query(SafetyNode).count()
        print(f"Total SafetyNode records in database: {safety_node_count}")

        if safety_node_count > 0:
            # Get geographic bounds of safety nodes
            from sqlalchemy import func
            result = db.query(
                func.min(SafetyNode.latitude).label('min_lat'),
                func.max(SafetyNode.latitude).label('max_lat'),
                func.min(SafetyNode.longitude).label('min_lon'),
                func.max(SafetyNode.longitude).label('max_lon')
            ).first()

            print(f"Safety nodes cover geographic area:")
            print(f"  Latitude: {result.min_lat} to {result.max_lat}")
            print(f"  Longitude: {result.min_lon} to {result.max_lon}")
            print(f"  Source point: ({source.latitude}, {source.longitude})")
            print(f"  Dest point: ({destination.latitude}, {destination.longitude})")

            # Check if source and destination are within the safety node coverage area
            lat_in_range = result.min_lat <= source.latitude <= result.max_lat and result.min_lat <= destination.latitude <= result.max_lat
            lon_in_range = result.min_lon <= source.longitude <= result.max_lon and result.min_lon <= destination.longitude <= result.max_lon

            print(f"Source within safety node area: {lat_in_range}")
            print(f"Destination within safety node area: {lon_in_range}")
        else:
            print("No safety nodes found in database")
    else:
        safety_node_count = 0
        print("Using mock service - no database connection")

    # Run the routing function
    print("\nRunning routing algorithm...")
    try:
        result = routing_service.find_safest_route(source, destination)

        print("\n=== ROUTING RESULTS ===")

        # Extract route information
        safest_route = result['safest_route']
        fastest_route = result['fastest_route']
        safest_distance = result['safest_distance']
        fastest_distance = result['fastest_distance']
        safest_safety_score = result['safest_safety_score']
        fastest_safety_score = result['fastest_safety_score']
        route_segments = result['route_segments']

        print(f"1. Fastest path coordinate count: {len(fastest_route)}")
        print(f"2. Safest path coordinate count: {len(safest_route)}")
        print(f"3. Fastest total distance: {fastest_distance/1000:.2f} km")
        print(f"4. Safest total distance: {safest_distance/1000:.2f} km")
        print(f"5. Fastest safety score: {fastest_safety_score:.3f}")
        print(f"6. Safest safety score: {safest_safety_score:.3f}")

        # Check if routes are visually identical (same coordinates)
        if len(fastest_route) == len(safest_route):
            # Compare coordinates
            identical = True
            for i in range(len(fastest_route)):
                f_coord = fastest_route[i]
                s_coord = safest_route[i]
                if abs(f_coord['latitude'] - s_coord['latitude']) > 0.0001 or abs(f_coord['longitude'] - s_coord['longitude']) > 0.0001:
                    identical = False
                    break

            if identical:
                print("7. Routes are IDENTICAL (same coordinates)")
                print("   A) YES - Both routes are using the exact same node sequence")
            else:
                print("7. Routes are DIFFERENT")
                print("   A) NO - Routes have different coordinate sequences")
        else:
            print("7. Routes have different lengths")
            print("   A) NO - Routes have different coordinate sequence lengths")

        # Additional analysis
        print(f"\n=== ADDITIONAL ANALYSIS ===")
        print(f"B) SafetyNode records exist: {safety_node_count}")

        if db and safety_node_count > 0:
            print(f"C) Safety node coverage area calculated above")

            # Check if we have enough nodes for meaningful routing
            # Get all nodes to see distribution
            nodes = db.query(SafetyNode).limit(10).all()
            print(f"D) Sample safety nodes (showing first {min(10, len(nodes))}):")
            for node in nodes:
                print(f"    Node {node.id}: ({node.latitude}, {node.longitude}) - safety_score: {node.safety_score}")

            # The key question: does the graph contain enough alternate nodes?
            # For route divergence, we need multiple paths between source and destination
            # This depends on having safety nodes positioned to create alternative routes

            # Let's check the A* path node counts (these are the safety nodes + source/dest used in pathfinding)
            # We don't have direct access to these from the result, but we can infer...
            print(f"   To determine if graph has enough alternate nodes, we'd need to see the internal A* paths.")
            print(f"   However, if safety nodes are sparse or not positioned between source/dest,")
            print(f"   the A* algorithm may have no choice but to use the same node sequence.")
        else:
            print("C) No safety node data available for geographic analysis")
            print("D) Cannot assess alternate nodes without safety node data")

        # Propose fix if needed
        if len(fastest_route) == len(safest_route) and all(
            abs(fastest_route[i]['latitude'] - safest_route[i]['latitude']) < 0.0001 and
            abs(fastest_route[i]['longitude'] - safest_route[i]['longitude']) < 0.0001
            for i in range(len(fastest_route))
        ):
            print("\n=== PROPOSED FIX ANALYSIS ===")
            print("Routes are identical - likely due to:")
            print("1. Insufficient safety node density between source and destination")
            print("2. Safety node scores too uniform (no meaningful safety differentiation)")
            print("3. Edge threshold too low to create meaningful graph connections")
            print("4. Safety weight factor too low to influence path selection")
            print("\nSmallest fix proposals (in order of preference):")
            print("A) Increase safety node density in the routing area (add more SafetyNode records)")
            print("B) Increase edge_threshold_m to connect more nodes into the routing graph")
            print("C) Increase safety influence factor (alpha) in safest path cost calculation")
            print("D) Ensure safety scores have meaningful variation (not all 0.5 or all 1.0)")
        else:
            print("\nRoutes show differentiation - system appears to be working correctly.")

    except Exception as e:
        print(f"Error running routing algorithm: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    test_real_routing()