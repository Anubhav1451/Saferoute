"""Recover data from corrupted DB into fresh DB."""
import sys
import os
sys.path.append('backend')
from app.db.session import engine as old_engine
from app.core.config import settings
from app.db.models import Base
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Get old DB path
old_url = settings.DATABASE_URL.replace('sqlite:///', '')
if not os.path.isabs(old_url):
    old_url = os.path.join(settings.BASE_DIR, old_url)

new_db_path = os.path.join(settings.BASE_DIR, 'saferoute_recovered.db')
print(f'Old DB: {old_url}')
print(f'New DB: {new_db_path}')

# Create new engine
new_engine = create_engine(f'sqlite:///{new_db_path}', connect_args={'check_same_thread': False})

# Create all tables in new DB
Base.metadata.create_all(new_engine)

# Tables to recover (those not corrupted)
tables_to_recover = [
    'safety_nodes', 'crime_hotspots', 'user_reports',
    'highway_black_spots', 'accident_records', 'road_segment_risks',
    'alembic_version'
]

with new_engine.connect() as new_conn:
    with old_engine.connect() as old_conn:
        for table in tables_to_recover:
            try:
                # Check source has rows
                r = old_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = r.scalar()
                print(f'{table}: {count} rows in old DB')

                # Copy data
                if count > 0:
                    # Get column list
                    cols = old_conn.execute(text(f'SELECT * FROM "{table}" LIMIT 0')).keys()
                    col_list = ', '.join(f'"{c}"' for c in cols)
                    rows = old_conn.execute(text(f'SELECT * FROM "{table}"'))
                    for row_tuple in rows:
                        placeholders = ', '.join('?' for _ in cols)
                        new_conn.execute(
                            text(f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'),
                            list(row_tuple)
                        )
                    new_conn.commit()
                    r = new_conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    print(f'  -> {r.scalar()} rows recovered')
            except Exception as e:
                print(f'  SKIP {table}: {e}')

print(f'Recovery complete. New DB: {new_db_path}')
print(f'Old DB: {old_url} (keep as backup)')
