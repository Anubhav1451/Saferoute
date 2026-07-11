# Chainage Resolution Design — Chainage→lat/lon Conversion Pipeline

## 1. Dataflow

```
                        Dataful CSV Row
                              │
                              ▼
                    ┌──────────────────────┐
                    │  raw CSV fields       │
                    │  location:            │
                    │   "175+300 to 175+800" │
                    │  black_spot_id:       │
                    │   "AP-(02)-NH16-60"    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  1. parse_chainage()  │
                    │  "175+300 to 175+800" │
                    │    → 175.3, 175.8     │
                    └──────────┬───────────┘
                               │
                    chainage_start_km = 175.3
                    chainage_end_km   = 175.8
                               │
                               ▼
                    ┌──────────────────────┐
                    │  2. Extract NH from   │
                    │     black_spot_id     │
                    │  "AP-(02)-NH16-60"    │
                    │    → "NH-16"          │
                    └──────────┬───────────┘
                               │
                    highway_number = "NH-16"
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │  3. Query road_centerlines DB     │
                    │                                   │
                    │  SELECT geometry, chainage_start  │
                    │  FROM road_centerlines            │
                    │  WHERE highway_number = 'NH-16'   │
                    │    AND state = 'Andhra Pradesh'   │
                    │    AND chainage_start <= 175.3    │
                    │    AND chainage_end >= 175.3      │
                    └──────────┬───────────────────────┘
                               │
                    returns: LineString geometry
                    returns: chainage_start = 0.0
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │  4. Compute target distance       │
                    │                                   │
                    │  target_m = (175.3 - 0.0) × 1000  │
                    │           = 175,300 meters        │
                    │                                   │
                    │  point = geometry.interpolate(    │
                    │      175300)                      │
                    │                                   │
                    │  → (16.5523, 80.5217)             │
                    └──────────┬───────────────────────┘
                               │
                    latitude = 16.5523
                    longitude = 80.5217
                               │
                               ▼
                    ┌──────────────────────────────────┐
                    │  5. Assemble HighwayBlackSpot     │
                    │                                   │
                    │  official_id: AP-(02)-NH16-60     │
                    │  latitude:      16.5523           │
                    │  longitude:     80.5217           │
                    │  chainage_start_km: 175.3         │
                    │  chainage_end_km:   175.8         │
                    │  highway_number:   NH-16          │
                    │  geometry_resolution: Chainage    │
                    │  confidence_score: 0.50           │
                    └──────────────────────────────────┘
```

### 1.1 End-to-End Flow Diagram

```
┌────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Dataful    │     │ MoRTHBlack-  │     │ HighwayBlackSpot │
│ CSV (8,862)│────▶│ spotsImporter│────▶│ (SQLite DB)      │
└────────────┘     └──────┬───────┘     └──────────────────┘
                          │
                          │ chainage_to_latlon('NH-16', 175.3)
                          │
                          ▼
                 ┌────────────────┐
                 │ RoadCenterline │
                 │ DB             │
                 │ (road_center-  │
                 │  lines table)  │
                 └────────────────┘
                          ▲
                          │
                 ┌────────┴────────┐
                 │ Build Pipeline  │
                 │ (one-time)      │
                 │                 │
                 │ OSM Geofabrik   │
                 │ → filter NH     │
                 │ → linemerge     │
                 │ → calibrate     │
                 │ → store         │
                 └─────────────────┘
```

The key invariant: the `RoadCenterline` DB is built **once** (refreshed
quarterly) and queried **per-record** during import.

---

## 2. Database Requirements

### 2.1 `road_centerlines` Table Proposal

