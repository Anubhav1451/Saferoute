"""Check actual DB config and state."""
import os, sys
sys.path.insert(0, '.')

# Show resolve path for DB
print("CWD:", os.getcwd())
print("CWD absolute:", os.path.abspath(os.getcwd()))
print()

from app.core.config import settings
print("DATABASE_URL from settings:", settings.DATABASE_URL)

# Parse URL
url = settings.DATABASE_URL
# sqlite:///./saferoute.db or sqlite:///D:/path/saferoute.db
db_path = url.replace('sqlite:///', '')
print("DB path:", db_path)
print("DB exists:", os.path.exists(db_path))
print()

# Check DB state
from app.db.session import engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables:", tables)
    session = Session(bind=engine)
    for tbl in tables:
        count = session.execute(text(f"SELECT COUNT(*) FROM [{tbl}]")).scalar()
        print(f"  {tbl}: {count} rows")
    session.close()
except Exception as e:
    print(f"Error: {e}")

# Check saferoute.db too
print()
other_path = os.path.join(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', 'saferoute.db')
print("Also checking saferoute.db at:", os.path.abspath(other_path))
print("Exists:", os.path.exists(other_path))
