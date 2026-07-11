# Black Spot Ingestion Plan — Dataful CSV → HighwayBlackSpot

## Overview

This document defines the ingestion pipeline for the Dataful MoRTH Black Spot Dataset
into the `HighwayBlackSpot` table. It covers transformation logic, failure handling,
confidence scoring, and the importer class design for implementation.

```
Dataful CSV (8,862 rows)
        │
        ▼
   raw location text ──────────────────────────────────────┐
        │                                                  │
        ▼                                                  │
   chainage extraction  ◄── parse_chainage()               │
        │                                                  │
        ▼                                                  │
   NH matching ◄────────── extract_highway_from_id()       │
        │                                                  │
        ▼                                                  │
   lat/lon generation ◄─── road centerline DB (OSM)        │
        │                                                  │
        ▼                                                  │
   HighwayBlackSpot ──────── 3 outcomes: INSERT / UPDATE / SKIP
```

---

## 1. Dataful CSV Ingestion Flow

### 1.1 Pipeline Stages

```
┌──────────────┐
│  Stage 0     │  Download CSV from dataful.in/datasets/21559/
│  Acquisition │  Manual or automated (curl/wget). Expected ~3MB.
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Stage 1     │  Read CSV rows with pandas (chunked, batch_size=1000)
│  Read        │  Expected: 20 columns, 8,862 rows
└──────┬───────┘       Reject rows where ALL key fields are empty
       │                (black_spot_id + location + state all empty → skip)
       ▼
┌──────────────┐
│  Stage 2     │  Per-row normalization pipeline:
│  Normalize   │    a. Clean whitespace, standardize state names
│              │    b. Parse chainage from location → (start_km, end_km)
│              │    c. Extract highway_number from black_spot_id
│              │    d. Generate lat/lon from chainage (or keep CSV value)
│              │    e. Map final_repair_status → investigation_status
│              │    f. Infer severity from accident/fatality counts
│              │    g. Compute confidence_score
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Stage 3     │  For each normalized record:
│  Dedup       │    a. Query HighwayBlackSpot by official_id
│              │    b. If found: compare data freshness
│              │       - Newer record → UPDATE
│              │       - Older record → SKIP
│              │    c. If not found: INSERT
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Stage 4     │  bulk_insert in batches of 500
│  Commit      │  Commit after each batch
│              │  Report: inserted, updated, skipped, errors
└──────────────┘
```

### 1.2 Data Path per Record

| Input | → | Stage 2 (Normalize) | → | Stage 3 (Dedup) | → | Output |
|-------|---|---------------------|---|-----------------|---|--------|
| `black_spot_id` | | `official_id = "AP-(02)-NH16-60"` | | Query by `official_id` | | INSERT / UPDATE |
| `state` | | `state = "Andhra Pradesh"` | | — | | HighwayBlackSpot.state |
| `district` | | `district = "Krishna"` | | — | | HighwayBlackSpot.district |
| `agency` | | `managed_by = "NHAI"` | | — | | HighwayBlackSpot.managed_by |
| `location` | | `chainage_start_km = 120.0`, `chainage_end_km = 120.5`, `location_text = "120+0 to 120+500"` | | — | | HighwayBlackSpot.chainage_start_km, .chainage_end_km |
| `black_spot_id` | | `highway_number = "NH-16"` | | — | | HighwayBlackSpot.highway_number |
| (chainage) | | `latitude = 28.6129`, `longitude = 77.2295` | | — | | HighwayBlackSpot.latitude, .longitude |
| `final_repair_status` | | `investigation_status = "RECTIFIED"` | | — | | HighwayBlackSpot.description (embedded) |
| — | | `severity = MEDIUM` (default until real counts) | | — | | HighwayBlackSpot.severity |
| — | | `confidence_score = 0.3 (chainage)` / `0.7 (GPS)` | | — | | HighwayBlackSpot.confidence_score |

---

## 2. Expected Raw Schema

