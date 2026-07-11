"""Create fresh database for OSM pipeline validation."""
import sys
sys.path.append('backend')
from app.db.session import engine
from app.db.models import Base
from sqlalchemy import inspect, text

# Create all tables
Base.metadata.create_all(bind=engine)

# Verify
insp = inspect(engine)
tables = insp.get_table_names()
print('Created tables:', tables)

# Set alembic version to current head
with engine.connect() as conn:
    conn.execute(text("INSERT OR REPLACE INTO alembic_version (version_num) VALUES ('520e30f0c181')"))
    conn.commit()
    r = conn.execute(text('SELECT version_num FROM alembic_version'))
    print(f'Alembic version: {r.scalar()}')

    for table in tables:
        r = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        print(f'  {table}: {r.scalar()} rows')

print('Fresh DB ready.')
