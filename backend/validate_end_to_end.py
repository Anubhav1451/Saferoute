#!/usr/bin/env python3
"""
Script to validate the end-to-end functionality of the SafeRoute AI system
using real data from the loaded OSM extract and testing the API.
"""
import os
import sys
import time

import requests

# Add the backend directory to the path to import modules if needed
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.session import SessionLocal
from sqlalchemy import text



def get_graph_bounding_box():
    """Get the bounding box of the graph from the database."""
    db = SessionLocal()
    try:
        # Get min/max latitude and longitude from graph_nodes
        result = db.execute(text("""
            SELECT
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon
            FROM graph_nodes
        """)).fetchone()
        if result:
            return {
                'min_lat': float(result[0]),
                'max_lat': float(result[1]),
                'min_lon': float(result[2]),
                'max_lon': float(result[3])
            }
    except Exception as e:
        print(f"Error getting bounding box: {e}")
    finally:
        db.close()
    return None

def is_point_in_bbox(lat, lon, bbox, buffer=0.1):
    """Check if a point is within the bounding box (with optional buffer)."""
    if not bbox:
        return False
    return (bbox['min_lat'] - buffer <= lat <= bbox['max_lat'] + buffer) and \
           (bbox['min_lon'] - buffer <= lon <= bbox['max_lon'] + buffer)

def make_request(method, endpoint, **kwargs):
    """Make an HTTP request and return the response and time taken."""
    url = f"http://localhost:8000{endpoint}"
    start_time = time.time()
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, **kwargs)
        elif method.upper() == 'POST':
            resp = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        elapsed = time.time() - start_time
        return resp, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        # Return a mock response with error
        class MockResponse:
            def __init__(self, error_msg):
                self.status_code = 500
                self.text = error_msg
            def json(self):
                return {"error": self.text}
        return MockResponse(str(e)), elapsed

def test_route(route_name, source_lat, source_lng, dest_lat, dest_lng, safety_weight=0.5):
    """Test a route between two points."""
    print(f"Testing route: {route_name}")

    # Prepare the request payload
    payload = {
        "source": {"latitude": source_lat, "longitude": source_lng},
        "destination": {"latitude": dest_lat, "longitude": dest_lng},
        "safety_weight": safety_weight
    }

    # First request (might be slower due to cache warm-up)
    resp1, time1 = make_request('POST', '/api/v1/calculate', json=payload)

    # Second request (should be faster if caching works)
    resp2, time2 = make_request('POST', '/api/v1/calculate', json=payload)

    # Parse responses
    try:
        data1 = resp1.json() if resp1.status_code == 200 else None
        data2 = resp2.json() if resp2.status_code == 200 else None
    except:
        data1 = None
        data2 = None

    result = {
        'route_name': route_name,
        'source': (source_lat, source_lng),
        'destination': (dest_lat, dest_lng),
        'status_code_1': resp1.status_code,
        'status_code_2': resp2.status_code,
        'time_first_request': time1,
        'time_second_request': time2,
        'response_data_1': data1,
        'response_data_2': data2,
        'success': resp1.status_code == 200 and resp2.status_code == 200
    }
    return result

def test_safety_score(lat, lon):
    """Test the safety score endpoint for a given point."""
    params = {'latitude': lat, 'longitude': lon}
    resp, elapsed = make_request('GET', '/api/v1/ai/safety-score', params=params)
    try:
        data = resp.json() if resp.status_code == 200 else None
    except:
        data = None
    return {
        'status_code': resp.status_code,
        'time': elapsed,
        'data': data
    }