### 2.1 Column Reference (Dataful Export)

| # | Column Name | Type | Example | Nullable | Notes |
|---|-------------|------|---------|----------|-------|
| 1 | `data_as_on` | date | `2024-03-31` | Yes | Snapshot date |
| 2 | `agency` | string | `NHAI` | No | One of 5 canonical values |
| 3 | `managed_by` | string | `RO, Vijayawada` | Yes | Road office name (286 distinct) |
| 4 | `state` | string | `Andhra Pradesh` | No | State/UT name |
| 5 | `district` | string | `Krishna` | No | District name |
| 6 | `black_spot_id` | string | `AP-(02)-NH16-60` | No | Primary key in MoRTH system |
| 7 | `location` | string | `175+300 to 175+800` | Yes | Chainage range (primary location reference) |
| 8 | `police_station` | string | `Gollapudi PS` | Yes | Jurisdiction |
| 9 | `latitude` | float | `28.6129` | Yes | GPS coordinate (rarely populated) |
| 10 | `longitude` | float | `77.2295` | Yes | GPS coordinate (rarely populated) |
| 11 | `repair_start_date` | date | `2022-03-15` | Yes | When repair work began |
| 12 | `repair_end_date` | date | `2022-06-20` | Yes | When repair work ended |
| 13 | `repair_details` | string | `Providing crash barrier and signage at km 120` | Yes | Free text (up to ~500 chars) |
| 14 | `temporary_repair_status` | string | `Completed` | Yes | Status of temporary works |
| 15 | `final_repair_status` | string | `Already Rectified` | Yes | One of 4 canonical statuses |

### 2.2 `final_repair_status` Canonical Values

| Status | Meaning | Ingestion Action |
|--------|---------|-----------------|
| `Already Rectified` | Engineering fix completed | Record → `investigation_status = "RECTIFIED"`. Still inserted into DB (historical record). |
| `Under Sanction / Investigation` | Under design/approval | Record → `investigation_status = "UNDER_INVESTIGATION"`. Inserted normally. |
| `In Progress` | Repair work underway | Record → `investigation_status = "IN_PROGRESS"`. Inserted normally. |
| (empty) | Not yet assigned | Record → `investigation_status = "UNKNOWN"`. Inserted with lower confidence. |

### 2.3 `agency` Canonical Values

| Agency | Count (approx) | managed_by |
|--------|---------------|------------|
| `NHAI` | 3,996 | `NHAI` |
| `MoRTH` / `PWD NH` | 4,139 | `MoRTH` |
| `NHIDCL` | 84 | `NHIDCL` |
| `BRO` | 18 | `BRO` |
| `State PWD` / `Other` | 645 | `State PWD` |

### 2.4 `black_spot_id` ID Format

The `black_spot_id` encodes state, district, highway, and serial number:

```
  AP   -  02     -  NH16  -  60
  │        │         │       │
  │        │         │       └── serial number (60th spot)
  │        │         └────────── highway (NH-16)
  │        └──────────────────── district code (02 = Krishna)
  └───────────────────────────── state code (AP = Andhra Pradesh)
```

This encoding lets us extract `highway_number` via regex without a lookup table.

---

## 3. Transformation Steps

### 3.1 Step A: Raw Location Text → Chainage (km)

#### Input
```
"175+300 to 175+800"   ← most common
"138+600"              ← single point (treat as range of 0)
"282/0 to 282/5"       ← hundreds-of-meters format
"23/.4"                ← dotted format (normalize before parse)
"NH-16 km 120"         ← unstructured text (fallback parse)
```

#### Chainage Format Parsing

