"""Drop and recreate corrupted OSM/graph tables, preserving other data."""
import sys
sys.path.append('backend')
from app.db.session import engine
from app.db.models import Base, OSMWay, OSMWayNode, GraphNode, GraphEdge
from sqlalchemy import inspect, text

# Verify current state
insp = inspect(engine)
tables = insp.get_table_names()
print('Current tables:', tables)

# Drop graph tables first (FK dependencies), then OSM tables
drop_order = ['graph_edges', 'graph_nodes', 'osm_way_nodes', 'osm_ways']

with engine.begin() as conn:
    for table in drop_order:
        if table in tables:
            print(f'Dropping {table}...')
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
    
    # Recreate via SQLAlchemy metadata
    Base.metadata.create_all(engine, tables=[OSMWay.__table__, OSMWayNode.__table__, GraphNode.__table__, GraphEdge.__table__])

# Verify
insp = inspect(engine)
tables = insp.get_table_names()
print('Tables after fix:', tables)

with engine.connect() as conn:
    for table in ['osm_ways', 'osm_way_nodes', 'graph_nodes', 'graph_edges', 'safety_nodes']:
        if table in tables:
            try:
                r = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                print(f'  {table}: {r.scalar()} rows')
            except Exception as e:
                print(f'  {table}: ERROR - {e}')

print('DB fix complete.')
