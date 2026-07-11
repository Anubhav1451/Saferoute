"""Test OSMWayNode queries specifically."""
import sys, os
sys.path.insert(0, '.')

import sqlite3

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 5000")
cur = conn.cursor()

# Try querying OSMWayNode
try:
    cur.execute("SELECT COUNT(*) FROM osm_way_nodes")
    print(f"osm_way_nodes COUNT: {cur.fetchone()[0]}")
except Exception as e:
    print(f"osm_way_nodes COUNT failed: {e}")

# Try a specific way's nodes
try:
    cur.execute("SELECT way_id, COUNT(*) FROM osm_way_nodes GROUP BY way_id LIMIT 5")
    rows = cur.fetchall()
    print(f"osm_way_nodes group by way (5): {rows}")
except Exception as e:
    print(f"osm_way_nodes group by failed: {e}")

# Try selecting nodes for a few ways (the kind of query process_way does)
try:
    cur.execute("SELECT way_id, osm_node_id, sequence FROM osm_way_nodes WHERE way_id = 1 ORDER BY sequence LIMIT 10")
    rows = cur.fetchall()
    print(f"Nodes for way_id=1: {len(rows)} rows, sample: {rows[:3]}")
except Exception as e:
    print(f"Nodes for way_id=1 failed: {e}")

# Try some more way ids
for wid in [1, 2, 3, 100, 1000]:
    try:
        cur.execute("SELECT COUNT(*) FROM osm_way_nodes WHERE way_id = ?", (wid,))
        count = cur.fetchone()[0]
        print(f"  way_id={wid}: {count} nodes")
    except Exception as e:
        print(f"  way_id={wid} failed: {e}")

# Try the UPDATE that failed
try:
    cur.execute("UPDATE osm_ways SET processed_at = datetime('now') WHERE id = 1")
    print("UPDATE osm_ways id=1: OK")
    cur.execute("UPDATE osm_ways SET processed_at = NULL WHERE id = 1")
    print("Rolled back: OK")
except Exception as e:
    print(f"UPDATE osm_ways failed: {e}")

conn.close()
