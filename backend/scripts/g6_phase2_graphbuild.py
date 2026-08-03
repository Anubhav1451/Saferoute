#!/usr/bin/env python3
"""Phase 2: Continue graph build on existing DB with OSM data already imported."""
import os
import sys
import time

import psutil

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_ROOT)

DB_PATH = r'C:\Users\anubh\AppData\Local\Temp\g6_validation_7sppitrd\saferoute.db'
os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'

process = psutil.Process(os.getpid())
from scripts.data_ingestion.graph_builder import GraphBuilder

m0 = process.memory_info().rss / 1048576
t0 = time.time()
builder = GraphBuilder()
result = builder.run()
builder.close_all()
duration = time.time() - t0
m1 = process.memory_info().rss / 1048576

print(f"\nGraph build complete: {duration:.1f}s, mem {m0:.0f}->{m1:.0f}MB")
print(f"Result: {result}")