| Format | Regex | Example | → start_km | end_km |
|--------|-------|---------|------------|--------|
| `X+YYY to X+YYY` | `(\d+)\+(\d+)\s*to\s*(\d+)\+(\d+)` | `175+300 to 175+800` | 175.300 | 175.800 |
| `X+YYY` (single) | `(\d+)\+(\d+)$` | `138+600` | 138.600 | 138.600 |
| `X/Y to X/Y` | `(\d+)/(\d+)\s*to\s*(\d+)/(\d+)` | `282/0 to 282/5` | 282.000 | 282.500 |
| `X/Y` (single) | `(\d+)/(\d+)$` | `23/4` | 23.400 | 23.400 |
| `X/.Y` (dotted) | Normalize `/.` → `/` first, then use `/` format | `23/.4` | 23.400 | 23.400 |
| `X to Y` (plain) | `(\d+\.?\d*)\s*to\s*(\d+\.?\d*)` | `23 to 24` | 23.000 | 24.000 |

#### Sub-unit Parsing Rule

The `_to_km()` helper distinguishes meters vs hundreds-of-meters:

```python
def _to_km(km_part, sub_part):
    km = float(km_part)
    val = float(sub_part)
    if len(sub_part) <= 2:
        km += val / 10.0    # X/Y format: Y is 0.0–0.9 km
    else:
        km += val / 1000.0  # X+YYY format: YYY is 0–999 meters
    return km
```

#### Output
```python
{
    "chainage_start_km": 175.3,    # float
    "chainage_end_km": 175.8,      # float (same as start if single point)
    "location_text": "175+300 to 175+800",  # original raw text preserved
}
```

#### Failure: Non-parseable Text

If the location field does not match any known format:
- Log a warning with the raw text
- Set `chainage_start_km = None`, `chainage_end_km = None`
- Try geocoding via `police_station` + `state` as last resort
- If no geocoding result → skip the record (requires lat/lon)

### 3.2 Step B: Chainage → lat/lon

#### Without Road Centerline DB

Currently `chainage_to_latlon()` returns `None`. For chainage-only records,
lat/lon stays NULL and the record is **skipped** (latitude and longitude are
required fields in `HighwayBlackSpot`).

**Estimated impact:** ~90% of Dataful records lack GPS coordinates, so ~7,900
records would be skipped without a centerline DB.

#### With Road Centerline DB (Future)

A road centerline database must be built from OSM way geometries for Indian
National Highways and State Highways:

```
┌──────────────────────────────────────────┐
│  RoadCenterline(mode)                    │
│──────────────────────────────────────────│
│  SELECT way_lat, way_lon                 │
│  FROM road_centerlines                   │
│  WHERE highway_number = 'NH-16'          │
│    AND chainage_start <= :km             │
│    AND chainage_end > :km                │
│  ORDER BY ABS(chainage_midpoint - :km)   │
│  LIMIT 1                                 │
└──────────────────────────────────────────┘
```

**Chainage→lat/lon algorithm:**
1. Find the road centerline for `(highway_number, chainage_km)`
2. Interpolate position along the centerline way geometry at the given km marker
3. Return interpolated (lat, lon)

**Fallback strategy:**
- If centerline DB does not cover this highway → skip record
- If centerline DB covers but chainage is out of range → use nearest endpoint
- Log all geocoding failures for manual review

**Confidence after geocoding:**
- GPS-provided (from CSV `latitude`/`longitude`): `0.7`
- Chainage→centerline interpolation: `0.5` (depends on OSM data quality)
- Manual/inferred from police_station name: `0.2`

#### Without Centerline DB — Partial Workaround

A simple heuristic can handle **some** records without a full centerline DB:

```python
def estimate_latlon_from_district(highway_number, chainage_km, state, district):
    """
    Use known highway bounding boxes to estimate approximate position.
    For NH-44 in Delhi NCR: lat ≈ 28.4 + chainage/111
    This is very approximate (±50km) but better than skipping entirely.
    """
```

This is not recommended for production. The centerline DB should be built first.

### 3.3 Step C: NH Matching (Highway Number Extraction)

#### From `black_spot_id`

The `black_spot_id` contains the highway number in a predictable position:

