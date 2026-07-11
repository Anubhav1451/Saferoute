import sys
sys.path.append('backend')
from app.db.session import engine
from sqlalchemy import text, inspect

# Check which tables are readable
insp = inspect(engine)
tables = insp.get_table_names()
print('Tables:', tables)

with engine.connect() as conn:
    for table in tables:
        if table == 'alembic_version':
            continue
        try:
            r = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            print(f'  {table}: {r.scalar()} rows')
        except Exception as e:
            print(f'  {table}: ERROR - {e}')
