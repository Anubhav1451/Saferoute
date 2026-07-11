"""Run GraphBuilder on a small sample - use the class itself."""
import sys
import os
sys.path.insert(0, '.')

# First ensure graph tables exist
from app.db.models import Base, GraphNode, GraphEdge, OSMWay
from app.db.session import engine
Base.metadata.create_all(bind=engine, tables=[GraphNode.__table__, GraphEdge.__table__])

# Clear any existing test data
from sqlalchemy import text
from sqlalchemy.orm import Session
session = Session(bind=engine)
session.execute(text("DELETE FROM graph_edges"))
session.execute(text("DELETE FROM graph_nodes"))
session.commit()
session.close()

# Now run the GraphBuilder properly
from scripts.data_ingestion.graph_builder import GraphBuilder
import time

start = time.time()
builder = GraphBuilder()

# We need to manually process only a few ways since run() processes ALL
# Let's modify approach: create a custom run that limits ways
session2 = Session(bind=engine)

# Get a small sample
ways = session2.query(OSMWay).filter(OSMWay.processed_at == None).limit(10).all()
print(f"Processing {len(ways)} sample ways")
print(f"Sample way IDs: {[w.id for w in ways]}")

import time
from datetime import datetime

for i, way in enumerate(ways):
    t0 = time.time()
    try:
        builder.process_way(session2, way)
        way.processed_at = datetime.utcnow()
        dt = time.time() - t0
        print(f"  way {way.id} ({way.highway}, osm_id={way.osm_id}): OK ({dt:.3f}s)")
    except Exception as e:
        dt = time.time() - t0
        print(f"  way {way.id}: FAILED ({dt:.3f}s) - {e}")
        import traceback
        traceback.print_exc()
        break

session2.commit()

from sqlalchemy import func
gn = session2.query(func.count(GraphNode.id)).scalar()
ge = session2.query(func.count(GraphEdge.id)).scalar()
print(f"\nGraphNodes: {gn}, GraphEdges: {ge}")
print(f"Total time: {time.time()-start:.2f}s")

session2.close()