```python
# Pattern: "XX-##-NH##-##" → extract "NH-16"
# Example: "AP-02-NH16-60" → "NH-16"
import re
m = re.search(r'NH\s*(\d+)', black_spot_id, re.IGNORECASE)
if m:
    highway_number = f"NH-{m.group(1)}"
```

This works for NHAI and MoRTH PWD records (~8,000 of 8,862). For NHIDCL and
BRO records, the format may differ and require separate rules.

#### From `road_name` (if available)

Some CSV rows have a `road_name` field. If `highway_number` extraction from ID
fails, fall back to scanning `road_name` for patterns like `"NH-44"`, `"NH 16"`,
etc.

#### Output

```python
{
    "highway_number": "NH-16",      # string or None if cannot determine
    "geometry_resolution": "Chainage",  # "GPS", "Chainage", "Manual"
}
```

### 3.4 Step D: Final Record Assembly

```python
{
    # Required spatial fields
    "latitude": 28.6129,
    "longitude": 77.2295,
    "radius": 250.0,               # Half of 500m MoRTH definition
    "geometry_resolution": "Chainage",

    # Identification
    "official_id": "AP-(02)-NH16-60",
    "state": "Andhra Pradesh",
    "district": "Krishna",
    "highway_number": "NH-16",
    "managed_by": "NHAI",
    "road_name": "NH-16",
    "location_text": "175+300 to 175+800",

    # Severity & counts (inferred)
    "severity": BlackSpotSeverity.MEDIUM,
    "accident_count": 0,            # 0 until clustering provides real counts
    "fatalities": 0,                # 0 until clustering provides real counts

    # Temporal
    "last_accident_date": None,     # None until clustering links AccidentRecords
    "updated_at": datetime.utcnow(),

    # Provenance
    "source": "MoRTH",
    "source_name": "Dataful MoRTH Black Spot Dataset",
    "source_url": "https://dataful.in/datasets/21559/",
    "confidence_score": 0.5,        # chainage-geocoded

    # Repair tracking (stored in description until dedicated column exists)
    "description": "Repair: Under Sanction / Investigation. Location: 175+300 to 175+800",
}
```

---

## 4. Failure Handling

### 4.1 Missing Chainage

**Scenario:** Row has `black_spot_id` and `state` but `location` is empty.

| Severity | Frequency (est.) | Action |
|----------|-----------------|--------|
| Rare | ~1% of records (<100 rows) | Log warning → skip row |

**Recovery options:**
1. If `police_station` + `district` are available, attempt reverse geocoding via
   Nominatim (query: `"Gollapudi PS, Krishna, Andhra Pradesh"`)
2. If geocoding succeeds → use returned lat/lon, set `confidence_score = 0.2`,
   `geometry_resolution = "Manual"`
3. If geocoding fails → skip (return `None` from row parser)

### 4.2 Duplicate Spots

**Scenario:** Same `black_spot_id` appears in multiple CSV snapshots (the dataset
is updated quarterly, and re-imports will encounter existing records).

**Dedup decision matrix:**

| Existing Record | Incoming Record | Action |
|-----------------|-----------------|--------|
| Not found | Any | `INSERT` |
| `official_id` match, identical data | Any | `SKIP` (no change) |
| `official_id` match, same `updated_at` | Different data | `UPDATE` (overwrite with incoming) |
| `official_id` match, newer `updated_at` | Older data | `SKIP` (existing is fresher) |
| `official_id` match, older `updated_at` | Newer data | `UPDATE` (replace with incoming) |

**Timestamp comparison:**
- Compare `data_as_on` (snapshot date from CSV) against `updated_at` (DB field)
- If CSV's `data_as_on` > DB's `updated_at` → update

**Coordinate dedup (fallback when official_id is missing):**
- Query by lat/lon within 0.001° (~100m) tolerance
- If any matching record found with same `highway_number` → update instead of insert

### 4.3 Repaired Spots

