#!/usr/bin/env python
"""
Real safety node ingestion from OpenStreetMap Overpass API.
Supports multiple Indian city regions: Delhi NCR, Mumbai-Pune,
Chandigarh-Dehradun, Lucknow-Kanpur.
"""
import sys
import os
import math
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import sessionmaker
from app.db.models import Base, SafetyNode, LightingLevel, CrowdDensity
from app.db.session import engine
import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_TIMEOUT = 60
LOCAL_RADIUS_METERS = 100.0

WEIGHTS = {
    'police': 0.30,
    'hospital': 0.15,
    'pharmacy': 0.15,
    'street_lamp': 0.20,
    'shop': 0.10,
    'cafe': 0.10,
}

# Regions covering all target city corridors
REGIONS = [
    {
        "name": "Delhi NCR + Saharanpur",
        "bbox": {"south": 28.4, "north": 30.2, "west": 76.8, "east": 78.0},
    },
    {
        "name": "Mumbai-Pune",
        "bbox": {"south": 18.3, "north": 19.3, "west": 72.7, "east": 74.1},
    },
    {
        "name": "Chandigarh-Dehradun",
        "bbox": {"south": 30.1, "north": 31.0, "west": 76.5, "east": 78.3},
    },
    {
        "name": "Lucknow-Kanpur",
        "bbox": {"south": 26.2, "north": 27.1, "west": 80.0, "east": 81.3},
    },
]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000
    return c * r


def build_overpass_query(bbox: Dict[str, float]) -> str:
    return f"""
[out:json][timeout:45];
(
  node["highway"="street_lamp"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
  node["amenity"="police"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
  node["amenity"="hospital"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
  node["amenity"="pharmacy"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
  node["amenity"="shop"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
  node["amenity"="cafe"]({bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']});
);
out center;
"""


def fetch_osm_elements(bbox: Dict[str, float], region_name: str) -> List[Dict[str, Any]]:
    query = build_overpass_query(bbox)
    print(f"  Fetching OSM data for {region_name}: {bbox}")
    headers = {'User-Agent': 'SafeRouteAI/2.0'}
    strategies = [
        ("POST", lambda: requests.post(OVERPASS_URL, data=query, headers=headers, timeout=OVERPASS_TIMEOUT)),
        ("GET", lambda: requests.get(OVERPASS_URL, params={'data': query}, headers=headers, timeout=OVERPASS_TIMEOUT)),
        ("GET (no timeout)", lambda: requests.get(OVERPASS_URL, params={'data': query.replace('[timeout:45]', '')}, headers=headers, timeout=OVERPASS_TIMEOUT)),
    ]
    for label, req_fn in strategies:
        try:
            response = req_fn()
            response.raise_for_status()
            data = response.json()
            elements = data.get('elements', [])
            print(f"  Fetched {len(elements)} OSM elements via {label}")
            return elements
        except Exception as e:
            print(f"  {label} failed: {e}")
    print(f"  All attempts failed for {region_name}")
    return []


