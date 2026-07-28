"""Run GraphBuilder on a small sample to validate the pipeline."""
import sys
sys.path.insert(0, '.')

import time
from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.models import Base, OSMWay, GraphNode, GraphEdge
from scripts.data_ingestion.graph_builder import GraphBuilder
from datetime import datetime

# Get raw session, run GraphBuilder logic on a sample
session = Session(bind=engine)

# Get a sample of unprocessed ways (limit to 1000 for speed)
ways = session.query(OSMWay).filter(OSMWay.processed_at == None).limit(1000).all()
print(f"Processing sample of unprocessed ways ({len(ways)})...")

start = time.time()

# We need GraphBuilder to process these ways
builder = GraphBuilder()
builder.start_batch(total_records=len(ways), metadata={"mode": "sample"})

for i, way in enumerate(ways):
    try:
        # Load the way nodes for this way into the builder's cache
        builder._load_way_nodes_for_batch(session, [way.id])
        builder.process_way(session, way)
        way.processed_at = datetime.utcnow()

        if (i + 1) % 25 == 0:
            session.commit()
            print(f"  Processed {i+1}/{len(ways)} ways...")
    except Exception as e:
        print(f"  FAILED way {way.id}: {e}")
        import traceback
        traceback.print_exc()

session.commit()

elapsed = time.time() - start
print(f"\nGraphBuilder sample completed in {elapsed:.2f}s")

# Check what was created
from sqlalchemy import func
gn_count = session.query(func.count(GraphNode.id)).scalar()
ge_count = session.query(func.count(GraphEdge.id)).scalar()
print(f"GraphNodes created: {gn_count}")
print(f"GraphEdges created: {ge_count}")

# Fetch sample edges for verification
print("\n--- Sample edges ---")
edges = session.query(GraphEdge).limit(5).all()
for e in edges:
    print(f"  id={e.id} src={e.source_node_id} dst={e.dest_node_id} len={e.length:.1f}m dir={e.direction} highway={e.highway} travel_time={e.travel_time:.1f}s")

session.close()
