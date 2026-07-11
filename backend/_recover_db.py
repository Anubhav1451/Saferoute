"""Try to recover the corrupted database."""
import sqlite3, os, sys, subprocess, tempfile, time

db_path = r"D:\saferoute-ai\backend\saferoute_recovered.db"
recovered_path = r"D:\saferoute-ai\backend\saferoute_recovered_clean.db"
backup_path = r"D:\saferoute-ai\backend\saferoute_recovered_backup.db"

# Step 1: Take the backup path
print("=== Attempting database recovery ===")
print(f"Source: {db_path} ({os.path.getsize(db_path)/(1024**3):.2f} GB)")

# First try to use sqlite3 .clone or .backup
print("\n1. Trying sqlite3 CLI .backup...")
start = time.time()
try:
    # Use sqlite3 CLI which handles large backups better
    import subprocess
    result = subprocess.run(
        ['sqlite3', db_path, f'.backup {recovered_path}'],
        capture_output=True, text=True, timeout=7200
    )
    if result.returncode != 0:
        raise Exception(result.stderr)
    
    elapsed = time.time() - start
    recovered_size = os.path.getsize(recovered_path) / (1024**3)
    print(f"   Backup completed in {elapsed:.1f}s")
    print(f"   Recovered DB size: {recovered_size:.2f} GB")
    
except Exception as e:
    print(f"   CLI backup failed: {e}")
    print("   Trying Python API backup...")
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=30000")
        
        backup_conn = sqlite3.connect(recovered_path)
        conn.backup(backup_conn)
        backup_conn.close()
        conn.close()
        
        elapsed = time.time() - start
        print(f"   Python backup completed in {elapsed:.1f}s")
    except Exception as e2:
        print(f"   Python backup also failed: {e2}")
        recovered_path = None

if recovered_path and os.path.exists(recovered_path):
    # Test the recovered DB
    try:
        conn2 = sqlite3.connect(recovered_path)
        cur = conn2.cursor()
        cur.execute("SELECT COUNT(*) FROM osm_ways")
        count = cur.fetchone()[0]
        print(f"   osm_ways count: {count}")
        
        # Test UPDATE on the previously problematic row
        cur.execute("UPDATE osm_ways SET processed_at = datetime('now') WHERE id = 4905")
        print(f"   UPDATE way 4905: OK")
        cur.execute("UPDATE osm_ways SET processed_at = NULL WHERE id = 4905")
        cur.execute("SELECT COUNT(*) FROM osm_way_nodes")
        nodes_count = cur.fetchone()[0]
        print(f"   osm_way_nodes count: {nodes_count}")
        
        conn2.close()
        print(f"\n✅ Recovery successful! Clean DB at: {recovered_path}")
    except Exception as e:
        print(f"   Verification failed: {e}")
    
    # Fallback: try .dump and restore
    print("\n2. Trying sqlite3 .dump recovery...")
    try:
        dump_file = r"D:\saferoute-ai\backend\_dump.sql"
        
        # Dump using subprocess
        with open(dump_file, 'w', encoding='utf-8') as f:
            subprocess.run(
                ['sqlite3', db_path, '.dump'],
                stdout=f, stderr=subprocess.PIPE,
                timeout=3600
            )
        
        print(f"   Dump completed, size: {os.path.getsize(dump_file)/(1024**3):.2f} GB")
        
        # Restore to new DB
        conn3 = sqlite3.connect(recovered_path)
        conn3.executescript(open(dump_file, 'r', encoding='utf-8').read())
        conn3.close()
        
        print(f"   Restore completed")
        os.remove(dump_file)
        print(f"✅ Recovery via dump successful!")
        
    except Exception as e2:
        print(f"   Dump recovery also failed: {e2}")
        print("❌ Database cannot be recovered. Will need to reimport OSM data.")
        
        if os.path.exists(dump_file):
            os.remove(dump_file)

# Cleanup old recovery if exists
for f in [recovered_path]:
    if os.path.exists(f):
        print(f"Recovered DB: {os.path.getsize(f)/(1024**3):.2f} GB")
