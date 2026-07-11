"""
SafeRoute AI - OSM Pipeline Validation Script
==============================================
Validates the complete OSM pipeline end-to-end on a real dataset.
Creates a fresh database, imports OSM data, builds the routing graph,
enriches it, and validates integrity.
"""
import sys, os, time, json, math
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VALIDATION_DB = os.path.abspath("saferoute_validation.db")
OSM_PBF_FILE = os.path.abspath("delhi_sample.osm.pbf")
PGNS = {"total": 0, "failed": 0, "warnings": 0}

def log(msg: str):
    print(f"  {msg}")

def step(name: str):
    print(f"\n{'='*70}")
    print(f"STEP: {name}")
    print(f"{'='*70}")

def pass_msg(msg: str = ""):
    print(f"  [PASS] {msg}")

def fail_msg(msg: str):
    print(f"  [FAIL] {msg}")
    PGNS["failed"] += 1

def warn_msg(msg: str):
    print(f"  [WARN] {msg}")
    PGNS["warnings"] += 1

def check(condition: bool, msg: str):
    if condition:
        pass_msg(msg)
    else:
        fail_msg(msg)

PGNS["report_sections"] = []

def report_item(key: str, value):
    PGNS["report_sections"].append((key, value))
    print(f"  {key}: {value}")

# ---------------------------------------------------------------------------
# 1. Environment Setup
# ---------------------------------------------------------------------------
step("1. Environment & Dependency Verification")

# Check pyosmium
log("Checking pyosmium...")
try:
    import osmium
    log(f"  osmium: OK (version check passed)")
    PGNS["deps_osmium"] = True
except ImportError as e:
    fail_msg(f"pyosmium not installed: {e}")
    PGNS["deps_osmium"] = False

# Check other deps
for dep in ["sqlalchemy", "alembic", "sqlite3"]:
    try:
        __import__(dep)
        log(f"  {dep}: OK")
    except ImportError:
        fail_msg(f"{dep} not installed")

# Check data file
log(f"\nChecking OSM data file...")
if os.path.exists(OSM_PBF_FILE):
    size_mb = os.path.getsize(OSM_PBF_FILE) / (1024*1024)
    report_item("OSM PBF file", f"{OSM_PBF_FILE} ({size_mb:.1f} MB)")
else:
    fail_msg(f"OSM PBF file not found: {OSM_PBF_FILE}")

# Remove old validation DB if exists
if os.path.exists(VALIDATION_DB):
    os.remove(VALIDATION_DB)
    log(f"Removed old validation DB")

# ---------------------------------------------------------------------------
# 2. Create Fresh Database
# ---------------------------------------------------------------------------
step("2. Create Fresh Database")

# Use direct SQLAlchemy connection with a new DB URL
from sqlalchemy import create_engine, inspect, text, MetaData
from sqlalchemy.orm import Session, sessionmaker

validation_engine = create_engine(
    f"sqlite:///{VALIDATION_DB}",
    connect_args={"check_same_thread": False}
)

# Set PRAGMAs
with validation_engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL"))
    conn.execute(text("PRAGMA foreign_keys=ON"))
    conn.execute(text("PRAGMA synchronous=NORMAL"))
    conn.execute(text("PRAGMA cache_size=-64000"))  # 64MB cache
    conn.commit()

from app.db.models import Base
Base.metadata.create_all(bind=validation_engine)

# Verify all tables
inspector = inspect(validation_engine)
tables = inspector.get_table_names()
expected = {'safety_nodes', 'crime_hotspots', 'user_reports', 'highway_black_spots',
            'accident_records', 'road_segment_risks', 'osm_ways', 'osm_way_nodes',
            'graph_nodes', 'graph_edges'}
missing = expected - set(tables)
check(len(missing) == 0, f"All {len(expected)} tables created")
if missing:
    log(f"  Missing tables: {missing}")

for t in sorted(tables):
    col_count = len(inspector.get_columns(t))
    log(f"  {t}: {col_count} columns")

# Count total columns
total_cols = sum(len(inspector.get_columns(t)) for t in tables)
report_item("Tables created", f"{len(tables)}")
report_item("Total columns", f"{total_cols}")

ValidationSession = sessionmaker(bind=validation_engine)

# ---------------------------------------------------------------------------
# 3. OSM Import
# ---------------------------------------------------------------------------
step("3. OSM Import from PBF File")
log(f"Importing {OSM_PBF_FILE}...")

