"""Check current database state."""
import sys
sys.path.insert(0, '.')

from app.db.session import engine
from app.db.models import Base
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables in DB:", tables)
print()

session = Session(bind=engine)
for tbl in tables:
    count = session.execute(text(f"SELECT COUNT(*) FROM [{tbl}]")).scalar()
    print(f"  {tbl}: {count} rows")

print()

# Check columns
for tbl in ['osm_ways', 'osm_way_nodes']:
    if tbl in tables:
        print(f"--- {tbl} columns ---")
        for col in inspector.get_columns(tbl):
            print(f"  {col['name']}: {col['type']} nullable={col['nullable']}")

# Check for graphs tables
print()
for tbl in ['graph_nodes', 'graph_edges']:
    exists = tbl in tables
    print(f"  {tbl}: {'EXISTS' if exists else 'NOT FOUND'}")

session.close()
