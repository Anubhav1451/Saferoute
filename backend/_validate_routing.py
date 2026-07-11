"""
SafeRoute AI - OSM Graph Routing Validation
=============================================
Validates routing on the generated OSM graph end-to-end:
- A* routing smoke tests
- Graph connectivity & spatial index
- Safety integration (RoadSegmentRisk lookup, edge cost, route score)
"""
import sys, os, time, math, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

P = {"failed": 0, "warnings": 0, "report": []}
VAL_DB = os.path.abspath("routing_validation.db")
OSM_PBF = os.path.abspath("delhi_sample.osm.pbf")

def log(msg): print(f"  {msg}")
def step(name): print(f"\n{'='*70}\nSTEP: {name}\n{'='*70}")
def ok(msg=""): print(f"  [PASS] {msg}")
def fail(msg): print(f"  [FAIL] {msg}"); P["failed"] += 1
def warn(msg): print(f"  [WARN] {msg}"); P["warnings"] += 1
def report(k, v): P["report"].append((k, v)); print(f"  {k}: {v}")

# ---------------------------------------------------------------------------
# 1. Setup: fresh DB + full OSM pipeline
# ---------------------------------------------------------------------------
step("1. Build OSM Graph (fresh DB + import + builder + enricher)")

for ext in ["", "-wal", "-shm"]:
    p = VAL_DB + ext
    if os.path.exists(p):
        os.remove(p)

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine("sqlite:///" + VAL_DB, connect_args={"check_same_thread": False})
with engine.connect() as c:
    c.execute(text("PRAGMA journal_mode=WAL"))
    c.execute(text("PRAGMA foreign_keys=ON"))
    c.execute(text("PRAGMA cache_size=-64000"))
    c.commit()

from app.db.models import Base, OSMWay, OSMWayNode, GraphNode, GraphEdge, RoadSegmentRisk
Base.metadata.create_all(bind=engine)

ValidationSession = sessionmaker(bind=engine)

def patched_session():
    return ValidationSession()

# --- OSM Import ---
from scripts.data_ingestion.osm_importer import OSMImporter
imp = OSMImporter()
imp.batch_size = 5000
imp.get_session = patched_session
t0 = time.time()
res = imp.run(filepath=OSM_PBF)
report("OSM Import duration", f"{time.time()-t0:.1f}s")
report("OSM Ways", res.get("inserted", 0))
report("OSM Import errors", res.get("errors", 0))

# --- Graph Builder ---
from scripts.data_ingestion.graph_builder import GraphBuilder
gb = GraphBuilder()
gb.batch_size = 2000
gb.get_session = patched_session
t0 = time.time()
res = gb.run()
report("Graph Builder duration", f"{time.time()-t0:.1f}s")
s = ValidationSession()
gn = s.query(GraphNode).count()
ge = s.query(GraphEdge).count()
report("GraphNodes", f"{gn:,}")
report("GraphEdges", f"{ge:,}")
s.close()

# --- Graph Enricher ---
from scripts.data_ingestion.enrich_graph import GraphEnricher
en = GraphEnricher()
en.batch_size = 5000
en.get_session = patched_session
t0 = time.time()
res = en.run()
report("Graph Enricher duration", f"{time.time()-t0:.1f}s")
s = ValidationSession()
null_mid = s.query(GraphEdge).filter(GraphEdge.mid_lat == None).count()
null_pri = s.query(GraphEdge).filter(GraphEdge.priority == None).count()
report("Edges with NULL mid_lat", f"{null_mid}")
report("Edges with NULL priority", f"{null_pri}")
s.close()

ok() if null_mid == 0 and null_pri == 0 else warn(f"{null_mid} NULL mid_lat, {null_pri} NULL priority")

db_size = os.path.getsize(VAL_DB) / (1024**3)
report("DB file size", f"{db_size:.1f} GB")

# ---------------------------------------------------------------------------
# 2. Graph Connectivity & Basic Stats
# ---------------------------------------------------------------------------
step("2. Graph Connectivity & Statistics")
s = ValidationSession()

# Node coordinate bounds
bounds = s.execute(text("""
    SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude), COUNT(*)
    FROM graph_nodes
""")).fetchone()
report("Graph lat range", f"{bounds[0]:.4f} to {bounds[1]:.4f}")
report("Graph lon range", f"{bounds[2]:.4f} to {bounds[3]:.4f}")
report("Total GraphNodes", f"{bounds[4]:,}")

# Edge stats
edge_stats = s.execute(text("""
    SELECT COUNT(*), MIN(length), AVG(length), MAX(length) FROM graph_edges
""")).fetchone()
report("GraphEdges count", f"{edge_stats[0]:,}")
report("Edge length min", f"{edge_stats[1]:.1f}m")
report("Edge length avg", f"{edge_stats[2]:.1f}m")
report("Edge length max", f"{edge_stats[3]:.1f}m")

