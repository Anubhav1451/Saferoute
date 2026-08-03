#!/usr/bin/env python3
"""G6 Phases 4-10: Run remaining stages on existing DB with OSM data + partial graph."""
import json
import os
import sys
import time

import psutil

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_ROOT)

DB_PATH = r'C:\Users\anubh\AppData\Local\Temp\g6_validation_7sppitrd\saferoute.db'
DB_URL = f'sqlite:///{DB_PATH}'
os.environ['DATABASE_URL'] = DB_URL

process = psutil.Process(os.getpid())
results = []

def mem_mb():
    return process.memory_info().rss / 1048576

def record(name, status, duration, records=None, warnings=None, failures=None, m0=0, m1=0, details=''):
    entry = {'name': name, 'status': status, 'duration_s': round(duration, 3),
             'mem_before_mb': round(m0, 1), 'mem_after_mb': round(m1, 1),
             'mem_delta_mb': round(m1 - m0, 1), 'records': records or {},
             'warnings': warnings or [], 'failures': failures or [], 'details': details}
    results.append(entry)
    icon = {'PASS':'[OK]','FAIL':'[FAIL]','SKIP':'[SKIP]','BLOCKED':'[BLK]'}.get(status,'[???]')
    print(f"  {icon} {name}: {status} ({duration:.1f}s, mem {m0:.0f}->{m1:.0f}MB)")
    if warnings:
        for w in warnings: print(f"       WARN: {w}")
    if failures:
        for f in failures: print(f"       FAIL: {f}")

# ── Verify current state ──
print("=" * 60)
print("G6 Phase 4-10: Remaining Stages")
print("=" * 60)

from app.db.models import (
    AccidentRecord,
    GraphEdge,
    GraphNode,
    HighwayBlackSpot,
    OSMWay,
    RoadSegmentRisk,
    SafetyNode,
)
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
s = Session()
state = {
    'osm_ways': s.query(func.count(OSMWay.id)).scalar(),
    'osm_processed': s.query(func.count(OSMWay.id)).filter(OSMWay.processed_at != None).scalar(),
    'graph_nodes': s.query(func.count(GraphNode.id)).scalar(),
    'graph_edges': s.query(func.count(GraphEdge.id)).scalar(),
    'hbs': s.query(func.count(HighwayBlackSpot.id)).scalar(),
    'ar': s.query(func.count(AccidentRecord.id)).scalar(),
    'rsr': s.query(func.count(RoadSegmentRisk.id)).scalar(),
    'sn': s.query(func.count(SafetyNode.id)).scalar(),
}
s.close(); engine.dispose()

print(f"\nCurrent DB state:")
for k, v in state.items():
    print(f"  {k}: {v:,}")

# ── Stage 5: Graph Enrichment ──
print(f"\n{'='*60}")
print("[5/10] Graph Enrichment")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []

# Count unenriched edges
engine = create_engine(DB_URL)
s = Session()
unenriched = s.query(func.count(GraphEdge.id)).filter(GraphEdge.mid_lat == None).scalar()
total_edges = s.query(func.count(GraphEdge.id)).scalar()
s.close(); engine.dispose()

if unenriched == 0:
    print(f"  All {total_edges:,} edges already enriched")
    record('graph_enrich', 'PASS', 0, {'edges_enriched': total_edges, 'errors': 0},
           m0=m0, m1=mem_mb())
    enrich_info = {'edges_enriched': total_edges, 'errors': 0}
else:
    print(f"  Enriching {unenriched:,} / {total_edges:,} edges...")
    from scripts.data_ingestion.enrich_graph import GraphEnricher
    enricher = GraphEnricher()
    try:
        result = enricher.run()
    except Exception as e:
        failures.append(f"Crashed: {e}")
        result = {}
    finally:
        enricher.close_all()
    duration = time.time() - t0
    enriched = result.get('enriched_edges', 0)
    errors = result.get('errors', 0)
    if errors > 0: warnings.append(f"{errors} errors")
    status = result.get('status', 'UNKNOWN')
    record('graph_enrich', status, duration,
           {'edges_enriched': enriched, 'errors': errors, 'unenriched_before': unenriched},
           warnings=warnings, failures=failures, m0=m0, m1=mem_mb())
    enrich_info = {'edges_enriched': enriched, 'errors': errors}

