import os
import sys
import time

# Set environment variable for a fresh database
os.environ['DATABASE_URL'] = 'sqlite:///./test_fresh_sample.db'
print(f'DATABASE_URL set to: {os.environ["DATABASE_URL"]}')

# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import after setting env var
from app.db.session import engine
from app.db.models import Base
from scripts.data_ingestion.osm_importer import OSMImporter
from scripts.data_ingestion.graph_builder import GraphBuilder
from scripts.data_ingestion.enrich_graph import GraphEnricher
from sqlalchemy import func, text, select
from app.db.models import OSMWay, OSMWayNode, GraphNode, GraphEdge

def main():
    # Remove existing file
    db_file = './test_fresh_sample.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f'Removed existing {db_file}')
    # Create tables
    Base.metadata.create_all(engine)
    print('Tables created.')
    # Print engine URL for verification
    print(f'Engine URL: {engine.url}')

    pbf_path = r'D:/saferoute-ai/backend/delhi_sample.osm.pbf'
    if not os.path.exists(pbf_path):
        print(f'Sample file not found: {pbf_path}')
        return 1

    # 1. OSM Importer
    print('\n[1/3] Running OSMImporter...')
    start = time.time()
    importer = OSMImporter()
    osm_result = importer.run(filepath=pbf_path)
    osm_time = time.time() - start
    print(f'  Status: {osm_result["status"]}')
    print(f'  Ways inserted: {osm_result["inserted"]}')
    print(f'  Errors: {osm_result["errors"]}')
    print(f'  Duration: {osm_time:.2f}s')

    # 2. Graph Builder
    print('\n[2/3] Running GraphBuilder...')
    start = time.time()
    builder = GraphBuilder()
    graph_result = builder.run()
    graph_time = time.time() - start
    print(f'  Status: {graph_result["status"]}')
    print(f'  Processed ways: {graph_result["processed_ways"]}')
    print(f'  Errors: {graph_result["errors"]}')
    print(f'  Duration: {graph_time:.2f}s')

    # 3. Graph Enricher
    print('\n[3/3] Running GraphEnricher...')
    start = time.time()
    enricher = GraphEnricher()
    enrich_result = enricher.run()
    enrich_time = time.time() - start
    print(f'  Status: {enrich_result["status"]}')
    print(f'  Enriched edges: {enrich_result["enriched_edges"]}')
    print(f'  Errors: {enrich_result["errors"]}')
    print(f'  Duration: {enrich_time:.2f}s')

    total_time = osm_time + graph_time + enrich_time
    print(f'\nTotal pipeline time: {total_time:.2f}s')

    # 4. Integrity checks
    print('\n[4/4] Performing database integrity checks...')
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    # Counts
    osm_ways = session.query(OSMWay).count()
    osm_nodes = session.query(OSMWayNode).count()
    graph_nodes = session.query(GraphNode).count()
    graph_edges = session.query(GraphEdge).count()

    # Duplicate OSM IDs
    dup_ways = session.query(OSMWay.osm_id, func.count(OSMWay.osm_id)).group_by(OSMWay.osm_id).having(func.count(OSMWay.osm_id) > 1).count()

    # Null geometry edges
    null_geom = session.query(GraphEdge).filter(GraphEdge.geometry_wkt == None).count()

    # Null OSM nodes in graph
    null_osm_nodes = session.query(GraphNode).filter(GraphNode.osm_node_id == None).count()

    # Orphan graph nodes (no edges)
    subq_source = select(GraphEdge.source_node_id)
    subq_dest = select(GraphEdge.dest_node_id)
    orphan_nodes = session.query(GraphNode).filter(
        ~GraphNode.id.in_(subq_source),
        ~GraphNode.id.in_(subq_dest)
    ).count()

    # Orphan edges (dangling refs)
    orphan_edges = session.query(GraphEdge).filter(
        ~GraphEdge.source_node_id.in_(session.query(GraphNode.id)) |
        ~GraphEdge.dest_node_id.in_(session.query(GraphNode.id))
    ).count()

    print(f'  OSM Ways: {osm_ways}')
    print(f'  OSM Nodes: {osm_nodes}')
    print(f'  Graph Nodes: {graph_nodes}')
    print(f'  Graph Edges: {graph_edges}')
    print(f'  Duplicate OSM Ways: {dup_ways}')
    print(f'  Edges with NULL geometry: {null_geom}')
    print(f'  Graph Nodes with NULL OSM ID: {null_osm_nodes}')
    print(f'  Orphan Graph Nodes (no edges): {orphan_nodes}')
    print(f'  Orphan Edges (dangling node refs): {orphan_edges}')

    # Determine pass/fail
    failed = False
    if dup_ways > 0 or null_geom > 0 or null_osm_nodes > 0:
        failed = True

    if failed:
        print('\n[FAIL] Integrity issues found.')
        return 1
    else:
        print('\n[PASS] Integrity check passed.')
        return 0

if __name__ == '__main__':
    sys.exit(main())