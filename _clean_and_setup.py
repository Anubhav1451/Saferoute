"""Clean up old DBs and create a fresh one for OSM pipeline validation."""
import os
import sys
sys.path.append('backend')
from app.core.config import settings
from app.db.session import engine
from app.db.models import Base

# Backup old DBs
project_root = os.path.dirname(os.path.abspath(__file__))
backup_dir = os.path.join(project_root, '_db_backups')
os.makedirs(backup_dir, exist_ok=True)

# Find all .db files
import glob
for db_file in glob.glob(os.path.join(project_root, '**/*.db'), recursive=True):
    # Skip etl_metadata.db and other system DBs
    if 'etl_metadata' in db_file or 'saferoute_recovered' in db_file:
        continue
    basename = os.path.basename(db_file)
    backup_path = os.path.join(backup_dir, basename)
    if not os.path.exists(backup_path):
        os.rename(db_file, backup_path)
        print(f'Moved {db_file} -> {backup_path}')

# Now create a fresh DB by using alembic or create_all
print('Creating fresh database...')
Base.metadata.create_all(bind=engine)

# Verify
from sqlalchemy import inspect, text
insp = inspect(engine)
tables = insp.get_table_names()
print('Created tables:', tables)

# Set alembic version to current head
with engine.connect() as conn:
    conn.execute(text("INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('520e30f0c181')"))
    conn.commit()
    r = conn.execute(text("SELECT version_num FROM alembic_version"))
    print(f'Alembic version: {r.scalar()}')

    for table in ['osm_ways', 'osm_way_nodes', 'graph_nodes', 'graph_edges', 'safety_nodes']:
        if table in tables:
            r = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            print(f'  {table}: {r.scalar()} rows')

print('Fresh DB ready.')
print(f'Old DBs backed up to: {backup_dir}')