```sql
CREATE TABLE road_centerlines (
    -- Primary key
    id              INTEGER PRIMARY KEY,

    -- Highway identifier
    highway_number  TEXT    NOT NULL,  -- e.g. "NH-16", "SH-5"

    -- Spatial anchor (WGS84, EPSG:4326)
    geometry        BLOB,              -- WKB-encoded LineString

    -- Administrative
    state           TEXT,              -- State/UT through which this segment runs
                                       -- e.g. "Andhra Pradesh", "Tamil Nadu"
                                       -- A single NH-16 has one row per state
    road_name       TEXT,              -- e.g. "Grand Trunk Road" (OSM name tag)

    -- Chainage calibration (computed during build)
    chainage_start_km   REAL NOT NULL, -- km value at start of this geometry
    chainage_end_km     REAL NOT NULL, -- km value at end of this geometry
                                       -- NH-16 Andhra segment: 0.0 to 300.0
                                       -- NH-16 Tamil Nadu segment: 300.0 to 550.0

    -- Bounding box (denormalized for fast bbox filtering)
    min_lat         REAL,
    min_lon         REAL,
    max_lat         REAL,
    max_lon         REAL,

    -- Calibration metadata
    calibration_points  INTEGER DEFAULT 0,  -- number of GPS points used
    calibration_rmse_m  REAL,               -- RMSE in meters
    source              TEXT    DEFAULT 'OSM+Hybrid',
    last_updated        TEXT    DEFAULT (datetime('now')),

    -- Uniqueness constraint
    UNIQUE(highway_number, state)
);
```

### 2.2 Geometry Storage

The `geometry` column stores a WKB-encoded `shapely.geometry.LineString`.
WKB is preferred over WKT for three reasons:

| Reason | Detail |
|--------|--------|
| **Binary size** | WKB is ~50% smaller than WKT for the same geometry |
| **Round-trip** | No precision loss from string serialization |
| **Shapely compat** | `shapely.wkb.loads(blob)` is a single function call |

**Node spacing requirement:** The LineString should have nodes at most every
100m to ensure accurate chainage interpolation. If OSM nodes are sparser
(>1km gaps), they must be densified during the build phase:

```sql
-- Example: NH-44 has 5,000 nodes over 500km
-- Node spacing: 100m (good — accurate interpolation)

-- Counter-example: rural NH has 50 nodes over 500km
-- Node spacing: 10km (poor — linear interpolation across curves)
-- Fix: densify to 100m nodes during build
```

### 2.3 Index Requirements

```sql
-- Primary index for lookup by highway_number
CREATE UNIQUE INDEX idx_rcl_hwy_state
    ON road_centerlines(highway_number, state);
    -- Primary query pattern:
    --   WHERE highway_number = ? AND state = ?

-- Fallback index for queries without state filter
CREATE INDEX idx_rcl_hwy
    ON road_centerlines(highway_number);
    -- Needed when state is unknown (e.g., some CSV rows lack state)

-- Spatial bounding-box index
CREATE INDEX idx_rcl_bbox
    ON road_centerlines(min_lat, max_lat, min_lon, max_lon);
    -- Enables fast bounding-box filtering for nearest-geometry queries
    -- before falling back to shapely for exact distance

-- Chainage range index
CREATE INDEX idx_rcl_chainage
    ON road_centerlines(highway_number, chainage_start_km, chainage_end_km);
    -- Query pattern: WHERE highway_number = ?
    --   AND chainage_start_km <= ? AND chainage_end_km >= ?
```

### 2.4 Estimated Row Count & Size

| Highway Type | Count | Avg Segment Length | Total Rows |
|-------------|-------|--------------------|------------|
| NH (National Highways) | 599 highways | 500km each → ~2 rows per NH (state boundary splits) | ~1,200 |
| SH (State Highways) | ~1,000+ | 200km each → ~1 row per SH | ~1,000 |
| **Total** | | | **~2,200 rows** |

**Storage estimate:** 2,200 rows × ~50KB geometry (WKB, 500 nodes) = ~110MB.
Well within SQLite capacity.

### 2.5 Build Table DDL in SQLite

The production build uses a Python script, not raw SQL. But the final schema
is created via:

```python
road_centerlines = """
    CREATE TABLE IF NOT EXISTS road_centerlines (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        highway_number      TEXT NOT NULL,
        geometry_wkb        BLOB,
        state               TEXT,
        road_name           TEXT,
        chainage_start_km   REAL NOT NULL,
        chainage_end_km     REAL NOT NULL,
        min_lat            REAL,
        min_lon            REAL,
        max_lat            REAL,
        max_lon            REAL,
        calibration_points  INTEGER DEFAULT 0,
        calibration_rmse_m  REAL,
        source              TEXT DEFAULT 'OSM+Hybrid',
        last_updated        TEXT DEFAULT (datetime('now')),
        UNIQUE(highway_number, state)
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_rcl_hwy_state
        ON road_centerlines(highway_number, state);

    CREATE INDEX IF NOT EXISTS idx_rcl_hwy
        ON road_centerlines(highway_number);

    CREATE INDEX IF NOT EXISTS idx_rcl_chainage
        ON road_centerlines(highway_number, chainage_start_km, chainage_end_km);
"""
```