**Scenario:** Record has `final_repair_status = "Already Rectified"`.

| Treatment | Detail |
|-----------|--------|
| **Still insert** | A repaired black spot is still a known hazard location. Past accident data is valuable even if repaired. |
| **Severity markdown** | Mark `severity` as LOW if the spot has been rectified (road geometry still matters). |
| **Retain in DB** | Do not delete. The routing engine should weigh repaired spots lower but not ignore them. |
| **Confidence boost** | `+0.1` confidence for records with any repair tracking (validates data freshness). |

**Routing integration note** (future, not yet implemented):
- `last_repair_date` can be used in penalty calculation: more recent repair → lower penalty
- A `RECTIFIED` status can be stored in `description` for now, or in a future `investigation_status` column

### 4.4 Foreign Key Gaps (Agency Not Mapped)

**Scenario:** `agency` value does not match any canonical `managed_by` value.

| Severity | Frequency | Action |
|----------|-----------|--------|
| Low | ~3% (new agencies) | Log warning → set `managed_by = "Other"` |

**Canonical mapping:**
```python
AGENCY_MAP = {
    "NHAI": "NHAI",
    "MoRTH": "MoRTH", "MORTH": "MoRTH", "PWD NH": "MoRTH",
    "NHIDCL": "NHIDCL",
    "BRO": "BRO", "Border Roads": "BRO",
    "State PWD": "State PWD", "PWD": "State PWD",
    # All others → "Other"
}
```

### 4.5 Summary: Record Disposition Flow

```
                        ┌──────────────────────┐
                        │  Raw CSV row          │
                        └──────────┬───────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  Has black_spot_id?       │
                    └──────┬──────────┬────────┘
                       NO  │          │ YES
                           ▼          ▼
                    ┌──────────┐  ┌──────────────────┐
                    │  SKIP    │  │  Has location     │
                    │ (no key) │  │  or lat/lon?      │
                    └──────────┘  └─────┬──────┬─────┘
                                    NO  │      │ YES
                                        ▼      ▼
                                 ┌────────┐  ┌──────────────────┐
                                 │ SKIP   │  │  Parse chainage   │
                                 │(no geo)│  │  → lat/lon OK?    │
                                 └────────┘  └─────┬──────┬─────┘
                                               NO  │      │ YES
                                                   ▼      ▼
                                            ┌────────┐  ┌──────────────────┐
                                            │ SKIP   │  │  Dedup by ID     │
                                            │(no geo)│  │  → found?        │
                                            └────────┘  └─────┬──────┬─────┘
                                                           NO  │      │ YES
                                                               ▼      ▼
                                                        ┌────────┐  ┌──────────────┐
                                                        │ INSERT │  │ UPDATE or SKIP│
                                                        │        │  │ (by freshness)│
                                                        └────────┘  └──────────────┘

Expected outcomes (est.):
  INSERT  ~5,000 (chainage→lat/lon via centerline)
  UPDATE  ~3,000 (quarterly snapshot refresh)
  SKIP      ~800 (missing geo, duplicate data)
  ERROR     ~62  (~0.7% — malformed rows, DB constraints)
```

---

## 5. Confidence Scoring

### 5.1 Per-Record Confidence

The `confidence_score` field (0.0–1.0) captures how reliable each record is:

| Factor | GPS | Centerline | Manual | Weight |
|--------|-----|-----------|--------|--------|
| Geometry resolution | `0.9` (GPS) | `0.6` (Chainage→interpolated) | `0.2` (Police station geocoded) | 0.40 |
| Has official_id | `0.9` (yes) | `0.0` (no) | — | 0.20 |
| Has severity | `0.8` (inferred from counts) | `0.5` (default MEDIUM) | — | 0.15 |
| Has repair tracking | `0.9` (all statuses) | `0.7` (partial) | `0.3` (no repair data) | 0.10 |
| Source freshness | `0.9` (< 6 months old) | `0.6` (6–24 months) | `0.3` (> 24 months) | 0.10 |
| Has police_station | `0.2` bonus | — | — | 0.05 |

