"""Check database corruption."""
import sys
sys.path.insert(0, '.')

from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.orm import Session
import sqlite3

# Check with raw sqlite3 first
db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchall()
    print("PRAGMA integrity_check:", result)
    cur.close()
    conn.close()
except Exception as e:
    print(f"SQLite3 error: {e}")

# Also check the other DB
print()
db_path2 = r"D:\saferoute-ai\backend\saferoute.db"
try:
    conn = sqlite3.connect(db_path2)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    result = cur.fetchall()
    print(f"saferoute.db integrity_check:", result)
    cur.close()
    conn.close()
except Exception as e:
    print(f"saferoute.db error: {e}")

# Can we query safe tables?
print()
try:
    session = Session(bind=engine)
    # Try querying graph_edges (new empty table)
    count = session.execute(text("SELECT COUNT(*) FROM graph_edges")).scalar()
    print(f"graph_edges: {count} (ok)")
except Exception as e:
    print(f"graph_edges error: {e}")

print()
try:
    # Try a count from osm_way_nodes
    count = session.execute(text("SELECT COUNT(*) FROM osm_way_nodes")).scalar()
    print(f"osm_way_nodes: {count} (ok)")
except Exception as e:
    print(f"osm_way_nodes error: {e}")

session.close()
