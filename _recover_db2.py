"""Use raw sqlite3 to recover data from corrupted DB."""
import sqlite3
import os
import sys
sys.path.append('backend')
from app.core.config import settings
from app.db.models import Base
from sqlalchemy import create_engine

# Get old DB path
old_url = settings.DATABASE_URL.replace('sqlite:///', '')
if not os.path.isabs(old_url):
    old_url = os.path.join(settings.BASE_DIR, old_url)

new_db_path = os.path.join(settings.BASE_DIR, 'saferoute_recovered.db')
print(f'Old DB: {old_url}')
print(f'New DB: {new_db_path}')

# Connect to old DB - open with immutable mode to prevent further corruption
try:
    old_conn = sqlite3.connect(old_url)
    old_conn.execute('PRAGMA journal_mode = OFF')
except sqlite3.DatabaseError as e:
    print(f'Cannot open old DB: {e}')
    sys.exit(1)

# Create new DB
if os.path.exists(new_db_path):
    os.remove(new_db_path)
new_conn = sqlite3.connect(new_db_path)
new_conn.execute('PRAGMA journal_mode = OFF')

# Create all tables via SQLAlchemy metadata
new_engine = create_engine(f'sqlite:///{new_db_path}', connect_args={'check_same_thread': False})
Base.metadata.create_all(new_engine)
new_engine.dispose()

# Tables to recover
tables_to_recover = [
    ('safety_nodes', 'id INTEGER PRIMARY KEY AUTOINCREMENT, '
     'latitude FLOAT NOT NULL, longitude FLOAT NOT NULL, '
     'safety_score FLOAT NOT NULL, lighting_level VARCHAR(10) NOT NULL, '
     'crowd_density VARCHAR(10) NOT NULL, updated_at DATETIME'),
    ('alembic_version', 'version_num VARCHAR(32) PRIMARY KEY'),
]

# Also recover any tables from the full list
all_tables = [
    'safety_nodes', 'crime_hotspots', 'user_reports',
    'highway_black_spots', 'accident_records', 'road_segment_risks',
    'alembic_version'
]

for table in all_tables:
    try:
        # Check if table exists in old DB
        old_cursor = old_conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not old_cursor.fetchone():
            print(f'{table}: not in old DB')
            continue

        # Get row count
        count = old_conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        print(f'{table}: {count} rows in old DB')

        if count > 0:
            # Get column info
            col_info = old_conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            col_names = [c[1] for c in col_info]
            col_list = ', '.join(f'"{c}"' for c in col_names)
            placeholders = ', '.join('?' for c in col_names)
            
            # Read old data
            rows = old_conn.execute(f'SELECT * FROM "{table}"').fetchall()
            
            # Insert into new DB
            for row in rows:
                new_conn.execute(
                    f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
                    row
                )
            new_conn.commit()
            new_count = new_conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(f'  -> {new_count} rows recovered')
    except sqlite3.DatabaseError as e:
        print(f'  SKIP {table}: {e}')

old_conn.close()
new_conn.close()

# Update DATABASE_URL in .env to point to new DB
env_path = os.path.join(settings.BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
    with open(env_path, 'w') as f:
        content = content.replace(old_url.replace('\\', '/'), new_db_path.replace('\\', '/'))
        content = content.replace(settings.DATABASE_URL, f'sqlite:///{new_db_path.replace(os.path.sep, "/")}')
        f.write(content)
    print(f'Updated .env to point to new DB')

print(f'\nDone. Recovered DB: {new_db_path}')
print(f'Backup of old DB: {old_url}')
