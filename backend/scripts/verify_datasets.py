#!/usr/bin/env python3
"""
verify_datasets.py — SafeRoute AI Dataset Verification Tool

Scans the data/raw directory tree, detects available source datasets,
reports missing expected files, and prints the recommended import order.

Usage:
    python scripts/verify_datasets.py
    python scripts/verify_datasets.py --verbose

Exit codes:
    0 — all required datasets present
    1 — one or more required datasets missing
"""

import argparse
import fnmatch
import os
import sys
from collections import defaultdict
from datetime import datetime


# Path resolution: project root is two levels up from this script
SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")


# Expected files by source directory
SOURCE_SPEC = {
    "dataful": {
        "label": "Dataful MoRTH Black Spot CSV",
        "expected": {"blackspots.csv", "blackspots_2024.csv", "blackspots_2025.csv"},
        "patterns": ["blackspots*.csv"],
        "purpose": "HighwayBlackSpot import (8,862 records, ~15% GPS)",
        "required": True,
        "importer": "morth_blackspots_importer.py",
        "target_model": "HighwayBlackSpot",
    },
    "opencity": {
        "label": "OpenCity MoRTH Accident CSVs",
        "expected": {
            "state_wise.csv",
            "type_of_collision.csv",
            "type_of_violation.csv",
            "road_classification.csv",
            "vehicle_type.csv",
        },
        "patterns": ["*.csv"],
        "purpose": "AccidentRecord import (aggregated per-dimension tables)",
        "required": False,
        "importer": "morth_accidents_importer.py",
        "target_model": "AccidentRecord",
    },
    "morth": {
        "label": "MoRTH Road Accidents in India",
        "expected": set(),
        "patterns": ["RAI_*.pdf", "RAI_*.csv", "RAI_*.xlsx"],
        "purpose": "AccidentRecord import (state/UT aggregate tables)",
        "required": False,
        "importer": "morth_accidents_importer.py",
        "target_model": "AccidentRecord",
    },
    "state": {
        "label": "State-level Police / Department Data",
        "expected": set(),
        "patterns": ["*.csv", "*.xlsx"],
        "purpose": "AccidentRecord import (individual FIR records)",
        "required": False,
        "importer": "morth_accidents_importer.py",
        "target_model": "AccidentRecord",
    },
    "osm": {
        "label": "OpenStreetMap Exports",
        "expected": set(),
        "patterns": ["*.osm", "*.osm.pbf", "*.geojson"],
        "purpose": "Road centerline construction for chainage->lat/lon resolution",
        "required": False,
        "importer": "build_road_centerline/build_centerline.py (not yet implemented)",
        "target_model": "Road centerline DB (separate from SQLAlchemy models)",
    },
    "irad": {
        "label": "iRAD / e-DAR Exports",
        "expected": set(),
        "patterns": ["*.csv", "*.json"],
        "purpose": "AccidentRecord import (individual FIR records with GPS coordinates)",
        "required": False,
        "importer": "edar_importer.py (not yet implemented)",
        "target_model": "AccidentRecord",
    },
}


# Import order for ETL pipeline
IMPORT_ORDER = [
    (1, "dataful", "morth_blackspots_importer.py", "HighwayBlackSpot"),
    (2, "opencity", "morth_accidents_importer.py", "AccidentRecord"),
    (3, "morth", "morth_accidents_importer.py", "AccidentRecord"),
    (4, "state", "morth_accidents_importer.py", "AccidentRecord"),
    (5, "irad", "edar_importer.py (not yet implemented)", "AccidentRecord"),
]

POST_IMPORT_STEPS = [
    (6, "cluster_blackspots.py", "Generate HighwayBlackSpot from AccidentRecord clusters"),
    (7, "compute_segment_risk.py", "Build RoadSegmentRisk from HighwayBlackSpot + AccidentRecord"),
    (8, "osm", "Build road centerline DB for chainage->lat/lon resolution"),
]


def fmt_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


def fmt_path(abspath: str) -> str:
    """Shorten an absolute path to be relative to the project root."""
    try:
        return os.path.relpath(abspath, PROJECT_ROOT)
    except ValueError:
        return abspath


