"""Test UPDATE on specific way ID that failed."""
import sqlite3, os

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"
print(f"Testing updates on way_id=4905")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 5000")
cur = conn.cursor()

# First check the row
cur.execute("SELECT id, osm_id, highway, name, processed_at FROM osm_ways WHERE id = 4905")
row = cur.fetchone()
print(f"Row 4905 before: {row}")

# Try UPDATE on processed_at
try:
    cur.execute("UPDATE osm_ways SET processed_at = datetime('now') WHERE id = 4905")
    conn.commit()
    print("UPDATE id=4905 processed_at: OK")
    # Roll back
    cur.execute("UPDATE osm_ways SET processed_at = NULL WHERE id = 4905")
    conn.commit()
    print("Rolled back: OK")
except Exception as e:
    print(f"UPDATE id=4905 failed: {e}")
    conn.rollback()

# Try UPDATE on other field
try:
    cur.execute("UPDATE osm_ways SET name = name WHERE id = 4905")
    conn.commit()
    print("UPDATE id=4905 name=name: OK")
except Exception as e:
    print(f"UPDATE id=4905 name=name failed: {e}")

# Try UPDATE with rowid syntax
try:
    cur.execute("UPDATE osm_ways SET updated_at = datetime('now') WHERE id = 4905")
    conn.commit()
    print("UPDATE id=4905 updated_at: OK")
except Exception as e:
    print(f"UPDATE id=4905 updated_at: {e}")

# Try other way ids that failed in test
for wid in [4906, 4907]:
    try:
        cur.execute("UPDATE osm_ways SET name = name WHERE id = ?", (wid,))
        print(f"UPDATE id={wid}: OK")
    except Exception as e:
        print(f"UPDATE id={wid}: FAILED - {e}")

# Try specific test: execute the exact SQL that SQLAlchemy runs
print()
print("Testing exact SQLAlchemy-style UPDATE:")
try:
    import datetime
    now = datetime.datetime.utcnow()
    cur.execute(
        "UPDATE osm_ways SET processed_at=?, updated_at=? WHERE osm_ways.id = ?",
        (str(now), str(now), 4905)
    )
    conn.commit()
    print("Exact SQLAlchemy UPDATE: OK")
    # Rollback
    cur.execute("UPDATE osm_ways SET processed_at = NULL, updated_at = NULL WHERE id = 4905")
    conn.commit()
except Exception as e:
    print(f"Exact SQLAlchemy UPDATE: FAILED - {e}")

conn.close()
