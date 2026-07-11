"""Check corruption extent and try recovery."""
import sys, os, time
sys.path.insert(0, '.')

import sqlite3

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"

# 1. Quick integrity_check with timeout
print("=== Checking saferoute_recovered.db ===")
print(f"File size: {os.path.getsize(db_path) / (1024**3):.2f} GB")

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA busy_timeout = 5000")
cur = conn.cursor()

# Quick check - just check the osm_ways table specifically
try:
    cur.execute("SELECT COUNT(*) FROM osm_ways")
    print(f"osm_ways COUNT(*) works: {cur.fetchone()[0]}")
except Exception as e:
    print(f"osm_ways COUNT(*) failed: {e}")

# Try SELECT with LIMIT
try:
    cur.execute("SELECT id, osm_id FROM osm_ways LIMIT 5")
    rows = cur.fetchall()
    print(f"osm_ways SELECT LIMIT 5: {rows}")
except Exception as e:
    print(f"osm_ways SELECT LIMIT failed: {e}")

# Try UPDATE with a known row
try:
    # What's the first row?
    cur.execute("SELECT MIN(id), MAX(id) FROM osm_ways")
    min_id, max_id = cur.fetchone()
    print(f"osm_ways id range: {min_id} - {max_id}")
    
    # Try to update a specific row
    cur.execute("SELECT id FROM osm_ways WHERE id = ?", (min_id,))
    print(f"Row {min_id}: {cur.fetchone()}")
except Exception as e:
    print(f"Range query failed: {e}")

# Check for the other DB
print()
print("=== Checking saferoute.db ===")
db2_path = r"D:\saferoute-ai\backend\saferoute.db"
if os.path.exists(db2_path):
    print(f"File size: {os.path.getsize(db2_path) / (1024**3):.2f} GB")
    
    conn2 = sqlite3.connect(db2_path)
    conn2.execute("PRAGMA busy_timeout = 5000")
    cur2 = conn2.cursor()
    
    try:
        cur2.execute("SELECT COUNT(*) FROM osm_ways")
        print(f"osm_ways COUNT(*) works: {cur2.fetchone()[0]}")
    except Exception as e:
        print(f"osm_ways COUNT(*) failed: {e}")
    
    conn2.close()

conn.close()