**Composite formula:**
```python
score = sum(weight * factor_value for each factor)

# Penalty for missing data:
if geometry_resolution == "Manual":
    score *= 0.8  # 20% penalty for manual geocoding
if severity == BlackSpotSeverity.LOW and not accident_count:
    score *= 0.8  # Unsure about low severity if no data
```

### 5.2 Deterministic Scoring Table

| Scenario | geometry_resolution | has official_id | has repair_status | confidence_score |
|----------|--------------------|----------------|-------------------|------------------|
| Full GPS, all fields | GPS | Yes | Yes | 0.85 |
| GPS, minimal metadata | GPS | No | No | 0.40 |
| Chainage→centerline, full fields | Chainage | Yes | Yes | 0.60 |
| Chainage→centerline, minimal | Chainage | No | No | 0.30 |
| Manual geocode, full fields | Manual | Yes | Yes | 0.35 |
| Manual geocode, minimal | Manual | No | No | 0.15 |

### 5.3 Batch-Level Confidence

| Metric | Value |
|--------|-------|
| Mean per-record score | ~0.50 (majority chainage→centerline) |
| Std dev | ~0.20 |
| Records with score ≥ 0.7 | ~15% (only GPS records) |
| Records with score ≥ 0.5 | ~60% (centerline+official_id) |
| Records with score < 0.3 | ~25% (manual/minimal) |

Records with `confidence_score < 0.2` should be flagged for manual review but
still inserted (more data is better than no data, with appropriate low weight).

---

## 6. Future Importer Class Design

### 6.1 Class Hierarchy

```
BaseAccidentImporter                        (base_importer.py)
├── MoRTHBlackspotsImporter                 (morth_blackspots_importer.py)
│   ├── parse_csv_row()                     ← main row processor
│   ├── parse_repair_status()               ← status normalization
│   └── infer_severity()                    ← fallback severity
│
├── NHAIBlackspotsImporter                  (nhai_blackspots_importer.py)
│   ├── extract_highway_from_id()           ← NHAI ID parsing
│   └── run()                               ← NHAI-specific CSV reader
│
├── MoRTHAccidentsImporter                 (morth_accidents_importer.py)
│   └── run()                               ← OpenCity CSV → AccidentRecord
│
├── EDARImporter                           (edar_importer.py)
│   └── run()                               ← iRAD/e-DAR API → AccidentRecord
│
├── BlackSpotClusterer                      (cluster_blackspots.py)
│   ├── qualifies_as_blackspot()            ← MoRTH definition check
│   ├── compute_centroid()                  ← lat/lon from record list
│   └── cluster_by_highway()               ← sliding window algorithm
│
└── SegmentRiskComputer                    (compute_segment_risk.py)
    └── run()                               ← batch RoadSegmentRisk computation
```

### 6.2 MoRTHBlackspotsImporter — Key Methods

