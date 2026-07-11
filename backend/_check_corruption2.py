"""Quick corruption check."""
import sys
sys.path.insert(0, '.')
from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.orm import Session
import sqlite3

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"

# Quick probe
try:
    conn = sqlite3.connect(db_path)
    # Set a generous timeout
    conn.execute("PRAGMA busy_timeout=5000")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sqlite_master")
    tables = cur.fetchone()[0]
    print(f"DB has {tables} objects in schema")
    cur.close()
    conn.close()
except Exception as e:
    print(f"SQLite3 schema error: {e}")

# Try simpler queries
try:
    session = Session(bind=engine)
    # New table - should work
    c = session.execute(text("SELECT COUNT(*) FROM graph_edges")).scalar()
    print(f"graph_edges: {c}")
    session.close()
except Exception as e:
    print(f"graph_edges error: {e}")
    session.close()

# The osm_ways failure might be a result of opening a new session after the error
# Let me try with a fresh engine
print()
print("Trying fresh engine for osm_ways...")
from sqlalchemy import create_engine
fresh_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
session2 = Session(bind=fresh_engine)
try:
    c = session2.execute(text("SELECT COUNT(*) FROM osm_ways")).scalar()
    print(f"osm_ways (fresh): {c}")
except Exception as e:
    print(f"osm_ways (fresh) error: {e}")
session2.close()

# Also check file size
import os
size_mb = os.path.getsize(db_path) / (1024*1024)
print(f"\nDB file size: {size_mb:.1f} MB")
