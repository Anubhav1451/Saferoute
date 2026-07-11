import sys
sys.path.append('backend')
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    r = conn.execute(text('PRAGMA integrity_check'))
    print('Integrity:', r.scalar())
    
    for table in ['osm_ways', 'osm_way_nodes', 'graph_nodes', 'graph_edges']:
        r = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
        print(f'{table}: {r.scalar()}')
    
    r = conn.execute(text('SELECT COUNT(*) FROM osm_ways WHERE processed_at IS NOT NULL'))
    print(f'osm_ways processed: {r.scalar()}')
    
    r = conn.execute(text('PRAGMA page_count'))
    pages = r.scalar()
    r = conn.execute(text('PRAGMA page_size'))
    page_size = r.scalar()
    print(f'DB pages: {pages}, page_size: {page_size}, total: {pages * page_size} bytes')
