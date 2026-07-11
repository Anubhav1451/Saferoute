"""Create graph tables if they don't exist."""
import sys
sys.path.insert(0, '.')

from app.db.models import Base, GraphNode, GraphEdge
from app.db.session import engine

# Create only graph tables
Base.metadata.create_all(bind=engine, tables=[GraphNode.__table__, GraphEdge.__table__])
print("Graph tables created/verified.")

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables:", tables)

# Count existing graph nodes/edges
session = Session(bind=engine)
for tbl in ['graph_nodes', 'graph_edges']:
    if tbl in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM [{tbl}]")).scalar()
        print(f"  {tbl}: {count} rows")
    else:
        print(f"  {tbl}: NOT FOUND")

session.close()
