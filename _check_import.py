import sys
sys.path.append('backend')
from app.db.session import engine
from sqlalchemy import inspect, text

insp = inspect(engine)
tables = insp.get_table_names()
print('Tables:', tables)

with engine.connect() as conn:
    for table in tables:
        r = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        print(f'  {table}: {r.scalar()} rows')
    
    # Check if osm_ways has data
    r = conn.execute(text('SELECT osm_id, highway, name FROM osm_ways LIMIT 3'))
    print('\nSample osm_ways:')
    for row in r:
        print(f'  osm_id={row[0]}, highway={row[1]}, name={row[2]}')
    
    r = conn.execute(text('SELECT COUNT(*) FROM osm_way_nodes'))
    print(f'\nosm_way_nodes: {r.scalar()} rows')