# Road class distribution
rc_dist = {}
for row in s.execute(text("SELECT road_class, COUNT(*) FROM graph_edges GROUP BY road_class ORDER BY COUNT(*) DESC")):
    rc_dist[row[0]] = row[1]
report("Road classes", dict(rc_dist))

# Direction distribution
dir_dist = {}
for row in s.execute(text("SELECT direction, COUNT(*) FROM graph_edges GROUP BY direction")):
    dir_dist[row[0]] = row[1]
report("Edge directions", dir_dist)

# Orphan checks
orphan_src = s.execute(text("""
    SELECT COUNT(*) FROM graph_edges e LEFT JOIN graph_nodes n ON e.source_node_id = n.id WHERE n.id IS NULL
""")).scalar()
orphan_dst = s.execute(text("""
    SELECT COUNT(*) FROM graph_edges e LEFT JOIN graph_nodes n ON e.dest_node_id = n.id WHERE n.id IS NULL
""")).scalar()
check_orphan = 0
for label, cnt in [("orphan source", orphan_src), ("orphan dest", orphan_dst), ("orphan waynodes",
    s.execute(text("SELECT COUNT(*) FROM osm_way_nodes wn LEFT JOIN osm_ways w ON wn.way_id = w.id WHERE w.id IS NULL")).scalar())]:
    if cnt > 0: fail(f"{label}: {cnt}"); check_orphan += 1
if check_orphan == 0: ok("No orphan references")

# Nodes with 0 edges
iso = s.execute(text("""
    SELECT COUNT(*) FROM graph_nodes gn
    LEFT JOIN graph_edges e ON gn.id = e.source_node_id OR gn.id = e.dest_node_id
    WHERE e.id IS NULL
""")).scalar()
report("Isolated nodes (0 edges)", f"{iso:,}")
if iso > 0: warn(f"{iso:,} GraphNodes have no incident edges")

s.close()

# ---------------------------------------------------------------------------
# 3. Spatial Index Validation
# ---------------------------------------------------------------------------
step("3. Spatial Index & Nearest-Node/Edge Lookup")
s = ValidationSession()

from app.services.graph_utils import GraphSpatialIndex, haversine_distance

t0 = time.time()
spatial = GraphSpatialIndex(s)
build_time = time.time() - t0
report("Spatial index build time", f"{build_time:.3f}s")

# Grid stats
report("Node grid cells", f"{len(spatial._node_grid):,}")
report("Edge grid cells", f"{len(spatial._edge_grid):,}")

# Nearest node from Delhi center
delhi_center = (28.6139, 77.2090)
t0 = time.time()
nn = spatial.nearest_node(delhi_center[0], delhi_center[1], radius_m=5000)
nn_time = time.time() - t0
if nn is not None:
    node = s.query(GraphNode).get(nn)
    dist = haversine_distance(delhi_center[0], delhi_center[1], node.latitude, node.longitude)
    report("Nearest node to Delhi center", f"id={nn} lat={node.latitude:.4f} lon={node.longitude:.4f} dist={dist:.1f}m lookup={nn_time*1000:.1f}ms")
    ok(f"Nearest node found in {nn_time*1000:.1f}ms")
else:
    fail("Nearest node NOT found within 5km of Delhi center")

# Nearest edge
t0 = time.time()
ne = spatial.nearest_edge(delhi_center[0], delhi_center[1], radius_m=5000)
ne_time = time.time() - t0
if ne is not None:
    edge = s.query(GraphEdge).get(ne)
    ok(f"Nearest edge found (id={ne}) in {ne_time*1000:.1f}ms")
    report("Nearest edge highway", edge.highway)
    report("Nearest edge road_class", edge.road_class)
else:
    fail("Nearest edge NOT found within 5km of Delhi center")

# Bbox query
bbox = (28.55, 77.12, 28.65, 77.25)  # central Delhi
t0 = time.time()
bbox_nodes = spatial.get_nodes_in_bbox(*bbox)
bbox_edges = spatial.get_edges_in_bbox(*bbox)
bbox_time = time.time() - t0
report("Bbox query time", f"{bbox_time*1000:.1f}ms")
report("Nodes in central Delhi bbox", f"{len(bbox_nodes):,}")
report("Edges in central Delhi bbox", f"{len(bbox_edges):,}")

s.close()

# ---------------------------------------------------------------------------
# 4. A* Routing on OSM Graph
# ---------------------------------------------------------------------------
step("4. A* Routing on OSM Graph")

s = ValidationSession()