def scan_raw_subdir(source_key: str) -> dict:
    """Scan a single raw subdirectory and return file metadata."""
    subdir = os.path.join(RAW_DIR, source_key)
    if not os.path.isdir(subdir):
        return {"exists": False, "files": []}

    entries = []
    for entry in os.scandir(subdir):
        if entry.is_file() and not entry.name.startswith("."):
            entries.append({
                "name": entry.name,
                "size": entry.stat().st_size,
                "mtime": datetime.fromtimestamp(entry.stat().st_mtime),
            })
    entries.sort(key=lambda f: f["name"])
    return {"exists": True, "files": entries}


def match_patterns(filename: str, patterns: list) -> bool:
    """Check if a filename matches any of the given glob patterns."""
    return any(fnmatch.fnmatch(filename, pat) for pat in patterns)


def print_header(text: str, char: str = "=", width: int = 72):
    print(f"\n{text}")
    print(char * width)


def print_subheader(text: str):
    print(f"\n  {text}")
    print(f"  {'-' * min(len(text), 70)}")


def main():
    parser = argparse.ArgumentParser(
        description="SafeRoute AI — Dataset Verification Tool"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show per-file details"
    )
    args = parser.parse_args()

    # Verify base directories
    if not os.path.isdir(DATA_DIR):
        print(f"[FAIL] Data directory not found: {DATA_DIR}")
        print("       Create it with: mkdir -p data/raw/{opencity,morth,dataful,state,osm,irad}")
        sys.exit(1)

    for subdir in SOURCE_SPEC:
        os.makedirs(os.path.join(RAW_DIR, subdir), exist_ok=True)

    # Scan each source directory
    scan_results = {}
    for key in sorted(SOURCE_SPEC):
        scan_results[key] = scan_raw_subdir(key)

    # SECTION 1 — Source Directory Overview
    print_header("Source Directory Overview")
    print(f"{'Source':<14} {'Files':>6} {'Size':>10}  Status")
    print(f"{'':-<14} {'':->6} {'':->10}  {'':->20}")

    total_files = 0
    total_size = 0
    any_required_missing = False
    missing_required = []

    for key in sorted(SOURCE_SPEC):
        spec = SOURCE_SPEC[key]
        result = scan_results[key]
        if not result["exists"]:
            status = "[!!] MISSING DIR"
            any_required_missing = True
            missing_required.append(key)
            n = 0
            sz = 0
        else:
            files = result["files"]
            n = len(files)
            sz = sum(f["size"] for f in files)

            expected_names = spec["expected"]
            if expected_names:
                found_expected = {f["name"] for f in files} & expected_names
                if spec["required"]:
                    if found_expected:
                        status = "[OK]"
                    else:
                        status = "[MISSING expected file(s)]"
                        any_required_missing = True
                        missing_required.append(key)
                else:
                    status = f"[OK] {len(found_expected)}/{len(expected_names)} expected"
            else:
                if n > 0:
                    status = f"[OK] {n} file(s)"
                else:
                    status = "(empty)"

        total_files += n
        total_size += sz
        print(f"{key:<14} {n:>6} {fmt_size(sz):>10}  {status}")

    print(f"{'':-<14} {'':->6} {'':->10}  {'':->20}")
    print(f"{'TOTAL':<14} {total_files:>6} {fmt_size(total_size):>10}")

    # SECTION 2 — Expected vs Actual (per source)
    print_header("Expected File Check")
    all_expected_found = True

    for key in sorted(SOURCE_SPEC):
        spec = SOURCE_SPEC[key]
        result = scan_results[key]
        expected = spec["expected"]
        if not expected:
            continue

        actual_names = {f["name"] for f in result["files"]} if result["exists"] else set()
        found = actual_names & expected
        missing = expected - actual_names
        extra = actual_names - expected

        label = f"{key}/{spec['label']}"
        print(f"\n  {label}")
        print(f"  {'-' * len(label)}")

        for fname in sorted(expected):
            status = "[OK]" if fname in found else "[X] MISSING"
            print(f"    [{status}] {fname}")

        if extra and args.verbose:
            print(f"\n    Unexpected files ({len(extra)}):")
            for fname in sorted(extra):
                print(f"      {fname}")

        if missing:
            all_expected_found = False

    if all_expected_found:
        print("\n  All expected files accounted for.")

    # SECTION 3 — Duplicate Filename Detection
    print_header("Duplicate Filename Check")
    name_to_dirs = defaultdict(list)
    for key in sorted(SOURCE_SPEC):
        result = scan_results[key]
        if result["exists"]:
            for f in result["files"]:
                name_to_dirs[f["name"]].append(key)

    duplicates_found = False
    for fname, dirs in sorted(name_to_dirs.items()):
        if len(dirs) > 1:
            duplicates_found = True
            print(f"  [!!] \"{fname}\" appears in: {', '.join(dirs)}")
            print(f"    Imports may fail if both directories are used. Archive or rename.")

    if not duplicates_found:
        print("  No duplicate filenames across source directories.")

    # SECTION 4 — File Type Breakdown
    print_header("File Type Breakdown")
    ext_counts = defaultdict(int)
    ext_sizes = defaultdict(int)
    for key in sorted(SOURCE_SPEC):
        result = scan_results[key]
        if result["exists"]:
            for f in result["files"]:
                ext = os.path.splitext(f["name"])[1].lower() or "(no ext)"
                ext_counts[ext] += 1
                ext_sizes[ext] += f["size"]

    if ext_counts:
        print(f"{'Extension':<14} {'Count':>6} {'Total Size':>10}")
        print(f"{'':-<14} {'':->6} {'':->10}")
        for ext in sorted(ext_counts, key=lambda e: -ext_sizes[e]):
            print(f"{ext:<14} {ext_counts[ext]:>6} {fmt_size(ext_sizes[ext]):>10}")
    else:
        print("  No files found.")

    # SECTION 5 — Detailed File Listing (verbose only)
    if args.verbose:
        print_header("Per-File Details (--verbose)")
        for key in sorted(SOURCE_SPEC):
            spec = SOURCE_SPEC[key]
            result = scan_results[key]
            if result["exists"] and result["files"]:
                print(f"\n  {key}/ — {spec['label']}")
                max_name = max(len(f["name"]) for f in result["files"])
                for f in result["files"]:
                    print(f"    {f['name']:<{max_name}}  {fmt_size(f['size']):>8}  {f['mtime']:%Y-%m-%d %H:%M}")

    # SECTION 6 — Recommended Import Order
    print_header("Recommended Import Order")
    print(f"{'#':>2} {'Source':<12} {'Importer':<40} {'Target Model':<20}")
    print(f"{'':->2} {'':->12} {'':->40} {'':->20}")

    for step, key, importer, model in IMPORT_ORDER:
        result = scan_results[key]
        has_data = result["exists"] and len(result["files"]) > 0
        status = "[OK]" if has_data else "(no data)"
        print(f" {step:>1}  {key:<12} {importer:<40} {model:<20}  [{status}]")

    print()
    print("  Post-import steps (after data is loaded):")
    for step, script, desc in POST_IMPORT_STEPS:
        print(f"  {step:>1}. {script:<40} {desc}")

    print()
    print(f"  Running order: dataful -> opencity/morth/state -> irad -> cluster -> compute_segment_risk")

    # SECTION 7 — Validation Summary
    print_header("Validation Summary")

    if total_files == 0:
        summary_status = "[!!] NO DATASETS FOUND"
        summary_mark = "FAIL"
        exit_code = 1
    elif any_required_missing:
        summary_status = f"[!!] {len(missing_required)} required source(s) missing: {', '.join(missing_required)}"
        summary_mark = "WARN"
        exit_code = 1
    elif not all_expected_found:
        summary_status = "[!!] Some expected files missing (non-required sources)"
        summary_mark = "PASS"
        exit_code = 0
    else:
        summary_status = "All required datasets present"
        summary_mark = "PASS"
        exit_code = 0

    print(f"  Result:       [{summary_mark}]")
    print(f"  Status:       {summary_status}")
    print(f"  Sources:      {sum(1 for k in SOURCE_SPEC if scan_results[k]['exists'])}/{len(SOURCE_SPEC)} present")
    print(f"  Total files:  {total_files}")
    print(f"  Total size:   {fmt_size(total_size)}")
    print(f"  Data dir:     {fmt_path(DATA_DIR)}")

    print()
    print(f"  Legend:")
    print(f"    [OK]  file found / source has data")
    print(f"    [X]   expected file missing")
    print(f"    [!!]  warning (non-fatal)")
    print(f"    (empty)  directory exists but is empty")
    print(f"  For detailed checks: run 'python {__file__} --verbose'")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()