```
MoRTHBlackspotsImporter
├── __init__(db_path: str = None)
│   └── Initialize DB connection, batch tracking counters
│
├── run(filepath: str) → Dict[str, int]
│   ├── Stage 1: Read CSV into pandas DataFrame (chunked, 1000 rows)
│   ├── Stage 2: For each row, call parse_csv_row()
│   │   ├── On success → append to insert buffer
│   │   └── On None → increment skipped counter
│   ├── Stage 3: Dedup buffer by official_id (UPSERT logic)
│   ├── Stage 4: bulk_insert in batches of 500
│   └── Return {"inserted": N, "updated": M, "skipped": K, "errors": E}
│
├── parse_csv_row(row: Dict) → Optional[Dict]
│   ├── Extract chainage via parse_chainage()
│   ├── Resolve lat/lon via chainage_to_latlon() or CSV coordinates
│   ├── Extract highway_number via regex on black_spot_id
│   ├── Map repair_status to investigation_status
│   ├── Compute scalar confidence_score
│   └── Return assembled dict or None (if critical fields missing)
│
├── parse_repair_status(status: str) → str
│   └── Map "Already Rectified" → "RECTIFIED", empty → "UNKNOWN", etc.
│
├── infer_severity(accident_count: int, fatalities: int) → BlackSpotSeverity
│   └── ≥10 fatalities → HIGH, ≥5 accidents → MEDIUM, else LOW
│
├── compute_confidence(row: Dict) → float
│   ├── Evaluate geometry_resolution, official_id, repair_status, freshness
│   └── Return weighted score per section 5 formula
│
├── dedup_buffer(buffer: List[Dict]) → List[Dict]
│   ├── Query DB for existing official_id values in buffer
│   ├── Match incoming vs existing by updated_at
│   └── Return list of records ready for INSERT (including UPDATE payloads)
│
└── chainage_to_latlon(highway: str, km: float) → Optional[Tuple[float, float]]
    └── Query OSM road centerline for highway at chainage → interpolate
```

### 6.3 Base Class Shared Utilities (already in base_importer.py)

| Method | Purpose | Status |
|--------|---------|--------|
| `get_session()` / `close_session()` | DB session lifecycle | ✅ Working |
| `parse_chainage(str)` → `(float, float)` | Chainage parser (X+YYY, X/Y, X to Y) | ✅ Working |
| `chainage_to_latlon(str, float)` → `(float, float)` | Road centerline lookup | ❌ Stub (returns None) |
| `dedup_by_official_id(session, model, field, value)` → `Optional[object]` | Dedup by ID | ✅ Working |
| `dedup_by_coordinate(session, model, lat, lon, tol)` → `List[object]` | Spatial dedup | ✅ Working |
| `bulk_insert(session, records, batch_size)` → `int` | Batch insert with commit | ✅ Working |
| `bulk_update(session, records)` → `int` | Batch update commit | ✅ Working |

### 6.4 Road Centerline DB Integration (Future)

The `chainage_to_latlon()` stub is the single blocking dependency for the
Dataful import. Two implementation options:

| Option | Approach | Effort | Quality |
|--------|----------|--------|---------|
| **A** | Extract NH geometries from Geofabrik India OSM PBF, build SQLite with (highway_number, chainage_km, lat, lon) | 2–3 days | High (±100m) |
| **B** | Query Overpass API per record for NH way geometry, interpolate on-the-fly | High latency | Best (±10m) but rate-limited |
| **C** | Manual bounding-box approximation per NH + chainage (linear interpolation) | 1 day | Low (±5km) |

**Recommendation:** Option A (pre-extract NH geometries from Geofabrik India
extract). This avoids Overpass API rate limits and provides reliable chainage
interpolation for ~90% of records.

### 6.5 Running the Importer

```bash
# Once road centerline DB is available:
cd backend

# Dry run (log only, no writes):
python -m scripts.data_ingestion.morth_blackspots_importer \
    --filepath data/blackspots_2024.csv \
    --dry-run

# Full import:
python -m scripts.data_ingestion.morth_blackspots_importer \
    --filepath data/blackspots_2024.csv \
    --batch-size 500 \
    --upsert

# Restartable: already-imported records with matching official_id
# are skipped (or updated if --upsert is passed).
```

**Logging format per run:**
```
[2026-06-27 20:15:00] INFO  | read 8,862 rows from blackspots_2024.csv
[2026-06-27 20:15:03] INFO  | normalize phase: 8,862 rows processed
[2026-06-27 20:15:03] WARN  |   chainage parse failed: 62 rows → skipped
[2026-06-27 20:15:03] WARN  |   lat/lon resolution failed: 800 rows → skipped
[2026-06-27 20:15:04] INFO  | dedup phase: 8,000 candidates
[2026-06-27 20:15:04] INFO  |   INSERT: 5,000 new records
[2026-06-27 20:15:04] INFO  |   UPDATE: 3,000 existing records refreshed
[2026-06-27 20:15:04] INFO  | commit phase: 8 batches × 500 records
[2026-06-27 20:15:05] INFO  | done. inserted=5000 updated=3000 skipped=862 errors=0
```