def prepare_node_data(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes = []
    for el in elements:
        lat = el.get('lat')
        lon = el.get('lon')
        if lat is None or lon is None:
            center = el.get('center', {})
            lat = center.get('lat')
            lon = center.get('lon')
        if lat is None or lon is None:
            continue
        tags = el.get('tags', {})
        nodes.append({'lat': float(lat), 'lon': float(lon), 'tags': tags, 'osm_id': el.get('id'), 'osm_type': el.get('type')})
    return nodes


def compute_local_features(target_node: Dict[str, Any], all_nodes: List[Dict[str, Any]]) -> Tuple[int, int, int, int, int, int]:
    target_lat = target_node['lat']
    target_lon = target_node['lon']
    police = hospital = pharmacy = street_lamp = shop = cafe = 0
    for node in all_nodes:
        dist = haversine_distance(target_lat, target_lon, node['lat'], node['lon'])
        if dist > LOCAL_RADIUS_METERS:
            continue
        tags = node['tags']
        if tags.get('amenity') == 'police':
            police += 1
        elif tags.get('amenity') == 'hospital':
            hospital += 1
        elif tags.get('amenity') == 'pharmacy':
            pharmacy += 1
        elif tags.get('highway') == 'street_lamp':
            street_lamp += 1
        elif tags.get('amenity') == 'shop':
            shop += 1
        elif tags.get('amenity') == 'cafe':
            cafe += 1
    return police, hospital, pharmacy, street_lamp, shop, cafe


def compute_safety_score(counts: Tuple[int, int, int, int, int, int]) -> float:
    police, hospital, pharmacy, street_lamp, shop, cafe = counts
    raw_score = (
        police * WEIGHTS['police'] +
        (hospital + pharmacy) * WEIGHTS['hospital'] +
        street_lamp * WEIGHTS['street_lamp'] +
        (shop + cafe) * WEIGHTS['shop']
    )
    return max(0.0, min(raw_score, 1.0))


def compute_lighting_level(street_lamp_count: int) -> LightingLevel:
    if street_lamp_count == 0:
        return LightingLevel.LOW
    elif street_lamp_count <= 3:
        return LightingLevel.MEDIUM
    else:
        return LightingLevel.HIGH


def compute_crowd_density(shop_count: int, cafe_count: int) -> CrowdDensity:
    total_commercial = shop_count + cafe_count
    if total_commercial == 0:
        return CrowdDensity.SPARSE
    elif total_commercial <= 3:
        return CrowdDensity.NORMAL
    else:
        return CrowdDensity.DENSE


def print_statistics(session):
    total = session.query(SafetyNode).count()
    if total == 0:
        print("No safety nodes found!")
        return
    min_score = session.query(SafetyNode.safety_score).order_by(SafetyNode.safety_score.asc()).first()[0]
    max_score = session.query(SafetyNode.safety_score).order_by(SafetyNode.safety_score.desc()).first()[0]
    min_lat = session.query(SafetyNode.latitude).order_by(SafetyNode.latitude.asc()).first()[0]
    max_lat = session.query(SafetyNode.latitude).order_by(SafetyNode.latitude.desc()).first()[0]
    min_lon = session.query(SafetyNode.longitude).order_by(SafetyNode.longitude.asc()).first()[0]
    max_lon = session.query(SafetyNode.longitude).order_by(SafetyNode.longitude.desc()).first()[0]
    print("\n=== Safety Node Statistics ===")
    print(f"Total nodes inserted: {total}")
    print(f"Safety score range: {min_score:.3f} - {max_score:.3f}")
    print(f"Geographic bounds:")
    print(f"  Latitude: {min_lat:.6f} to {max_lat:.6f}")
    print(f"  Longitude: {min_lon:.6f} to {max_lon:.6f}")


def test_route(db_session, name: str, src_lat: float, src_lon: float, dst_lat: float, dst_lon: float) -> dict:
    print(f"\n  Testing route: {name} ({src_lat}, {src_lon}) -> ({dst_lat}, {dst_lon})")
    from app.services.routing import SafetyRoutingService
    from app.schemas.routing import Coordinate
    svc = SafetyRoutingService(db_session)
    src = Coordinate(latitude=src_lat, longitude=src_lon)
    dst = Coordinate(latitude=dst_lat, longitude=dst_lon)
    t0 = time.time()
    result = svc.find_safest_route(src, dst)
    elapsed = time.time() - t0
    safe_pts = len(result.get('safest_route', []))
    fast_pts = len(result.get('fastest_route', []))
    safe_dist = result.get('safest_distance', 0)
    fast_dist = result.get('fastest_distance', 0)
    safe_score = result.get('safest_safety_score', 0)
    fast_score = result.get('fastest_safety_score', 0)
    diff = safe_pts != fast_pts
    print(f"    time={elapsed:.2f}s  safest_pts={safe_pts}  fastest_pts={fast_pts}")
    print(f"    safest_score={safe_score:.4f}  fastest_score={fast_score:.4f}")
    print(f"    safest_dist={safe_dist:.0f}m  fastest_dist={fast_dist:.0f}m")
    print(f"    routes_differ={diff}")
    return {
        "name": name, "time": elapsed, "safe_pts": safe_pts, "fast_pts": fast_pts,
        "safe_dist": safe_dist, "fast_dist": fast_dist,
        "safe_score": safe_score, "fast_score": fast_score, "diff": diff
    }


def main():
    print("=" * 60)
    print("  SafeRoute AI Safety Node Ingestion (Multi-Region)")
    print("=" * 60)
    total_start = time.time()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # ---- Step 1: Fetch OSM data for all regions ----
        print("\n[1/4] Fetching OSM data across all regions...")
        all_elements_by_id = {}
        for region in REGIONS:
            elements = fetch_osm_elements(region["bbox"], region["name"])
            for el in elements:
                key = (el.get('type'), el.get('id'))
                if key not in all_elements_by_id:
                    all_elements_by_id[key] = el
            print(f"  Running total unique elements: {len(all_elements_by_id)}")

        if not all_elements_by_id:
            print("No OSM data fetched from any region. Exiting.")
            return

        all_elements = list(all_elements_by_id.values())
        print(f"\nTotal unique OSM elements across all regions: {len(all_elements)}")

        # ---- Step 2: Prepare node data ----
        print("\n[2/4] Preparing node data...")
        all_nodes = prepare_node_data(all_elements)
        print(f"Prepared {len(all_nodes)} candidate safety node locations")

        # ---- Step 3: Compute features per region (to keep O(N^2) local) ----
        print("\n[3/4] Computing safety features per region...")
        safety_nodes = []
        seen_locations = set()
        for region in REGIONS:
            bbox = region["bbox"]
            region_nodes = [
                n for n in all_nodes
                if bbox["south"] <= n["lat"] <= bbox["north"]
                and bbox["west"] <= n["lon"] <= bbox["east"]
            ]
            if not region_nodes:
                print(f"  {region['name']}: 0 nodes (skipping)")
                continue
            print(f"  {region['name']}: {len(region_nodes)} nodes")
            region_safety_nodes = []
            for i, node in enumerate(region_nodes):
                if i % 100 == 0:
                    print(f"    Processing {i+1}/{len(region_nodes)}...")
                counts = compute_local_features(node, region_nodes)
                safety_score = compute_safety_score(counts)
                lighting_level = compute_lighting_level(counts[3])
                crowd_density = compute_crowd_density(counts[4], counts[5])
                sn = SafetyNode(
                    latitude=node['lat'],
                    longitude=node['lon'],
                    safety_score=safety_score,
                    lighting_level=lighting_level,
                    crowd_density=crowd_density,
                    updated_at=datetime.now(timezone.utc)
                )
                region_safety_nodes.append(sn)
            safety_nodes.extend(region_safety_nodes)
            print(f"  {region['name']}: created {len(region_safety_nodes)} SafetyNode objects")

        # Deduplicate by (lat, lon) rounding to 5dp (~1.1m)
        dedup = {}
        for sn in safety_nodes:
            key = (round(sn.latitude, 5), round(sn.longitude, 5))
            if key not in dedup or sn.safety_score > dedup[key].safety_score:
                dedup[key] = sn
        safety_nodes = list(dedup.values())
        print(f"\nTotal SafetyNode objects after dedup: {len(safety_nodes)}")

        # ---- Step 4: Replace in database ----
        print("\n[4/4] Replacing safety nodes in database...")
        existing_count = db.query(SafetyNode).count()
        print(f"Existing SafetyNode records: {existing_count}")

        db.query(SafetyNode).delete()
        db.flush()
        db.add_all(safety_nodes)
        db.commit()
        print(f"Inserted {len(safety_nodes)} new SafetyNode records")

        # ---- Statistics ----
        print_statistics(db)

        # ---- Test all routes ----
        print("\n=== Multi-City Route Validation ===")
        test_cases = [
            ("Delhi->Jaipur", 28.6139, 77.2090, 26.9124, 75.7873),
            ("Mumbai->Pune", 19.0760, 72.8777, 18.5204, 73.8567),
            ("Chandigarh->Dehradun", 30.7333, 76.7794, 30.3165, 78.0322),
            ("Lucknow->Kanpur", 26.8467, 80.9462, 26.4499, 80.3319),
        ]
        all_results = []
        for name, slat, slon, dlat, dlon in test_cases:
            result = test_route(db, name, slat, slon, dlat, dlon)
            all_results.append(result)

        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"{'Route':<25} {'Time':>7} {'SafePts':>8} {'FastPts':>8} {'SafeSc':>8} {'FastSc':>8} {'Diff':>6}")
        print("-" * 70)
        for r in all_results:
            print(f"{r['name']:<25} {r['time']:>6.1f}s {r['safe_pts']:>8} {r['fast_pts']:>8} {r['safe_score']:>8.4f} {r['fast_score']:>8.4f} {'YES' if r['diff'] else 'NO':>6}")

        total_elapsed = time.time() - total_start
        print(f"\nTotal ingestion time: {total_elapsed:.1f}s")
        print("\nSUCCESS: Multi-region safety node ingestion completed!")

    except Exception as e:
        print(f"\nError during ingestion: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