---

## 3. Matching Algorithm

### 3.1 Full Algorithm: `resolve_chainage(highway_number, chainage_km, state=None)`

```
┌─────────────────────────────────────────────────────────────────────────┐
│  resolve_chainage("NH-16", 175.3, "Andhra Pradesh")                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 1: NH number match                                        │   │
│  │                                                                  │   │
│  │  Query:                                                         │   │
│  │    SELECT geometry_wkb, chainage_start_km, chainage_end_km       │   │
│  │    FROM road_centerlines                                         │   │
│  │    WHERE highway_number = 'NH-16' AND state = 'Andhra Pradesh'   │   │
│  │                                                                  │   │
│  │  If found → 1 row. Continue.                                     │   │
│  │  If not found → retry without state filter:                      │   │
│  │    WHERE highway_number = 'NH-16'                                │   │
│  │    If multiple rows → find which row contains chainage_km:       │   │
│  │      WHERE chainage_start_km <= 175.3 AND chainage_end_km >= 175.3 │   │
│  │                                                                  │   │
│  │  If no row found → return None (record cannot be geolocated)     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 2: Range check                                            │   │
│  │                                                                  │   │
│  │  chainage_start_km = 0.0   chainage_end_km = 300.0               │   │
│  │  chainage_km = 175.3                                             │   │
│  │                                                                  │   │
│  │  0.0 <= 175.3 <= 300.0 → PASS                                    │   │
│  │                                                                  │   │
│  │  If chainage_km < start: clamp to start, log warning             │   │
│  │  If chainage_km > end:   clamp to end,   log warning             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 3: Compute target distance in meters                      │   │
│  │                                                                  │   │
│  │  distance_from_start_km = 175.3 - 0.0 = 175.3 km                │   │
│  │  target_m = 175.3 * 1000 = 175,300 meters                       │   │
│  │                                                                  │   │
│  │  Note: chainage_start_km is the chainage value at the FIRST      │   │
│  │  node of geometry. If the highway starts at km 0 in Delhi and    │   │
│  │  this geometry segment starts at km 300 (state border), then     │   │
│  │  chainage_start_km = 300.0, and                                   │   │
│  │  target_m = (175.3 - 300.0) → negative → clamp to start.        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 4: Reproject for accurate distance                        │   │
│  │                                                                  │   │
│  │  WGS84 degrees are not meters. Reproject geometry to a local     │   │
│  │  projected CRS for accurate distance measurement.                │   │
│  │                                                                  │   │
│  │  For Andhra Pradesh (~16.5°N): use UTM zone 44N (EPSG:32644)     │   │
│  │                                                                  │   │
│  │  transformer = pyproj.Transformer.from_crs('EPSG:4326',          │   │
│  │                                             'EPSG:32644')        │   │
│  │  geom_proj = shapely.ops.transform(transformer.transform, geom)  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 5: Interpolate point along projected geometry             │   │
│  │                                                                  │   │
│  │  point_proj = geom_proj.interpolate(target_m)                    │   │
│  │  # shapely.interpolate() walks the LineString, accumulating      │   │
│  │  # segment lengths, until it reaches target_m. Returns Point     │   │
│  │  # at that position, interpolated between surrounding nodes.     │   │
│  │                                                                  │   │
│  │  # Reproject back to WGS84                                      │   │
│  │  transformer_inv = pyproj.Transformer.from_crs('EPSG:32644',     │   │
│  │                                                 'EPSG:4326')     │   │
│  │  point_wgs84 = shapely.ops.transform(transformer_inv.transform,  │   │
│  │                                      point_proj)                │   │
│  │                                                                  │   │
│  │  latitude  = point_wgs84.y                                       │   │
│  │  longitude = point_wgs84.x                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Step 6: Validate & return                                      │   │
│  │                                                                  │   │
│  │  if not (state_bounds.min_lat <= lat <= state_bounds.max_lat     │   │
│  │      and state_bounds.min_lon <= lon <= state_bounds.max_lon):   │   │
│  │      log.warning(f"Point outside state bounds: {lat},{lon}")     │   │
│  │      return None                                                  │   │
│  │                                                                  │   │
│  │  return (16.5523, 80.5217)                                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Algorithm Pseudocode

```python
def chainage_to_latlon(
    highway_number: str,
    chainage_km: float,
    state: Optional[str] = None,
) -> Optional[Tuple[float, float]]:
    """
    Convert (highway_number, chainage_km) to (lat, lon).

    Steps:
      1. Query road_centerlines by highway_number + state (optional).
      2. Clamp chainage to valid range [start, end].
      3. Compute target distance in meters from geometry start.
      4. Reproject geometry from WGS84 to UTM for meter-accurate
         interpolation.
      5. shapely.interpolate() at target distance.
      6. Reproject result back to WGS84.
      7. Validate against state bounding box.
      8. Return (lat, lon) or None.
    """
    pass