# Load graph into memory for routing
# Build adjacency: node_id -> [(neighbor_id, edge_id, length, travel_time, road_class, highway)]
t0 = time.time()
adjacency = {}
edge_map = {}
node_map = {}

# Load all edges
edges = s.query(GraphEdge).all()
for e in edges:
    eid = e.id
    src = e.source_node_id
    dst = e.dest_node_id
    edge_map[eid] = e
    adjacency.setdefault(src, []).append((dst, eid, e.length, e.travel_time, e.road_class, e.highway))

# Load all node coords
nodes = s.query(GraphNode).all()
for n in nodes:
    node_map[n.id] = (n.latitude, n.longitude)

load_time = time.time() - t0
report("Graph loaded in memory", f"{load_time:.1f}s")
report("Adjacency entries", f"{sum(len(v) for v in adjacency.values()):,}")
report("Unique source nodes", f"{len(adjacency):,}")

# Test coordinates (central Delhi)
test_routes = [
    ("Central Delhi → South Delhi", (28.6139, 77.2090), (28.5300, 77.2200)),
    ("Central Delhi → East Delhi",  (28.6139, 77.2090), (28.6200, 77.2800)),
    ("Central Delhi → West Delhi",  (28.6139, 77.2090), (28.6000, 77.1000)),
    ("Central Delhi → North Delhi", (28.6139, 77.2090), (28.6800, 77.2000)),
]

# Heuristic: haversine / max_speed (so estimate min travel time)
def heuristic(nid_a, nid_b):
    if nid_a not in node_map or nid_b not in node_map:
        return 0
    lat1, lon1 = node_map[nid_a]
    lat2, lon2 = node_map[nid_b]
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    return dist / 25.0  # assume 25 km/h minimum speed

def osm_astar(start_nid, goal_nid, max_expand=50000):
    import heapq
    open_set = [(0.0, start_nid, 0.0, [start_nid], 0)]
    closed = set()
    expanded = 0
    
    while open_set and expanded < max_expand:
        f, current, g, path, depth = heapq.heappop(open_set)
        if current == goal_nid:
            return {"found": True, "path": path, "cost": g, "expanded": expanded, "depth": depth}
        if current in closed:
            continue
        closed.add(current)
        expanded += 1
        
        for neighbor, eid, length, ttime, rc, hw in adjacency.get(current, []):
            if neighbor in closed:
                continue
            ng = g + ttime
            nh = heuristic(neighbor, goal_nid)
            heapq.heappush(open_set, (ng + nh, neighbor, ng, path + [neighbor], depth + 1))
    
    return {"found": False, "expanded": expanded, "cost": None, "path": None, "depth": 0}

# Find nearest graph nodes for each start/end
def find_node(lat, lon, max_radius=10000):
    return spatial.nearest_node(lat, lon, max_radius)

A_starts = {}
A_goals = {}
for label, start, end in test_routes:
    A_starts[label] = find_node(start[0], start[1])
    A_goals[label] = find_node(end[0], end[1])

report("Route queries", f"{len(test_routes)}")

routing_fails = 0
for label, start, end in test_routes:
    snid = A_starts[label]
    gnid = A_goals[label]
    if snid is None:
        fail(f"{label}: start node not found near ({start[0]:.4f}, {start[1]:.4f})")
        routing_fails += 1
        continue
    if gnid is None:
        fail(f"{label}: goal node not found near ({end[0]:.4f}, {end[1]:.4f})")
        routing_fails += 1
        continue
    
    t0 = time.time()
    result = osm_astar(snid, gnid)
    elapsed = time.time() - t0
    
    if result["found"]:
        # Reconstruct geometry
        path_coords = [(node_map[nid][0], node_map[nid][1]) for nid in result["path"]]
        total_dist_m = 0
        for i in range(len(result["path"]) - 1):
            a = node_map[result["path"][i]]
            b = node_map[result["path"][i+1]]
            total_dist_m += haversine_distance(a[0], a[1], b[0], b[1])
        
        # Count unique edges traversed
        edges_traversed = 0
        edge_set = set()
        for i in range(len(result["path"]) - 1):
            a, b = result["path"][i], result["path"][i+1]
            for neighbor, eid, *_ in adjacency.get(a, []):
                if neighbor == b:
                    edge_set.add(eid)
                    edges_traversed += 1
                    break
        
        ok(f"{label}: ROUTE FOUND")
        report(f"  [{label}] Execution time", f"{elapsed*1000:.1f}ms")
        report(f"  [{label}] Nodes expanded", f"{result['expanded']:,}")
        report(f"  [{label}] Edges traversed", f"{edges_traversed:,}")
        report(f"  [{label}] Route distance", f"{total_dist_m/1000:.2f} km")
        report(f"  [{label}] Route cost (travel time)", f"{result['cost']:.1f}s")
        report(f"  [{label}] Path depth", f"{result['depth']}")
        report(f"  [{label}] Geometry coords", f"{len(path_coords)}")
    else:
        fail(f"{label}: NO ROUTE FOUND (expanded {result['expanded']:,} nodes)")
        routing_fails += 1

