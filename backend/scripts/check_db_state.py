"""Quick DB state check script."""
import os
import sys

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_ROOT)
from app.db.session import engine
from sqlalchemy import text


def check_db():
    with engine.connect() as conn:
        # Tables
        r = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        tables = [t[0] for t in r.fetchall()]
        print(f"Tables: {len(tables)}")
        for t in tables:
            cnt = conn.execute(text(f"SELECT COUNT(*) FROM [{t}]")).scalar()
            print(f"  {t}: {cnt} rows")
        # Indexes
        r = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"))
        idxs = [t[0] for t in r.fetchall()]
        print(f"Indexes: {len(idxs)}")
        # File size
        db_url = str(engine.url)
        if "sqlite" in db_url:
            db_path = db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                sz = os.path.getsize(db_path)
                print(f"DB file: {sz/1024/1024:.1f} MB ({sz:,} bytes)")

if __name__ == "__main__":
    check_db()