```

### 3.3 Query Strategy: State Filter

The state filter improves matching accuracy by narrowing to the correct
geographic segment:

```
Without state filter:                        With state filter:
                                           ┌─────────────┐
  ┌────────────────────────────────────┐    │Query returns│
  │SELECT * FROM road_centerlines      │    │only the row │
  │WHERE highway_number = 'NH-16'      │    │for Andhra   │
  │                                    │    │Pradesh:     │
  │Returns 4 rows:                     │    │             │
  │  (0.0, 300.0, "Andhra Pradesh")    │    │chainage_start=0.0│
  │  (300.0, 550.0, "Tamil Nadu")     │    │chainage_end=300.0│
  │  (550.0, 800.0, "Karnataka")      │    │             │
  │  (800.0, 1000.0, "Maharashtra")   │    │Only 1 row  │
  └────────────────────────────────────┘    │ → simpler   │
        Need to find correct row            │   logic     │
        by chainage range check             └─────────────┘
```

Recommended: use state filter when available (Dataful CSV has 100% state
coverage). Fall back to chainage range scan when state is missing.

### 3.4 Fallback Query (No State Match)

```
Input: highway_number="NH-16", chainage_km=175.3, state=None

Query:
  SELECT geometry_wkb, chainage_start_km, chainage_end_km
  FROM road_centerlines
  WHERE highway_number = 'NH-16'
    AND chainage_start_km <= 175.3
    AND chainage_end_km >= 175.3
  LIMIT 1

Expected:
  → (geometry, 0.0, 300.0)  -- Andhra Pradesh segment
```

---

## 4. Accuracy Handling

### 4.1 Accuracy Determinants

| Factor | Impact on Position Error | Source |
|--------|------------------------|--------|
| OSM node spacing | ±50m per km of node gap on a curved road | OSM |
| Chainage calibration offset | ±100m (with ≥10 GPS points), ±5000m (with <3) | Calibration |
| CRS reprojection | ±1m (pyproj is accurate to cm level) | pyproj |
| Chainage parsing | ±50m (chainage is a float; format ambiguity at boundaries) | Importer |
| GPS calibration point accuracy | ±5m (consumer GPS) | Dataful CSV |

**Dominant error source:** Calibration offset. OSM geometry is typically
accurate to ±10m; the chainage calibration contributes ±100m to ±5000m.

### 4.2 Accuracy Tiers by Source

#### Tier 1: GPS Direct (±5m)

```
Source: Dataful CSV rows with latitude/longitude populated
Coverage: ~1,300 records (15%)
Confidence: 0.85
Resolution: "GPS"
Action: Use CSV coordinates directly. No chainage conversion needed.
```

#### Tier 2: Hybrid Calibrated (±100–500m)

```
Source: OSM geometry + GPS calibration (≥10 points per NH)
Coverage: ~6,000 records (68%) — covers major NH with sufficient GPS data
Confidence: 0.50
Resolution: "Chainage"
Error sources: calibration offset ±100m + OSM geometry ±10m + interpolation ±20m