# Override the engine for the import session
from app.db.session import engine as _orig_engine
# We'll pass the session directly instead
from scripts.data_ingestion.osm_importer import OSMImporter

osm_importer = OSMImporter()
osm_importer.batch_size = 5000  # Larger batch for speed

# Monkey-patch get_session to return our validation session
orig_get_session = osm_importer.get_session
def patched_get_session():
    return ValidationSession()
osm_importer.get_session = patched_get_session

start_time = time.time()
try:
    result = osm_importer.run(filepath=OSM_PBF_FILE)
    elapsed = time.time() - start_time
    report_item("OSM Import status", result.get("status", "UNKNOWN"))
    report_item("OSM Import duration", f"{elapsed:.1f}s")
    report_item("OSM Ways imported", result.get("inserted", 0))
    report_item("OSM Import errors", result.get("errors", 0))
    report_item("Invalid coords skipped", result.get("invalid_coords", 0))
    
    if result.get("status") == "COMPLETED":
        pass_msg("OSM Import completed successfully")
    else:
        fail_msg(f"OSM Import failed: {result.get('status')}")
except Exception as e:
    elapsed = time.time() - start_time
    fail_msg(f"OSM Import exception: {e}")
    import traceback
    traceback.print_exc()

# Count what we got
session = ValidationSession()
try:
    from app.db.models import OSMWay, OSMWayNode
    way_count = session.query(OSMWay).count()
    node_count = session.query(OSMWayNode).count()
    
    # Highway type distribution
    highway_dist = {}
    for row in session.execute(text("SELECT highway, COUNT(*) as cnt FROM osm_ways GROUP BY highway ORDER BY cnt DESC")):
        highway_dist[row[0]] = row[1]
    
    report_item("OSMWay records", f"{way_count:,}")
    report_item("OSMWayNode records", f"{node_count:,}")
    report_item("Highway types", f"{len(highway_dist)}")
    
    log("\n  Highway type distribution:")
    for hw, cnt in highway_dist.items():
        log(f"    {hw}: {cnt:,}")
    
    # Quick geometry check
    null_geom = session.execute(text("SELECT COUNT(*) FROM osm_ways WHERE geometry_wkt IS NULL")).scalar()
    check(null_geom == 0, f"No NULL geometry_wkt ({null_geom} NULL)")
    
    # Check for duplicate osm_ids
    dup_ids = session.execute(text("SELECT osm_id, COUNT(*) as cnt FROM osm_ways GROUP BY osm_id HAVING cnt > 1")).fetchall()
    check(len(dup_ids) == 0, f"No duplicate osm_ids in osm_ways")
    if dup_ids:
        warn_msg(f"Found {len(dup_ids)} duplicate osm_ids in osm_ways")
    
    # Check way_node orphan ways
    orphan_nodes = session.execute(text("""
        SELECT COUNT(*) FROM osm_way_nodes wn
        LEFT JOIN osm_ways w ON wn.way_id = w.id
        WHERE w.id IS NULL
    """)).scalar()
    check(orphan_nodes == 0, f"No orphan osm_way_nodes ({orphan_nodes} orphans)")
    
    # Check OSMWayNode validity
    invalid_nodes = session.execute(text("""
        SELECT COUNT(*) FROM osm_way_nodes
        WHERE latitude < -90 OR latitude > 90 OR longitude < -180 OR longitude > 180
    """)).scalar()
    check(invalid_nodes == 0, f"No invalid coordinates in osm_way_nodes ({invalid_nodes} invalid)")
    
    session.close()
except Exception as e:
    fail_msg(f"Error during OSM verification: {e}")
    import traceback
    traceback.print_exc()

# ---------------------------------------------------------------------------
# 4. Graph Builder
# ---------------------------------------------------------------------------
step("4. Graph Builder - Build Routing Graph")
log("Converting OSM ways into GraphNodes and GraphEdges...")

from scripts.data_ingestion.graph_builder import GraphBuilder

graph_builder = GraphBuilder()
graph_builder.get_session = patched_get_session
graph_builder.batch_size = 5000

