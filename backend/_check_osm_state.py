"""Check OSM processing state."""
import sys
sys.path.insert(0, '.')

from app.db.session import engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

session = Session(bind=engine)

# Check processed_at
result = session.execute(text("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN processed_at IS NULL THEN 1 ELSE 0 END) as unprocessed,
        SUM(CASE WHEN processed_at IS NOT NULL THEN 1 ELSE 0 END) as processed
    FROM osm_ways
""")).fetchone()

print(f"OSMWay: total={result[0]}, unprocessed={result[1]}, processed={result[2]}")

# Sample of unprocessed ways
print()
print("--- Sample unprocessed ways (10) ---")
rows = session.execute(text("""
    SELECT id, osm_id, highway, name, ref 
    FROM osm_ways 
    WHERE processed_at IS NULL 
    LIMIT 10
""")).fetchall()
for r in rows:
    print(f"  id={r[0]} osm_id={r[1]} highway={r[2]} name={r[3]} ref={r[4]}")

# Check highway type distribution
print()
print("--- Highway type distribution ---")
rows = session.execute(text("""
    SELECT highway, COUNT(*) as cnt 
    FROM osm_ways 
    GROUP BY highway 
    ORDER BY cnt DESC
    LIMIT 20
""")).fetchall()
for r in rows:
    print(f"  {r[0]}: {r[1]}")

# Check DB file size
import os
db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"
size_mb = os.path.getsize(db_path) / (1024*1024)
print(f"\nDB size: {size_mb:.1f} MB")

session.close()