def main():
    print("Starting end-to-end validation...")

    # Get the bounding box of the loaded graph
    bbox = get_graph_bounding_box()
    if bbox:
        print(f"Graph bounding box: {bbox}")
    else:
        print("WARNING: Could not determine graph bounding box.")

    # Define the routes to test (using real city coordinates)
    routes = [
        # Delhi to Gurgaon (both in the northern India OSM extract)
        ("Delhi to Gurgaon", 28.6139, 77.2090, 28.4595, 77.0266),
        # Bangalore to Whitefield (both in Karnataka, might not be in the north India extract)
        ("Bangalore to Whitefield", 12.9716, 77.5946, 12.9698, 77.7500),
        # Mumbai to Navi Mumbai (both in Maharashtra, might not be in the extract)
        ("Mumbai to Navi Mumbai", 19.0760, 72.8777, 19.0330, 73.0297),
        # Patna to Gaya (both in Bihar, likely in the north India extract)
        ("Patna to Gaya", 25.5941, 85.1376, 24.7914, 85.0002)
    ]

    results = []

    for route_name, slat, slon, dlat, dlon in routes:
        # Check if points are in the bounding box
        in_bbox_start = is_point_in_bbox(slat, slon, bbox) if bbox else False
        in_bbox_end = is_point_in_bbox(dlat, dlon, bbox) if bbox else False

        print(f"  Start point ({slat}, {slon}) in bbox: {in_bbox_start}")
        print(f"  End point ({dlat}, {dlon}) in bbox: {in_bbox_end}")

        # Only attempt the route if both points are in the bounding box (or if we don't have bbox, assume we try)
        if bbox and not (in_bbox_start and in_bbox_end):
            print(f"  Skipping route {route_name} as points are outside the loaded map area.")
            result = {
                'route_name': route_name,
                'skipped': True,
                'reason': 'Points outside loaded map area',
                'start_in_bbox': in_bbox_start,
                'end_in_bbox': in_bbox_end
            }
        else:
            result = test_route(route_name, slat, slon, dlat, dlon)

        results.append(result)

        # Also test safety score for the start and end points
        print(f"  Testing safety score for start point...")
        start_score = test_safety_score(slat, slon)
        result['safety_score_start'] = start_score

        print(f"  Testing safety score for end point...")
        end_score = test_safety_score(dlat, dlon)
        result['safety_score_end'] = end_score

        # Small delay between requests to avoid overwhelming the server
        time.sleep(0.5)

    # Generate the report
    generate_report(results, bbox)

    print("Validation complete. Report generated.")
    return results