start_time = time.time()
try:
    result = graph_builder.run()
    elapsed = time.time() - start_time
    report_item("Graph Build status", result.get("status", "UNKNOWN"))
    report_item("Graph Build duration", f"{elapsed:.1f}s")
    report_item("Processed OSM ways", result.get("processed_ways", 0))
    report_item("Graph Build errors", result.get("errors", 0))
    
    if result.get("status") == "COMPLETED":
        pass_msg("Graph Builder completed successfully")
    else:
        fail_msg(f"Graph Builder failed: {result.get('status')}")
except Exception as e:
    elapsed = time.time() - start_time
    fail_msg(f"Graph Builder exception: {e}")
    import traceback
    traceback.print_exc()

# Count results
session = ValidationSession()
try:
    from app.db.models import GraphNode, GraphEdge
    gn_count = session.query(GraphNode).count()
    ge_count = session.query(GraphEdge).count()
    
    # Direction distribution
    dir_dist = {}
    for row in session.execute(text("SELECT direction, COUNT(*) FROM graph_edges GROUP BY direction")):
        dir_dist[row[0]] = row[1]
    
    # Highway type distribution in edges
    edge_highway_dist = {}
    for row in session.execute(text("SELECT highway, COUNT(*) FROM graph_edges GROUP BY highway ORDER BY COUNT(*) DESC")):
        edge_highway_dist[row[0]] = row[1]
    
    report_item("GraphNodes created", f"{gn_count:,}")
    report_item("GraphEdges created", f"{ge_count:,}")
    report_item("Edge directions", f"{dir_dist}")
    
    log("\n  Edge highway distribution:")
    for hw, cnt in edge_highway_dist.items():
        log(f"    {hw}: {cnt:,}")
    
    # Verify processing status
    unprocessed = session.execute(text("SELECT COUNT(*) FROM osm_ways WHERE processed_at IS NULL")).scalar()
    processed = session.execute(text("SELECT COUNT(*) FROM osm_ways WHERE processed_at IS NOT NULL")).scalar()
    report_item("OSM Ways processed", f"{processed:,}")
    report_item("OSM Ways unprocessed", f"{unprocessed:,}")
    check(unprocessed == 0, f"All OSM ways processed ({unprocessed} remaining)")
    
    session.close()
except Exception as e:
    fail_msg(f"Error during Graph Builder verification: {e}")
    import traceback
    traceback.print_exc()

# ---------------------------------------------------------------------------
# 5. Graph Enricher
# ---------------------------------------------------------------------------
step("5. Graph Enricher - Add Spatial Metadata")
log("Enriching graph edges with spatial metadata...")

from scripts.data_ingestion.enrich_graph import GraphEnricher

enricher = GraphEnricher()
enricher.get_session = patched_get_session
enricher.batch_size = 5000

start_time = time.time()
try:
    result = enricher.run()
    elapsed = time.time() - start_time
    report_item("Enrichment status", result.get("status", "UNKNOWN"))
    report_item("Enrichment duration", f"{elapsed:.1f}s")
    report_item("Enriched edges", result.get("enriched_edges", 0))
    report_item("Enrichment errors", result.get("errors", 0))
    
    if result.get("status") == "COMPLETED":
        pass_msg("Graph Enricher completed successfully")
    else:
        fail_msg(f"Graph Enricher failed: {result.get('status')}")
except Exception as e:
    elapsed = time.time() - start_time
    fail_msg(f"Graph Enricher exception: {e}")
    import traceback
    traceback.print_exc()

# Check enrichment results
session = ValidationSession()
try:
    # Check spatial metadata completeness
    null_mid_lat = session.execute(text("SELECT COUNT(*) FROM graph_edges WHERE mid_lat IS NULL")).scalar()
    null_priority = session.execute(text("SELECT COUNT(*) FROM graph_edges WHERE priority IS NULL")).scalar()
    null_heading = session.execute(text("SELECT COUNT(*) FROM graph_edges WHERE heading IS NULL")).scalar()
    
    check(null_mid_lat == 0, f"No edges with NULL mid_lat ({null_mid_lat} NULL)")
    check(null_priority == 0, f"No edges with NULL priority ({null_priority} NULL)")
    check(null_heading == 0, f"No edges with NULL heading ({null_heading} NULL)")
    
    report_item("Edges with NULL mid_lat", f"{null_mid_lat}")
    report_item("Edges with NULL priority", f"{null_priority}")
    report_item("Edges with NULL heading", f"{null_heading}")
    
    session.close()
except Exception as e:
    fail_msg(f"Error during Enrichment verification: {e}")

