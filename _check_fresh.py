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