s.close()

# ---------------------------------------------------------------------------
# 5. Safety Integration Check
# ---------------------------------------------------------------------------
step("5. Safety Integration — RoadSegmentRisk & Edge Cost")

s = ValidationSession()

# Check if RoadSegmentRisk data exists in this DB
rsr_count = s.query(RoadSegmentRisk).count()
report("RoadSegmentRisk records", f"{rsr_count:,}")
if rsr_count == 0:
    warn("No RoadSegmentRisk data — safety penalty integration will use zero penalty")

# For each edge, compute a safety score using existing route scoring pattern
# Load some edges and compute their RoadSegmentRisk proximity
sample_edges = s.query(GraphEdge).filter(GraphEdge.mid_lat != None).limit(1000).all()
edges_with_safety = 0

for e in sample_edges:
    if e.mid_lat is not None and e.mid_lon is not None:
        # Check if any RoadSegmentRisk is near this edge's midpoint
        nearby_rsr = s.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.start_latitude.between(e.mid_lat - 0.01, e.mid_lat + 0.01),
            RoadSegmentRisk.start_longitude.between(e.mid_lon - 0.01, e.mid_lon + 0.01)
        ).count()
        if nearby_rsr > 0:
            edges_with_safety += 1

report("Edges near RoadSegmentRisk (sample 1000)", f"{edges_with_safety}")

# Compute a simple per-edge safety score using the existing calculate_safety_score logic
# from routing.py
SAFETY_SCORE_MAX_PENALTY = 2500
SEGMENT_RISK_BASE_PENALTY = 500

def calculate_safety_score(avg_penalty):
    return max(0.0, 1.0 - avg_penalty / SAFETY_SCORE_MAX_PENALTY)

# Average length-weighted safety score for the full graph
total_len = 0
weighted_penalty = 0
for e in sample_edges:
    penalty = 0
    if rsr_count > 0 and e.mid_lat is not None:
        rsr = s.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.start_latitude.between(e.mid_lat - 0.005, e.mid_lat + 0.005),
            RoadSegmentRisk.start_longitude.between(e.mid_lon - 0.005, e.mid_lon + 0.005)
        ).first()
        if rsr:
            penalty += rsr.risk_score * SEGMENT_RISK_BASE_PENALTY
    total_len += e.length
    weighted_penalty += penalty * e.length

avg_penalty = weighted_penalty / total_len if total_len > 0 else 0
overall_score = calculate_safety_score(avg_penalty)
report("Avg per-edge penalty (sample 1000)", f"{avg_penalty:.2f}")
report("Overall route safety score (simulated)", f"{overall_score:.4f}")
report("Safety score interpretation", "1.0 = safest, 0.0 = most dangerous")

# Check that the OSM graph edges have the fields needed for the routing engine
report("GraphEdge has highway field", str(hasattr(GraphEdge, 'highway')))
report("GraphEdge has length field", str(hasattr(GraphEdge, 'length')))
report("GraphEdge has travel_time field", str(hasattr(GraphEdge, 'travel_time')))
report("GraphEdge has road_class field", str(hasattr(GraphEdge, 'road_class')))
report("GraphEdge has direction field", str(hasattr(GraphEdge, 'direction')))
report("GraphNode has coords", str(hasattr(GraphNode, 'latitude') and hasattr(GraphNode, 'longitude')))

s.close()

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
step("SUMMARY")
print()
fc = P["failed"]
wc = P["warnings"]
if fc == 0 and wc == 0:
    status = "ALL CHECKS PASSED"
elif fc == 0:
    status = f"ALL CHECKS PASSED ({wc} warnings)"
else:
    status = f"{fc} FAILED ({wc} warnings)"

print(f"  Status: {status}")
print()
for k, v in P["report"]:
    print(f"    {k}: {v}")
print()
print(f"  Validation DB: {VAL_DB}")
print(f"  DB Size: {os.path.getsize(VAL_DB)/(1024*1024*1024):.2f} GB")

print()
if routing_fails > 0:
    print(f"  NOTE: {routing_fails} route(s) failed. This is expected if the OSM")
    print(f"  graph does not cover the requested region. The Delhi sample covers")
    print(f"  approximately central Delhi (28.5-28.7 N, 77.1-77.3 E).")
    print(f"  Cross-country routes (Delhi→Mumbai, etc.) require the full India OSM extract.")

if fc > 0:
    sys.exit(1)
else:
    sys.exit(0)
