"""Check what OSM data files are available."""
import os, sys

files = [
    r"D:\saferoute-ai\backend\delhi_sample.osm.pbf",
    r"D:\saferoute-ai\data\raw\osm\northern-zone-260626.osm.pbf",
    r"D:\saferoute-ai\backend\hyderabad_sample.osm.pbf",
    r"D:\saferoute-ai\backend\sample.osm.pbf",
]

for f in files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        size_str = f"{size:,} bytes"
        if size > 1024*1024:
            size_str = f"{size/(1024*1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size/1024:.1f} KB"
        print(f"EXISTS: {f} ({size_str})")
    else:
        print(f"MISSING: {f} (not found)")

# Quick check if delhi_sample is valid
print()
try:
    import osmium
    class QuickCheck(osmium.SimpleHandler):
        def __init__(self):
            super().__init__()
            self.way_count = 0
        def way(self, w):
            self.way_count += 1
            if self.way_count >= 100:
                return
    
    for f in files:
        if os.path.exists(f) and os.path.getsize(f) > 1000:
            print(f"Scanning {os.path.basename(f)}...")
            qc = QuickCheck()
            try:
                qc.apply_file(f, locations=True)
                print(f"  Ways: {qc.way_count}")
            except Exception as e:
                print(f"  Error: {e}")
except Exception as e:
    print(f"osmium check error: {e}")