def generate_report(results, bbox):
    """Generate a markdown report of the validation results."""
    with open('END_TO_END_VALIDATION.md', 'w') as f:
        f.write("# End-to-End Validation Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Graph Bounding Box\n\n")
        if bbox:
            f.write(f"| Metric | Value |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Min Latitude | {bbox['min_lat']:.6f} |\n")
            f.write(f"| Max Latitude | {bbox['max_lat']:.6f} |\n")
            f.write(f"| Min Longitude | {bbox['min_lon']:.6f} |\n")
            f.write(f"| Max Longitude | {bbox['max_lon']:.6f} |\n\n")
        else:
            f.write("Could not determine bounding box from database.\n\n")

        f.write("## Route Test Results\n\n")
        f.write("| Route | Start In BBox | End In BBox | Status (1st) | Status (2nd) | Time (1st) (s) | Time (2nd) (s) | Success |\n")
        f.write("|-------|---------------|-------------|--------------|--------------|----------------|----------------|---------|\n")

        for r in results:
            if 'skipped' in r and r['skipped']:
                f.write(f"| {r['route_name']} | {r.get('start_in_bbox', 'N/A')} | {r.get('end_in_bbox', 'N/A')} | SKIPPED | SKIPPED | N/A | N/A | FAIL (Skipped: {r.get('reason', 'unknown')}) |\n")
            else:
                f.write(f"| {r['route_name']} | {r.get('start_in_bbox', 'N/A')} | {r.get('end_in_bbox', 'N/A')} | {r['status_code_1']} | {r['status_code_2']} | {r['time_first_request']:.3f} | {r['time_second_request']:.3f} | {'PASS' if r['success'] else 'FAIL'} |\n")

        f.write("\n## Detailed Response Analysis\n\n")

        for r in results:
            if 'skipped' in r and r['skipped']:
                continue
            f.write(f"### {r['route_name']}\n\n")
            f.write(f"- **First Request:** Status {r['status_code_1']}, Time {r['time_first_request']:.3f}s\n")
            f.write(f"- **Second Request:** Status {r['status_code_2']}, Time {r['time_second_request']:.3f}s\n")
            if r['response_data_1'] and 'data' in r['response_data_1']:
                data = r['response_data_1']['data']
                f.write(f"- **Route Data (1st req):**\n")
                safest_distance = data.get('safest_distance', 'N/A')
                if isinstance(safest_distance, (int, float)):
                    f.write(f"  - Safest Distance: {safest_distance:.2f} meters\n")
                else:
                    f.write(f"  - Safest Distance: {safest_distance}\n")
                fastest_distance = data.get('fastest_distance', 'N/A')
                if isinstance(fastest_distance, (int, float)):
                    f.write(f"  - Fastest Distance: {fastest_distance:.2f} meters\n")
                else:
                    f.write(f"  - Fastest Distance: {fastest_distance}\n")
                safest_safety_score = data.get('safest_safety_score', 'N/A')
                if isinstance(safest_safety_score, (int, float)):
                    f.write(f"  - Safest Safety Score: {safest_safety_score:.4f}\n")
                else:
                    f.write(f"  - Safest Safety Score: {safest_safety_score}\n")
                fastest_safety_score = data.get('fastest_safety_score', 'N/A')
                if isinstance(fastest_safety_score, (int, float)):
                    f.write(f"  - Fastest Safety Score: {fastest_safety_score:.4f}\n")
                else:
                    f.write(f"  - Fastest Safety Score: {fastest_safety_score}\n")
                f.write(f"  - Number of Route Segments: {len(data.get('route_segments', []))}\n")
            f.write(f"- **Safety Score (Start):** Status {r['safety_score_start']['status_code']}, Time {r['safety_score_start']['time']:.3f}s\n")
            if r['safety_score_start']['data']:
                ss_data = r['safety_score_start']['data']
                safety_score = ss_data.get('safety_score', 'N/A')
                if isinstance(safety_score, (int, float)):
                    f.write(f"  - Safety Score: {safety_score:.4f}\n")
                else:
                    f.write(f"  - Safety Score: {safety_score}\n")
                f.write(f"  - Method: {ss_data.get('method', 'N/A')}\n")
            f.write(f"- **Safety Score (End):** Status {r['safety_score_end']['status_code']}, Time {r['safety_score_end']['time']:.3f}s\n")
            if r['safety_score_end']['data']:
                ss_data = r['safety_score_end']['data']
                safety_score = ss_data.get('safety_score', 'N/A')
                if isinstance(safety_score, (int, float)):
                    f.write(f"  - Safety Score: {safety_score:.4f}\n")
                else:
                    f.write(f"  - Safety Score: {safety_score}\n")
                f.write(f"  - Method: {ss_data.get('method', 'N/A')}\n")
            f.write("\n")

        f.write("## Summary\n\n")
        total_routes = len(results)
        attempted = len([r for r in results if 'skipped' not in r or not r['skipped']])
        successful = len([r for r in results if 'skipped' not in r or not r['skipped'] and r.get('success', False)])

        f.write(f"- Total Routes Defined: {total_routes}\n")
        f.write(f"- Routes Attempted (within map bounds): {attempted}\n")
        f.write(f"- Routes Successful: {successful}\n")
        f.write(f"- Success Rate: {successful/attempted*100 if attempted>0 else 0:.1f}%\n\n")

        f.write("## Notes\n\n")
        f.write("1. The bounding box is derived from the `graph_nodes` table in the database.\n")
        f.write("2. A small buffer (0.1 degrees) is applied when checking if points are within the bbox.\n")
        f.write("3. Response times are measured in seconds and include network latency.\n")
        f.write("4. The second request benefits from caching (if implemented).\n")
        f.write("5. Safety scores are retrieved via the `/api/v1/ai/safety-score` endpoint.\n")
        f.write("6. 'N/A' indicates data not available due to error or non-200 response.\n")

if __name__ == "__main__":
    results = main()
    # Exit with non-zero if any of the attempted routes failed
    attempted_results = [r for r in results if 'skipped' not in r or not r['skipped']]
    if attempted_results:
        all_success = all(r.get('success', False) for r in attempted_results)
        sys.exit(0 if all_success else 1)
    else:
        print("No routes were attempted (all outside bounding box).")
        sys.exit(0)