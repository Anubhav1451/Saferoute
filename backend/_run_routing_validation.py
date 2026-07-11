"""
SafeRoute AI - OSM Graph Routing Validation (Fast)
===================================================
Runs steps 2-6 using the existing routing_validation.db
(skip the full pipeline rebuild since data is already populated)
"""
import sys, os, time, math, json, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

VAL_DB = os.path.abspath("routing_validation.db")
engine = create_engine("sqlite:///" + VAL_DB, connect_args={"check_same_thread": False})
S = sessionmaker(bind=engine)

def haversine_distance(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * 6371000 * math.asin(math.sqrt(a))

# ===========================================================================
# 2. Graph Connectivity & Statistics
# ===========================================================================
print("=" * 70)
print("STEP: 2. Graph Connectivity & Statistics")
print("=" * 70)
s = S()

bounds = s.execute(text("SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude), COUNT(*) FROM graph_nodes")).fetchone()
print(f"  Graph lat range: {bounds[0]:.4f} to {bounds[1]:.4f}")
print(f"  Graph lon range: {bounds[2]:.4f} to {bounds[3]:.4f}")
print(f"  Total GraphNodes: {bounds[4]:,}")

edge_stats = s.execute(text("SELECT COUNT(*), MIN(length), AVG(length), MAX(length) FROM graph_edges")).fetchone()
print(f"  GraphEdges count: {edge_stats[0]:,}")
print(f"  Edge length min: {edge_stats[1]:.1f}m")
print(f"  Edge length avg: {edge_stats[2]:.1f}m")
print(f"  Edge length max: {edge_stats[3]:.1f}m")

rc_dist = {row[0]: row[1] for row in s.execute(text("SELECT road_class, COUNT(*) FROM graph_edges GROUP BY road_class ORDER BY COUNT(*) DESC"))}
print(f"  Road classes: {json.dumps(rc_dist, indent=4)}")
dir_dist = {row[0]: row[1] for row in s.execute(text("SELECT direction, COUNT(*) FROM graph_edges GROUP BY direction"))}
print(f"  Edge directions: {dir_dist}")

orphan_src = s.execute(text("SELECT COUNT(*) FROM graph_edges e LEFT JOIN graph_nodes n ON e.source_node_id = n.id WHERE n.id IS NULL")).scalar()
orphan_dst = s.execute(text("SELECT COUNT(*) FROM graph_edges e LEFT JOIN graph_nodes n ON e.dest_node_id = n.id WHERE n.id IS NULL")).scalar()
orphan_wn = s.execute(text("SELECT COUNT(*) FROM osm_way_nodes wn LEFT JOIN osm_ways w ON wn.way_id = w.id WHERE w.id IS NULL")).scalar()
print(f"  Orphan source: {orphan_src}, dest: {orphan_dst}, waynodes: {orphan_wn}")

iso = s.execute(text("SELECT COUNT(*) FROM graph_nodes gn LEFT JOIN graph_edges e ON gn.id = e.source_node_id OR gn.id = e.dest_node_id WHERE e.id IS NULL")).scalar()
print(f"  Isolated nodes (0 edges): {iso:,}")

null_critical = {}
for tbl, col, label in [
    ("osm_ways", "osm_id", "osm_ways.osm_id"),
    ("graph_nodes", "latitude", "graph_nodes.latitude"),
    ("graph_edges", "length", "graph_edges.length"),
    ("graph_edges", "travel_time", "graph_edges.travel_time"),
    ("graph_edges", "road_class", "graph_edges.road_class"),
]:
    cnt = s.execute(text(f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL")).scalar()
    if cnt > 0:
        null_critical[label] = cnt
if null_critical:
    print(f"  [FAIL] NULL critical fields: {null_critical}")
else:
    print(f"  [PASS] No NULL critical fields")

zero_len = s.execute(text("SELECT COUNT(*) FROM graph_edges WHERE length <= 0")).scalar()
self_loops = s.execute(text("SELECT COUNT(*) FROM graph_edges WHERE source_node_id = dest_node_id")).scalar()
print(f"  Zero-length edges: {zero_len}, self-loops: {self_loops}")

s.close()

# ===========================================================================
# 3. Spatial Index
# ===========================================================================
print()
print("=" * 70)
print("STEP: 3. Spatial Index & Nearest-Node/Edge Lookup")
print("=" * 70)
s = S()
from app.services.graph_utils import GraphSpatialIndex

t0 = time.time()
spatial = GraphSpatialIndex(s)
print(f"  Spatial index build time: {time.time()-t0:.3f}s")
print(f"  Node grid cells: {len(spatial._node_grid):,}")
print(f"  Edge grid cells: {len(spatial._edge_grid):,}")

delhi_center = (28.6139, 77.2090)
t0 = time.time()
nn = spatial.nearest_node(delhi_center[0], delhi_center[1], radius_m=5000)
nn_time = time.time() - t0
if nn is not None:
    from app.db.models import GraphNode
    node = s.query(GraphNode).get(nn)
    dist = haversine_distance(delhi_center[0], delhi_center[1], node.latitude, node.longitude)
    print(f"  Nearest node to Delhi center: id={nn} lat={node.latitude:.4f} lon={node.longitude:.4f} dist={dist:.1f}m lookup={nn_time*1000:.1f}ms")
else:
    print("  [FAIL] Nearest node NOT found within 5km of Delhi center")

t0 = time.time()
ne = spatial.nearest_edge(delhi_center[0], delhi_center[1], radius_m=5000)
ne_time = time.time() - t0
if ne is not None:
    from app.db.models import GraphEdge
    edge = s.query(GraphEdge).get(ne)
    print(f"  Nearest edge found (id={ne}) in {ne_time*1000:.1f}ms")
    print(f"  Nearest edge highway={edge.highway} road_class={edge.road_class}")
else:
    print("  [WARN] Nearest edge NOT found within 5km of Delhi center")

bbox = (28.55, 77.12, 28.65, 77.25)
t0 = time.time()
bbox_nodes = spatial.get_nodes_in_bbox(*bbox)
bbox_edges = spatial.get_edges_in_bbox(*bbox)
print(f"  Bbox query time: {(time.time()-t0)*1000:.1f}ms")
print(f"  Nodes in central Delhi bbox: {len(bbox_nodes):,}")
print(f"  Edges in central Delhi bbox: {len(bbox_edges):,}")
s.close()

# ===========================================================================
# 4. A* Routing on OSM Graph
# ===========================================================================
print()
print("=" * 70)
print("STEP: 4. A* Routing on OSM Graph")
print("=" * 70)
s = S()

t0 = time.time()
adjacency = {}
node_map = {}
edges = s.query(GraphEdge).all()
for e in edges:
    adjacency.setdefault(e.source_node_id, []).append((e.dest_node_id, e.id, e.length, e.travel_time, e.road_class, e.highway))
nodes = s.query(GraphNode).all()
for n in nodes:
    node_map[n.id] = (n.latitude, n.longitude)
print(f"  Graph loaded in memory: {time.time()-t0:.1f}s")
print(f"  Adjacency entries: {sum(len(v) for v in adjacency.values()):,}")
print(f"  Unique source nodes: {len(adjacency):,}")

def heuristic(nid_a, nid_b):
    if nid_a not in node_map or nid_b not in node_map:
        return 0
    lat1, lon1 = node_map[nid_a]
    lat2, lon2 = node_map[nid_b]
    return haversine_distance(lat1, lon1, lat2, lon2) / 25.0

def osm_astar(start_nid, goal_nid, max_expand=50000):
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
            nh = heuristic(neighbor, goal_nid)
            heapq.heappush(open_set, (g + ttime + nh, neighbor, g + ttime, path + [neighbor], depth + 1))
    return {"found": False, "expanded": expanded}

test_routes = [
    ("Central Delhi -> South Delhi", (28.6139, 77.2090), (28.5300, 77.2200)),
    ("Central Delhi -> East Delhi",  (28.6139, 77.2090), (28.6200, 77.2800)),
    ("Central Delhi -> West Delhi",  (28.6139, 77.2090), (28.6000, 77.1000)),
    ("Central Delhi -> North Delhi", (28.6139, 77.2090), (28.6800, 77.2000)),
]

routing_fails = 0
for label, start, end in test_routes:
    snid = spatial.nearest_node(start[0], start[1], 10000)
    gnid = spatial.nearest_node(end[0], end[1], 10000)
    if snid is None:
        print(f"  [FAIL] {label}: start not found")
        routing_fails += 1
        continue
    if gnid is None:
        print(f"  [FAIL] {label}: goal not found")
        routing_fails += 1
        continue

    t0 = time.time()
    result = osm_astar(snid, gnid)
    elapsed = time.time() - t0

    if result["found"]:
        total_dist = sum(
            haversine_distance(node_map[result["path"][i]][0], node_map[result["path"][i]][1],
                               node_map[result["path"][i+1]][0], node_map[result["path"][i+1]][1])
            for i in range(len(result["path"]) - 1)
        )
        edge_set = set()
        for i in range(len(result["path"]) - 1):
            a, b = result["path"][i], result["path"][i+1]
            for neighbor, eid, *_ in adjacency.get(a, []):
                if neighbor == b:
                    edge_set.add(eid)
                    break
        print(f"  [PASS] {label}: ROUTE FOUND")
        print(f"    Time: {elapsed*1000:.1f}ms | Expanded: {result['expanded']:,} | Edges: {len(edge_set):,} | Dist: {total_dist/1000:.2f}km | Cost: {result['cost']:.1f}s | Depth: {result['depth']}")
    else:
        print(f"  [FAIL] {label}: NO ROUTE (expanded {result['expanded']:,} nodes)")
        routing_fails += 1

s.close()

# ===========================================================================
# 5. Safety Integration
# ===========================================================================
print()
print("=" * 70)
print("STEP: 5. Safety Integration")
print("=" * 70)
s = S()
from app.db.models import RoadSegmentRisk
rsr_count = s.query(RoadSegmentRisk).count()
print(f"  RoadSegmentRisk records: {rsr_count:,}")
if rsr_count == 0:
    print("  [WARN] No RoadSegmentRisk data")

sample = s.query(GraphEdge).filter(GraphEdge.mid_lat != None).limit(1000).all()
edges_near = 0
for e in sample:
    if e.mid_lat is not None:
        cnt = s.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.start_latitude.between(e.mid_lat - 0.01, e.mid_lat + 0.01),
            RoadSegmentRisk.start_longitude.between(e.mid_lon - 0.01, e.mid_lon + 0.01)
        ).count()
        if cnt > 0:
            edges_near += 1
print(f"  Edges near RoadSegmentRisk (sample 1000): {edges_near}")
s.close()

# ===========================================================================
# Summary
# ===========================================================================
print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"  DB file size: {os.path.getsize(VAL_DB)/(1024*1024*1024):.2f} GB")
print(f"  Routing failures: {routing_fails}")
if routing_fails == 0:
    print("  ALL ROUTING CHECKS PASSED")
else:
    print(f"  {routing_fails} routes failed (check coverage area)")
print(f"  Validation DB: {VAL_DB}")