Applicable to: NH-44, NH-48, NH-16, NH-19, NH-27, NH-2, NH-3
These 7 highways cover ~70% of Dataful records.
```

#### Tier 3: OSM Uncalibrated (±5–50km)

```
Source: OSM geometry only, no GPS calibration points
Coverage: ~1,000 records (11%) — SH roads, obscure NH
Confidence: 0.30
Resolution: "Chainage"
Error sources: unknown chainage origin ±5–50km + OSM geometry ±10m

Mitigation:
  - Still better than skipping the record entirely
  - The point falls on the right highway, just at an uncertain position
  - For routing (future): the point acts as a waypoint constraint, and
    Mapbox Directions will snap it to the correct road position
```

#### Tier 4: Discarded (No Location)

```
Source: Records with no chainage, no GPS, no geocodable text
Coverage: ~530 records (6%)
Confidence: N/A
Resolution: None
Action: Skip. Log as "no location info".
```

### 4.3 Fallback Confidence by Case

```
┌─────────────────────────────────────────────────────────────────────┐
│                FALLBACK CONFIDENCE MATRIX                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Chainage→lat/lon outcome     │ geometry_resolution │ confidence    │
│──────────────────────────────┼─────────────────────┼───────────────│
│  GPS in CSV                  │ GPS                 │ 0.85          │
│  Calibrated (≥10 pts)        │ Chainage            │ 0.50          │
│  Calibrated (3–9 pts)        │ Chainage            │ 0.40          │
│  OSM uncalibrated (0 pts)    │ Chainage            │ 0.30          │
│  Nearest point on NH (bbox)  │ Manual              │ 0.20          │
│  Geocoded from police_station│ Manual              │ 0.15          │
│  Failed → skipped            │ N/A                 │ 0.00          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Error Budget (Calibrated NH)

```
Chainage interpolation error budget (RMSE):

  Source                        Error (m)     Notes
  ──────────────────────────────────────────────────────
  GPS point accuracy             ±5           Consumer GPS
  Calibration offset estimation  ±100         Median of N points
  OSM geometry node spacing      ±10          ≤100m between nodes
  CRS reprojection               ±1           UTM zone boundary
  Chainage parsing               ±25          ±0.025 km at kilometer boundary
  ──────────────────────────────────────────────────────
  Combined (RSS)                 ±103 m
```

For uncalibrated NH, the calibration offset term balloons to ±5–50km,
dominating all other terms.

### 4.5 Validation During Import

Every chainage→lat/lon result should be validated before use:

```python
def validate_point(
    lat: float, lon: float,
    highway_number: str,
    state: Optional[str],
) -> bool:
    """
    Check that the resolved point is plausible.

    Validation rules:
      1. Is it within the state's bounding box?    (±2° buffer)
      2. Is it within 500m of any NH geometry?     (spatial proximity)
      3. Does the nearest NH match the expected    (highway cross-check)
         highway_number?

    If any check fails → confidence halved.
    If all checks fail → return None (discard).
    """
    if not state_bounds_check(lat, lon, state):
        return False
    if not proximity_check(lat, lon, highway_number):
        return False
    return True
```

---

## 5. Why Chainage Conversion Happens During Import, Not During Routing

### 5.1 Architectural Decision

```
                   IMPORT TIME (recommended)          vs          ROUTING TIME

  Dataful CSV ──→ chainage→lat/lon ──→ HighwayBlackSpot       Dataful CSV ──→ HighwayBlackSpot
                        │                                                            │
                   store (lat, lon)                                               store chainage
                        │                                                            │
                  ┌─────┴─────┐                                              ┌──────┴──────┐
                  │  Routing  │                                              │   Routing   │
                  │  engine   │                                              │   engine    │
                  │  uses     │                                              │   must      │
                  │  (lat,    │                                              │   convert   │
                  │   lon)    │                                              │   chainage  │
                  │  directly │                                              │   per req   │
                  └───────────┘                                              └─────────────┘
```

**Decision: Convert chainage to lat/lon at import time.**

### 5.2 Rationale