# ── Stage 6: Black Spot Import ──
print(f"\n{'='*60}")
print("[6/10] Black Spot Import")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []
DATA_RAW = os.path.join(os.path.dirname(BACKEND_ROOT), 'data', 'raw')

compatible_files = []
for src_name in ['dataful', 'opencity', 'morth', 'state', 'irad']:
    src = os.path.join(DATA_RAW, src_name)
    if os.path.isdir(src):
        for f in os.listdir(src):
            if f.endswith('.csv') and not f.startswith('.'):
                compatible_files.append(os.path.join(src, f))

if not compatible_files:
    warnings.append("No compatible CSV files in data/raw/ — requires Dataful (paid) or iRAD data")
    record('blackspot_import', 'SKIP', time.time() - t0,
           {'files_found': 0, 'inserted': 0},
           warnings=warnings, m0=m0, m1=mem_mb())
    blackspot_info = {'files_found': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}
else:
    from scripts.data_ingestion.morth_blackspots_importer import MoRTHBlackSpotImporter
    total_ins = total_skip = total_err = 0
    for fp in compatible_files:
        try:
            imp = MoRTHBlackSpotImporter()
            r = imp.run(filepath=fp)
            imp.close_all()
            total_ins += r.get('inserted', 0)
            total_skip += r.get('skipped', 0)
            total_err += r.get('errors', 0)
        except ValueError as e:
            warnings.append(f"{os.path.basename(fp)}: schema mismatch — {e}")
        except Exception as e:
            failures.append(f"{os.path.basename(fp)}: {e}")
    status = 'PASS' if not failures and total_ins > 0 else ('SKIP' if not failures else 'FAIL')
    record('blackspot_import', status, time.time() - t0,
           {'files_found': len(compatible_files), 'inserted': total_ins,
            'skipped': total_skip, 'errors': total_err},
           warnings=warnings, failures=failures, m0=m0, m1=mem_mb())
    blackspot_info = {'files_found': len(compatible_files), 'inserted': total_ins,
                      'skipped': total_skip, 'errors': total_err}

# ── Stage 7: Accident Import ──
print(f"\n{'='*60}")
print("[7/10] Accident Import")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []

if not compatible_files:
    warnings.append("No compatible CSV files in data/raw/ — requires iRAD FIR or OpenCity data")
    record('accident_import', 'SKIP', time.time() - t0,
           {'files_found': 0, 'inserted': 0},
           warnings=warnings, m0=m0, m1=mem_mb())
    accident_info = {'files_found': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}
else:
    from scripts.data_ingestion.morth_accidents_importer import AccidentRecordImporter
    total_ins = total_skip = total_err = 0
    acc_files = [f for f in compatible_files if 'opencity' in f or 'morth' in f or 'irad' in f]
    for fp in acc_files:
        try:
            imp = AccidentRecordImporter()
            r = imp.run(filepath=fp)
            imp.close_all()
            total_ins += r.get('inserted', 0)
            total_skip += r.get('skipped', 0)
            total_err += r.get('errors', 0)
        except Exception as e:
            failures.append(f"{os.path.basename(fp)}: {e}")
    status = 'PASS' if not failures and total_ins > 0 else ('SKIP' if not failures else 'FAIL')
    record('accident_import', status, time.time() - t0,
           {'files_found': len(acc_files), 'inserted': total_ins,
            'skipped': total_skip, 'errors': total_err},
           warnings=warnings, failures=failures, m0=m0, m1=mem_mb())
    accident_info = {'files_found': len(acc_files), 'inserted': total_ins,
                     'skipped': total_skip, 'errors': total_err}

# ── Stage 8: Chainage Resolution ──
print(f"\n{'='*60}")
print("[8/10] Chainage Resolution")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []

engine = create_engine(DB_URL)
s = Session()
pending = s.query(func.count(HighwayBlackSpot.id)).filter(
    HighwayBlackSpot.geometry_resolution == 'PENDING').scalar() or 0
total_hbs = s.query(func.count(HighwayBlackSpot.id)).scalar() or 0

if pending == 0:
    warnings.append(f"No PENDING black spots (total HBS: {total_hbs})")
    s.close(); engine.dispose()
    record('chainage_resolution', 'SKIP', time.time() - t0,
           {'total_blackspots': total_hbs, 'pending': 0, 'resolved': 0},
           warnings=warnings, m0=m0, m1=mem_mb())
    chainage_info = {'total_blackspots': total_hbs, 'pending': 0, 'resolved': 0}
