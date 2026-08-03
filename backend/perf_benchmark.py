"""
Phase 7 performance benchmark for the routing service.

Builds a synthetic grid graph in an in-memory SQLite DB, then measures:
  - wall-clock time for find_safest_route
  - total SQL statements executed (via engine event listener)
  - peak process RSS growth during the call

Run from backend/:  python perf_benchmark.py [--grid N] [--runs R] [--check]
"""
import argparse
import os
import sys
import time
import gc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, GraphNode, GraphEdge, RoadSegmentRisk
from app.schemas.routing import Coordinate
from app.services.routing import SafetyRoutingService


def build_grid(engine, size):
    """Build an N x N grid graph with bidirectional edges + risk records."""
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Grid geometry: size x size nodes spanning ~0.05 deg (~5.5 km) per side.
    # Coordinates kept inside India bounds (Delhi region).
    base_lat, base_lon = 28.6000, 77.2000
    dlat, dlon = 0.0002, 0.0002  # ~22 m spacing

    nodes = []
    for i in range(size):
        for j in range(size):
            idx = i * size + j
            nodes.append(GraphNode(
                id=idx + 1,
                osm_node_id=100000 + idx,
                latitude=base_lat + i * dlat,
                longitude=base_lon + j * dlon,
            ))
    db.add_all(nodes)
    db.flush()

    edges = []
    risks = []
    eid = 0
    for i in range(size):
        for j in range(size):
            src = i * size + j + 1
            # right neighbor
            if j + 1 < size:
                eid += 1
                dst = i * size + (j + 1) + 1
                edges.append(GraphEdge(
                    id=eid, source_node_id=src, dest_node_id=dst,
                    osm_way_id=None, length=30.0, direction="BIDIRECTIONAL",
                    highway="residential", travel_time=5.0, road_class="residential",
                    mid_lat=base_lat + i * dlat, mid_lon=base_lon + (j + 0.5) * dlon,
                ))
            # down neighbor
            if i + 1 < size:
                eid += 1
                dst = (i + 1) * size + j + 1
                edges.append(GraphEdge(
                    id=eid, source_node_id=src, dest_node_id=dst,
                    osm_way_id=None, length=30.0, direction="BIDIRECTIONAL",
                    highway="residential", travel_time=5.0, road_class="residential",
                    mid_lat=base_lat + (i + 0.5) * dlat, mid_lon=base_lon + j * dlon,
                ))
    db.add_all(edges)
    db.flush()

    # One risk record per edge (id aligned with edge id).
    risks = [
        RoadSegmentRisk(
            id=e.id,
            start_latitude=e.mid_lat, start_longitude=e.mid_lon,
            end_latitude=e.mid_lat, end_longitude=e.mid_lon,
            road_name="grid", segment_length_m=30.0,
            risk_score=0.1 + (e.id % 10) * 0.05,
        )
        for e in edges
    ]
    db.add_all(risks)
    db.commit()
    db.close()
    return len(nodes), eid


def count_queries(engine):
    counter = {"n": 0}
    @event.listens_for(engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        counter["n"] += 1
    return counter


def measure(engine, size, runs=3):
    SessionLocal = sessionmaker(bind=engine)
    counter = count_queries(engine)

    # Route from near bottom-left corner node to near top-right corner node.
    src = Coordinate(latitude=28.6001, longitude=77.2001)
    dst = Coordinate(latitude=28.6000 + (size - 1) * 0.0002 + 0.0001,
                     longitude=77.2000 + (size - 1) * 0.0002 + 0.0001)

    import psutil
    proc = psutil.Process()

    timings = []
    query_counts = []
    mem_deltas = []
    for _ in range(runs):
        db = SessionLocal()
        service = SafetyRoutingService(db)
        counter["n"] = 0
        gc.collect()
        rss_before = proc.memory_info().rss
        t0 = time.perf_counter()
        result = service.find_safest_route(src, dst)
        elapsed = time.perf_counter() - t0
        rss_after = proc.memory_info().rss
        db.close()
        timings.append(elapsed)
        query_counts.append(counter["n"])
        mem_deltas.append((rss_after - rss_before) / 1024 / 1024)

        n_safe = len(result["safest_route"])
        n_fast = len(result["fastest_route"])
        print(f"  run {_}: {elapsed*1000:.1f} ms, {counter['n']} queries, "
              f"safe_pts={n_safe}, fast_pts={n_fast}, "
              f"dist_safe={result['safest_distance']:.0f}m")

    return {
        "size": size,
        "nodes": len(result and []),  # placeholder
        "time_ms": [t * 1000 for t in timings],
        "queries": query_counts,
        "mem_mb": mem_deltas,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=int, default=50, help="grid side length (nodes per side)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--check", action="store_true", help="also verify result validity")
    args = ap.parse_args()

    engine = create_engine("sqlite:///:memory:")
    nodes, edges = build_grid(engine, args.grid)
    print(f"Graph: {nodes} nodes, {edges} edges ({args.grid}x{args.grid} grid)")

    res = measure(engine, args.grid, runs=args.runs)
    avg_t = sum(res["time_ms"]) / len(res["time_ms"])
    avg_q = sum(res["queries"]) / len(res["queries"])
    avg_m = sum(res["mem_mb"]) / len(res["mem_mb"])
    print(f"\nAVG: {avg_t:.1f} ms, {avg_q:.0f} queries, {avg_m:.1f} MiB RSS delta")
    print(f"SUMMARY size={res['size']} time_ms_avg={avg_t:.1f} queries_avg={avg_q:.0f} mem_mb_avg={avg_m:.2f}")


if __name__ == "__main__":
    main()