| Reason | Detail |
|--------|--------|
| **1. Routing performance** | Every route request would need N chainage→lat/lon conversions (one per nearby HighwayBlackSpot). With ~8,000 black spots, that is thousands of `shapely.interpolate()` calls per request. At import time, it's a one-time batch cost of ~42 seconds. |
| **2. Simpler routing code** | The routing engine treats HighwayBlackSpot identically to CrimeHotspot — both have `(lat, lon, radius, severity)`. No branching needed for "is this point in chainage format?". |
| **3. Single responsibility** | The importer handles all data normalization (chainage→lat/lon, validation, confidence). The routing engine focuses on spatial queries and penalties. |
| **4. Deterministic at query time** | If chainage→lat/lon changed between import and query (e.g., OSM geometry updated, calibration improved), two queries for the same route could return different safety scores. Import-time conversion freezes the position. |
| **5. Re-import is manageable** | When calibration improves (more GPS points), re-import only the affected NH records. This is a batch job, not a real-time operation. |
| **6. The routing penalty is already spatial** | `calculate_penalty()` uses `haversine_distance(midpoint, spot.lat, spot.lon)` — it needs lat/lon. Changing the penalty function to also handle chainage would violate the existing spatial-only abstraction. |

### 5.3 Import-time is Correct by Design

```
┌────────────────────────────────────────────────────────────────┐
│  HighwayBlackSpot table always stores resolved coordinates     │
│                                                                │
│  id  │  latitude  │  longitude  │  chainage_start_km │ source  │
│ ─────┼────────────┼─────────────┼────────────────────┼─────────│
│  1   │  16.5523   │  80.5217   │  175.3             │ MoRTH   │
│  2   │  16.5623   │  80.5317   │  176.0             │ MoRTH   │
│  3   │  28.6129   │  77.2295   │  120.0             │ MoRTH   │
│ ...                                                             │
│                                                                │
│  Routing query: find black spots within 1km of (lat, lon)     │
│  → Simple bounding box: WHERE lat BETWEEN ? AND ?              │
│    AND lon BETWEEN ? AND ?                                     │
│  → No chainage conversion needed                               │
└────────────────────────────────────────────────────────────────┘
```

The `chainage_start_km` and `chainage_end_km` columns are stored for
**provenance** (traceability back to the original CSV data), not for routing.

### 5.4 What If the Centerline DB Changes?

```
Scenario: After importing 8,000 records with chainage→lat/lon via
          calibration v1 (RMSE ±200m), calibration v2 improves to ±50m.

Action:
  1. Identify affected HighwayBlackSpot records:
     UPDATE highway_black_spots
     SET needs_recompute = 1
     WHERE geometry_resolution = 'Chainage'
       AND highway_number IN (list_of_improved_NH);

  2. Re-run chainage→lat/lon for flagged records:
     For each flagged record:
       lat, lon = chainage_to_latlon(hwy, chainage_km)
       UPDATE highway_black_spots
       SET latitude = :lat, longitude = :lon,
           confidence_score = :new_score,
           updated_at = now()
       WHERE id = :id;

  3. Recompute RoadSegmentRisk for affected highway:
     (Step 5 of the ingestion pipeline)
```

This re-computation is a batch job, not part of the routing hot path.
The routing engine is unaware this happened — it sees updated lat/lon
values on the next query.

### 5.5 Provenance Tracking

The `HighwayBlackSpot` model retains enough information to trace any
coordinate back to its source:

```
HighwayBlackSpot record for AP-(02)-NH16-60:

  latitude:            16.5523           ← from chainage→lat/lon
  longitude:           80.5217
  chainage_start_km:   175.3             ← original CSV chainage
  chainage_end_km:     175.8
  geometry_resolution: "Chainage"        ← method used
  source:              "MoRTH"           ← dataset origin
  source_name:         "Dataful MoRTH Black Spot Dataset"
  source_url:          "https://dataful.in/datasets/21559/"
  confidence_score:    0.50              ← calibration quality
  updated_at:          2026-06-27 T 20:15:00 ← when converted
```

All routing-time decisions use only `(lat, lon, radius, severity)`.
The chainage fields are informational — they allow the operator to
verify and re-compute if needed.