else:
    from scripts.data_ingestion.chainage_resolver import ChainageResolver
    resolver = ChainageResolver(s)
    try:
        r = resolver.resolve_highway_blackspots()
    except Exception as e:
        failures.append(f"Crashed: {e}")
        r = {}
    s.close(); engine.dispose()
    duration = r.get('duration_seconds', time.time() - t0)
    record('chainage_resolution', 'PASS' if not failures else 'FAIL', duration,
           {'total_blackspots': total_hbs, 'pending': r.get('total_pending', 0),
            'resolved': r.get('resolved', 0), 'unresolved': r.get('unresolved', 0)},
           warnings=warnings, failures=failures, m0=m0, m1=mem_mb())
    chainage_info = r

# ── Stage 9: Road Segment Risk ──
print(f"\n{'='*60}")
print("[9/10] Road Segment Risk")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []

engine = create_engine(DB_URL)
s = Session()
hbs_c = s.query(func.count(HighwayBlackSpot.id)).scalar() or 0
ar_c = s.query(func.count(AccidentRecord.id)).scalar() or 0
s.close(); engine.dispose()

if hbs_c == 0 and ar_c == 0:
    warnings.append("No input data: HighwayBlackSpot=0, AccidentRecord=0")
    record('segment_risk', 'BLOCKED', time.time() - t0,
           {'input_hbs': 0, 'input_ar': 0, 'segments_created': 0},
           warnings=warnings, m0=m0, m1=mem_mb())
    segment_info = {'input_hbs': 0, 'input_ar': 0, 'segments_created': 0}
else:
    from scripts.data_ingestion.compute_segment_risk import RoadSegmentRiskBuilder
    builder = RoadSegmentRiskBuilder()
    try:
        r = builder.run()
    except Exception as e:
        failures.append(f"Crashed: {e}")
        r = {}
    duration = r.get('duration_seconds', time.time() - t0)
    record('segment_risk', 'PASS' if not failures else 'FAIL', duration,
           {'input_hbs': hbs_c, 'input_ar': ar_c,
            'segments_created': r.get('segments_created', 0)},
           warnings=warnings, failures=failures, m0=m0, m1=mem_mb())
    segment_info = r

# ── Stage 9.5: Graph Validation ──
print(f"\n{'='*60}")
print("[9.5/10] Graph Validation")
print(f"{'='*60}")
m0 = mem_mb(); t0 = time.time()
warnings, failures = [], []

from scripts.data_ingestion.validate_graph import GraphValidator

engine = create_engine(DB_URL)
s = Session()
validator = GraphValidator(s)
try:
    issues = validator.run_all_checks()
    summary = validator.get_summary()
except Exception as e:
    failures.append(f"Crashed: {e}")
    summary = {}
s.close(); engine.dispose()

duration = time.time() - t0
issue_details = []
for iss in issues:
    issue_details.append(f"[{iss.severity}] {iss.check}: {iss.message}")
critical = summary.get('critical', 0)
errors_count = summary.get('error', 0)
if critical > 0: failures.append(f"{critical} CRITICAL issues")
if errors_count > 0:
    non_empty = [i for i in issues if i.severity == 'ERROR' and i.check != 'empty_graph']
    if non_empty: warnings.append(f"{len(non_empty)} non-trivial ERROR issues")

record('graph_validation', 'PASS' if critical == 0 else 'FAIL', duration,
       {'total_issues': summary.get('total_issues', 0), 'critical': critical,
        'error': errors_count, 'warning': summary.get('warning', 0),
        'info': summary.get('info', 0)},
       warnings=warnings, failures=failures, m0=m0, m1=mem_mb(),
       details='\n'.join(issue_details))

# ── Save partial results ──
json_path = os.path.join(os.path.dirname(DB_PATH), 'g6_phases_5_9.json')
with open(json_path, 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to: {json_path}")
print(f"\nStage summary:")
for r in results:
    icon = {'PASS':'[OK]','FAIL':'[FAIL]','SKIP':'[SKIP]','BLOCKED':'[BLK]'}.get(r['status'],'[???]')
    print(f"  {icon} {r['name']}: {r['status']} ({r['duration_s']}s)")
