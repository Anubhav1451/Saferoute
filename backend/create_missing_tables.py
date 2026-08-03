from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Try to create the tables directly
    print('Creating route_monitor table...')
    db.execute(text('''
        CREATE TABLE IF NOT EXISTS route_monitor (
            id INTEGER NOT NULL,
            route_id VARCHAR(255) NOT NULL,
            start_location VARCHAR(255) NOT NULL,
            end_location VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (id)
        )
    '''))

    print('Creating indexes for route_monitor...')
    db.execute(text('CREATE INDEX IF NOT EXISTS ix_route_monitor_id ON route_monitor (id)'))
    db.execute(text('CREATE INDEX IF NOT EXISTS ix_route_monitor_route_id ON route_monitor (route_id)'))

    print('Creating offline_maps table...')
    db.execute(text('''
        CREATE TABLE IF NOT EXISTS offline_maps (
            id INTEGER NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            bounds_north FLOAT NOT NULL,
            bounds_south FLOAT NOT NULL,
            bounds_east FLOAT NOT NULL,
            bounds_west FLOAT NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size BIGINT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT (datetime('now')),
            updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (id)
        )
    '''))

    print('Creating indexes for offline_maps...')
    db.execute(text('CREATE INDEX IF NOT EXISTS ix_offline_maps_id ON offline_maps (id)'))
    db.execute(text('CREATE INDEX IF NOT EXISTS ix_offline_maps_name ON offline_maps (name)'))

    db.commit()
    print('Tables created successfully!')

    # Verify
    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='route_monitor'"))
    route_monitor_exists = result.fetchone() is not None
    print('route_monitor table exists:', route_monitor_exists)

    result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='offline_maps'"))
    offline_maps_exists = result.fetchone() is not None
    print('offline_maps table exists:', offline_maps_exists)

finally:
    db.close()