# ---------------------------------------------------------------------------
# 6. Database Integrity
# ---------------------------------------------------------------------------
step("6. Database Integrity Validation")
log("Running comprehensive integrity checks...")

session = ValidationSession()
try:
    # 6a. Orphan GraphNodes (edges referencing non-existent nodes)
    orphan_src = session.execute(text("""
        SELECT COUNT(*) FROM graph_edges e
        LEFT JOIN graph_nodes n ON e.source_node_id = n.id
        WHERE n.id IS NULL
    """)).scalar()
    orphan_dst = session.execute(text("""
        SELECT COUNT(*) FROM graph_edges e
        LEFT JOIN graph_nodes n ON e.dest_node_id = n.id
        WHERE n.id IS NULL
    """)).scalar()
    check(orphan_src == 0, f"No orphan source nodes ({orphan_src})")
    check(orphan_dst == 0, f"No orphan dest nodes ({orphan_dst})")

    # 6b. Orphan reverse: nodes with no edges
    nodes_no_edges = session.execute(text("""
        SELECT COUNT(*) FROM graph_nodes gn
        LEFT JOIN graph_edges e ON gn.id = e.source_node_id OR gn.id = e.dest_node_id
        WHERE e.id IS NULL
    """)).scalar()
    check(nodes_no_edges == 0, f"No orphan GraphNodes ({nodes_no_edges} with 0 edges)")
    if nodes_no_edges:
        warn_msg(f"{nodes_no_edges} GraphNodes have no edges")

    # 6c. Orphan OSMWayNodes
    orphan_waynodes = session.execute(text("""
        SELECT COUNT(*) FROM osm_way_nodes wn
        LEFT JOIN osm_ways w ON wn.way_id = w.id
        WHERE w.id IS NULL
    """)).scalar()
    check(orphan_waynodes == 0, f"No orphan OSMWayNodes ({orphan_waynodes})")

    # 6d. Duplicate osm_ids
    dup_osm_ids = session.execute(text("""
        SELECT osm_id, COUNT(*) as cnt FROM osm_ways
        GROUP BY osm_id HAVING cnt > 1
    """)).fetchall()
    check(len(dup_osm_ids) == 0, f"No duplicate osm_id in osm_ways ({len(dup_osm_ids)} dupes)")
    if dup_osm_ids:
        warn_msg(f"Example: osm_id={dup_osm_ids[0][0]} appears {dup_osm_ids[0][1]} times")

    # 6e. Duplicate osm_node_id in graph_nodes
    dup_gnodes = session.execute(text("""
        SELECT osm_node_id, COUNT(*) as cnt FROM graph_nodes
        GROUP BY osm_node_id HAVING cnt > 1
    """)).fetchall()
    check(len(dup_gnodes) == 0, f"No duplicate osm_node_id in graph_nodes ({len(dup_gnodes)} dupes)")
    if dup_gnodes:
        warn_msg(f"Example: osm_node_id={dup_gnodes[0][0]} appears {dup_gnodes[0][1]} times")

    # 6f. Duplicate edges (same source, dest, and osm_way_id)
    dup_edges = session.execute(text("""
        SELECT source_node_id, dest_node_id, osm_way_id, COUNT(*) as cnt
        FROM graph_edges
        GROUP BY source_node_id, dest_node_id, osm_way_id
        HAVING cnt > 1
    """)).fetchall()
    check(len(dup_edges) == 0, f"No duplicate edges ({len(dup_edges)} dupes)")
    if dup_edges:
        warn_msg(f"Example: src={dup_edges[0][0]} dst={dup_edges[0][1]} way={dup_edges[0][2]} appears {dup_edges[0][3]} times")

    # 6g. Geometry validity - check WKT format
    invalid_wkt = session.execute(text("""
        SELECT COUNT(*) FROM
        (SELECT geometry_wkt FROM osm_ways WHERE geometry_wkt IS NOT NULL)
        WHERE geometry_wkt NOT LIKE 'LINESTRING%'
    """)).scalar()
    check(invalid_wkt == 0, f"No invalid WKT geometries ({invalid_wkt})")

    # 6h. Edge geometry validity
    invalid_edge_geom = session.execute(text("""
        SELECT COUNT(*) FROM graph_edges
        WHERE geometry_wkt IS NOT NULL 
        AND geometry_wkt NOT LIKE 'LINESTRING%'
    """)).scalar()
    check(invalid_edge_geom == 0, f"No invalid edge geometries ({invalid_edge_geom})")

    # 6i. NULL critical fields
    null_critical = {}
    for tbl, col, label in [
        ("osm_ways", "osm_id", "osm_ways.osm_id"),
        ("osm_ways", "highway", "osm_ways.highway"),
        ("osm_way_nodes", "latitude", "osm_way_nodes.latitude"),
        ("osm_way_nodes", "longitude", "osm_way_nodes.longitude"),
        ("graph_nodes", "osm_node_id", "graph_nodes.osm_node_id"),
        ("graph_nodes", "latitude", "graph_nodes.latitude"),
        ("graph_nodes", "longitude", "graph_nodes.longitude"),
        ("graph_edges", "source_node_id", "graph_edges.source_node_id"),
        ("graph_edges", "dest_node_id", "graph_edges.dest_node_id"),
        ("graph_edges", "length", "graph_edges.length"),
        ("graph_edges", "direction", "graph_edges.direction"),
        ("graph_edges", "highway", "graph_edges.highway"),
        ("graph_edges", "travel_time", "graph_edges.travel_time"),
        ("graph_edges", "road_class", "graph_edges.road_class"),
    ]:
        count = session.execute(text(f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL")).scalar()
        if count > 0:
            null_critical[label] = count
    
    if null_critical:
        fail_msg(f"NULL critical fields found: {null_critical}")
        for k, v in null_critical.items():
            warn_msg(f"  {k}: {v} NULLs")
    else:
        pass_msg("No NULL critical fields in any table")

    # 6j. Edge length validity
    zero_len = session.execute(text("SELECT COUNT(*) FROM graph_edges WHERE length <= 0")).scalar()
    check(zero_len == 0, f"No zero-length edges ({zero_len})")
    if zero_len:
        warn_msg(f"{zero_len} edges have length <= 0")

    # 6k. Self-loop edges
    self_loops = session.execute(text("""
        SELECT COUNT(*) FROM graph_edges
        WHERE source_node_id = dest_node_id
    """)).scalar()
    check(self_loops == 0, f"No self-loop edges ({self_loops})")

    # 6l. Graph node coordinate ranges
    gn_bounds = session.execute(text("""
        SELECT 
            MIN(latitude), MAX(latitude), 
            MIN(longitude), MAX(longitude),
            COUNT(*) 
        FROM graph_nodes
    """)).fetchone()
    if gn_bounds[4]:
        report_item("GraphNode lat range", f"{gn_bounds[0]:.4f} to {gn_bounds[1]:.4f}")
        report_item("GraphNode lon range", f"{gn_bounds[2]:.4f} to {gn_bounds[3]:.4f}")
        report_item("Total GraphNodes", f"{gn_bounds[4]:,}")
    else:
        report_item("GraphNode lat range", "N/A (no nodes)")
        report_item("Total GraphNodes", "0")

    session.close()
except Exception as e:
    fail_msg(f"Integrity check error: {e}")
    import traceback
    traceback.print_exc()
    session.close()

# ---------------------------------------------------------------------------
# 7. Database File Info
# ---------------------------------------------------------------------------
step("7. Database File Information")
db_size = os.path.getsize(VALIDATION_DB)
report_item("DB file size", f"{db_size/(1024*1024):.1f} MB")
report_item("DB location", VALIDATION_DB)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
step("SUMMARY")
print()
fail_count = PGNS["failed"]
warn_count = PGNS["warnings"]
if fail_count == 0 and warn_count == 0:
    status = "ALL CHECKS PASSED"
elif fail_count == 0:
    status = f"ALL CHECKS PASSED ({warn_count} warnings)"
else:
    status = f"{fail_count} CHECKS FAILED ({warn_count} warnings)"

print(f"  Status: {status}")
print()
print("  Key Metrics:")
for key, value in PGNS["report_sections"]:
    print(f"    {key}: {value}")

print()
print(f"  Validation DB: {VALIDATION_DB}")
print(f"  DB Size: {db_size/(1024*1024):.1f} MB")

if fail_count > 0:
    print(f"\n  FAILED: {fail_count} checks failed - see details above")
    sys.exit(1)
else:
    print(f"\n  PASSED: Pipeline validated successfully!")
    sys.exit(0)
