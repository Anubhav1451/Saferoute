"""Test various DB operations to understand corruption extent."""
import sys, os
sys.path.insert(0, '.')

import sqlite3

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"
print(f"DB: {db_path} ({os.path.getsize(db_path)/(1024**3):.2f} GB)")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 5000")
conn.execute("PRAGMA journal_mode = WAL")
cur = conn.cursor()

# Try INSERT into graph_edges (new table, should work)
print("\n=== Testing operations ===")

try:
    cur.execute("INSERT INTO graph_edges (source_node_id, dest_node_id, length, direction, highway, travel_time, road_class) VALUES (1, 2, 100.0, 'BIDIRECTIONAL', 'primary', 10.0, 'ARTERIAL')")
    print("INSERT graph_edges: OK (will rollback)")
    conn.rollback()
except Exception as e:
    print(f"INSERT graph_edges failed: {e}")

try:
    cur.execute("INSERT INTO graph_nodes (osm_node_id, latitude, longitude) VALUES (-1, 28.0, 77.0)")
    inserted_id = cur.lastrowid
    print(f"INSERT graph_nodes: OK, id={inserted_id}")
    cur.execute(f"UPDATE graph_nodes SET latitude=28.5 WHERE id={inserted_id}")
    print(f"UPDATE graph_nodes: OK")
    conn.rollback()
except Exception as e:
    print(f"graph_nodes ops failed: {e}")

# Check if osm_ways page-level corruption
print("\n=== Testing osm_ways UPDATE on different pages ===")

# Check how the table is organized
import random

# Get a few rows scattered across the table
cur.execute("SELECT id FROM osm_ways ORDER BY id LIMIT 10")
ids_sample = [r[0] for r in cur.fetchall()]

# Get some from the middle and end
cur.execute("SELECT id FROM osm_ways ORDER BY id LIMIT 1 OFFSET 700000")
ids_sample.append(cur.fetchone()[0])

cur.execute("SELECT id FROM osm_ways ORDER BY id DESC LIMIT 1")
ids_sample.append(cur.fetchone()[0])

print(f"Testing UPDATE on row IDs: {ids_sample}")
for rid in ids_sample[:5]:
    try:
        conn.execute("SAVEPOINT test_update")
        cur.execute("UPDATE osm_ways SET name = name WHERE id = ?", (rid,))
        conn.execute("RELEASE SAVEPOINT test_update")
        print(f"  UPDATE id={rid}: OK")
    except Exception as e:
        print(f"  UPDATE id={rid}: FAILED - {e}")
        conn.execute("ROLLBACK TO SAVEPOINT test_update")

conn.close()

# Alternative approach: can we create a new clean DB?
print("\n=== Trying to create new DB from this one ===")
try:
    new_db = db_path.replace('.db', '_recovered.db')
    conn2 = sqlite3.connect(new_db)
    conn2backup = sqlite3.connect(db_path)
    conn2backup.backup(conn2, pages=1000, name="main", progress=lambda x,y: None)
    print("Backup of first 1000 pages: OK")
    conn2.close()
    conn2backup.close()
    os.remove(new_db)
except Exception as e:
    print(f"Failed: {e}")