---

## 7. Reference: Field Mapping (CSV → Model)

```
Dataful CSV column             HighwayBlackSpot field       Notes
─────────────────────────      ──────────────────────       ─────
black_spot_id             →    official_id                  Primary dedup key
state                     →    state                        Direct copy
district                  →    district                     Direct copy
agency                    →    managed_by                   Canonical mapping (5 values)
location                  →    chainage_start_km,           Parse via parse_chainage()
                               chainage_end_km,             
                               location_text                Raw text preserved
latitude / longitude      →    latitude, longitude          Use CSV if present, else derive
—                         →    geometry_resolution          "GPS" / "Chainage" / "Manual"
—                         →    highway_number               Extracted from black_spot_id
—                         →    severity                     Inferred from accident count
—                         →    accident_count               0 until clustering runs
—                         →    fatalities                   0 until clustering runs
final_repair_status       →    description (embedded)       Status stored in description text
repair_details            →    description (embedded)       Appended to description
—                         →    source                       "MoRTH"
—                         →    source_name                  "Dataful MoRTH Black Spot Dataset"
—                         →    source_url                   "https://dataful.in/datasets/21559/"
—                         →    confidence_score             Computed per section 5
—                         →    radius                       250.0 (half of 500m standard)
—                         →    last_accident_date           None until clustering
```

## 8. Appendices

### A. Format Examples for Chainage Parser Test Cases

| Input | Expected start_km | Expected end_km | Notes |
|-------|-------------------|-----------------|-------|
| `"175+300 to 175+800"` | 175.300 | 175.800 | Standard, YYY is meters |
| `"138+600"` | 138.600 | 138.600 | Single point |
| `"23/.0 to 23/.4"` | 23.000 | 23.400 | Dotted, normalize before parse |
| `"282/0 to 282/5"` | 282.000 | 282.500 | Hundreds-of-meters format |
| `"23 to 24"` | 23.000 | 24.000 | Plain km range |
| `"km 120 of NH-16"` | None | None | Unparseable |
| `""` | None | None | Empty |
| `None` | None | None | Null |

### B. Sample Row — Full Transformation

```
Input CSV row:
{
  "data_as_on": "2024-03-31",
  "agency": "NHAI",
  "managed_by": "RO, Vijayawada",
  "state": "Andhra Pradesh",
  "district": "Krishna",
  "black_spot_id": "AP-(02)-NH16-60",
  "location": "175+300 to 175+800",
  "police_station": "Gollapudi PS",
  "final_repair_status": "Under Sanction / Investigation"
}

After parse_csv_row():
{
  "official_id": "AP-(02)-NH16-60",
  "state": "Andhra Pradesh",
  "district": "Krishna",
  "managed_by": "NHAI",
  "highway_number": "NH-16",
  "chainage_start_km": 175.3,
  "chainage_end_km": 175.8,
  "location_text": "175+300 to 175+800",
  "latitude": 16.5523,          ← derived from centerline DB
  "longitude": 80.5217,         ← derived from centerline DB
  "geometry_resolution": "Chainage",
  "radius": 250.0,
  "severity": BlackSpotSeverity.MEDIUM,
  "accident_count": 0,
  "fatalities": 0,
  "last_accident_date": None,
  "source": "MoRTH",
  "source_name": "Dataful MoRTH Black Spot Dataset",
  "source_url": "https://dataful.in/datasets/21559/",
  "confidence_score": 0.5,       ← chainage-geocoded, official_id present
  "description": "Repair: Under Sanction / Investigation. Location: 175+300 to 175+800",
  "updated_at": datetime(2026, 6, 27, 20, 15, 0)
}
```
