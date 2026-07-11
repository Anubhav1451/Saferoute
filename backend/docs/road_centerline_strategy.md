# Road Centerline Database — Strategy for Chainage→lat/lon Conversion

## The Problem

The Dataful Black Spot CSV has 8,862 records. Only ~15% include GPS coordinates.
The remaining ~7,500 records have `(highway_number, chainage_km)` but no lat/lon.
The `HighwayBlackSpot` model requires `(latitude, longitude)` — they are the
only non-nullable spatial fields. Without them, records are rejected.

A road centerline database bridges this gap:

```
highway = "NH-16", chainage = 120.0 km
        │
        ▼
road_centerlines table:
  SELECT way_geometry FROM roads
  WHERE highway_number = 'NH-16'
  ORDER BY ABS(chainage_midpoint - 120.0)
  LIMIT 1
        │
        ▼
interpolate point at 120km along way_geometry
        │
        ▼
lat = 28.6129, lon = 77.2295
```

---

## 1. Options

### Option A: OpenStreetMap (Geofabrik Extract)

| Property | Value |
|----------|-------|
| **Data source** | https://download.geofabrik.de/asia/india.html |
| **Format** | OSM PBF (~2GB for India) or GeoJSON |
| **License** | ODbL (Open Database License) |
| **Update frequency** | Daily (Geofabrik mirrors) |
| **Coverage** | All Indian NH, SH, expressways mapped by OSM contributors |
| **Cost** | Free |

#### How It Works

1. Download India `.osm.pbf` from Geofabrik
2. Filter ways where `highway IN ('motorway', 'trunk', 'primary')` and
   `ref LIKE 'NH%'` or `ref LIKE 'SH%'`
3. For each matching way, extract:
   - `ref` tag → `highway_number` (e.g. `"NH-44"`)
   - Way node coordinates → `geometry` (LineString)
   - `name` tag → `road_name`
4. Build SQLite/PostGIS table with spatial index
5. At import time: for a given `(highway_number, chainage_km)`, find the
   nearest way, interpolate, return lat/lon

#### Strengths

- **Free and open** — no licensing costs, no API keys
- **Well-maintained** — OSM India community actively maps highways
- **Global coverage** — same approach works if the app expands beyond India
- **Rich tagging** — `ref`, `name`, `highway`, `maxspeed`, `lanes`, `surface`
  tags available for future enrichment

#### Weaknesses

- **No chainage markers** — OSM does not store kilometer chainage in tags.
  Chainage position must be estimated by measuring cumulative distance from
  the way's start node.
- **Way fragmentation** — A single highway like NH-44 is typically split into
  hundreds of short ways (at intersections, district boundaries). Determining
  the correct start point for chainage measurement requires assembling ways
  into a continuous route and identifying the NH origin.
- **Origin offset** — NH chainage starts at the highway's origin (e.g., km 0
  at Delhi for NH-44). OSM ways don't encode this. The first way node found
  by random download may start at km 120, not km 0.
- **Data quality varies** — Rural NH segments may be missing or have poor
  node resolution (±500m between nodes in remote areas).

#### Effort Estimate

| Task | Time |
|------|------|
| Download & filter OSM extract | 1 hour |
| Write assembly script (ways→continuous routes) | 2–3 days |
| Calibrate chainage origins using known GPS points | 1–2 days |
| Build spatial index, test coverage | 1 day |
| **Total** | **4–6 days** |

---

### Option B: Government / ArcGIS NH Layers

| Property | Value |
|----------|-------|
| **Potential sources** | NHAI GIS cell, Bhuvan (ISRO), India WRIS, Survey of India |
| **Format** | Shapefile, GeoJSON, KML |
| **License** | Government data — typically free for non-commercial use |
| **Update frequency** | Ad-hoc (NHAI GIS updated irregularly) |
| **Coverage** | All NH as per NHAI records (official) |
| **Cost** | Free (RTI-accessible) but may require formal request |

#### Source Candidates

##### B1: NHAI GIS Data

NHAI maintains a GIS database of all National Highways with **chainage markers**
as point features at every kilometer. This is the gold standard — it directly
maps `chainage_km → lat/lon`.

| Property | Value |
|----------|-------|
| **Availability** | Not publicly downloadable. May require RTI application. |
| **Format** | Shapefile with point features at km intervals |
| **Origin accuracy** | Exact — chainage measured from official NH origin |
| **Effort to acquire** | Unknown (weeks to months via RTI) |

##### B2: Bhuvan (ISRO) — Indian Road Network

ISRO's Bhuvan platform provides high-resolution road network data derived from
satellite imagery (Cartosat-1, 2.5m resolution).

| Property | Value |
|----------|-------|
| **Availability** | https://bhuvan.nrsc.gov.in/ — web portal with API |
| **Format** | WMS/WFS (not direct download) |
| **Chainage** | No chainage data |
| **Effort to acquire** | Medium — API registration required |

##### B3: India WRIS (Water Resources Information System)

India WRIS includes road network data as part of its infrastructure layer.

| Property | Value |
|----------|-------|
| **Availability** | https://indiawris.gov.in/ |
| **Format** | Web viewer, limited export |
| **Chainage** | No chainage data |
| **Focus** | Water resources (canals, rivers) — road data is secondary |

#### Strengths

- **Authoritative** — official NHAI/MoRTH data, definitive chainage origins
- **Direct mapping** — NHAI GIS has explicit chainage→lat/lon (no estimation)

#### Weaknesses

- **Acquisition risk** — NHAI GIS may require RTI, take weeks, or be denied
- **Format fragmentation** — different agencies use different formats and
  coordinate systems
- **No single source** — would need to combine NHAI, MoRTH, and state data
  for full coverage
- **Update uncertainty** — government GIS data is not on a fixed release cadence

#### Effort Estimate

| Task | Time |
|------|------|
| Identify and contact NHAI GIS cell | 2–4 weeks (wait time) |
| Write importer for Shapefile/GeoJSON | 2 days |
| Harmonize coordinate systems | 1 day |
| Coverage validation against Dataful CSV | 1 day |
| **Total** | **2–4 weeks (blocked on RTI)** |

---

### Option C: Hybrid (OSM Base + GPS Calibration)

| Property | Value |
|----------|-------|
| **Base geometry** | OSM (Geofabrik) |
| **Chainage calibration** | ~1,300 GPS-tagged Dataful records |
| **License** | ODbL (base) + Open Government Data (calibration) |
| **Update frequency** | Daily (OSM) + on-demand (calibration refresh) |
| **Cost** | Free |

#### How It Works

The core problem with pure OSM (Option A) is unknown chainage origin. The
hybrid approach solves this using the GPS-tagged Dataful records as calibration
points:

```
Step 1: Extract OSM NH geometries (same as Option A)
        └── Each highway becomes an unordered set of way segments

Step 2: Assemble ways into continuous routes
        └── Sort ways by spatial proximity, merge into one LineString per NH

Step 3: Calibrate chainage origin for each NH
        └── Use ~1,300 GPS-tagged black spot records from Dataful CSV
        └── Each GPS record has (lat, lon, highway_number, chainage_km)
        └── For each record:
              a. Find nearest point on assembled NH geometry
              b. Measure cumulative distance from geometry start
              c. The difference between measured distance and known chainage
                 is the origin offset
        └── Average all calibration points for one NH → final offset

Step 4: Interpolation function
        └── Given (NH-44, 120.0 km):
              a. Look up assembled NH-44 geometry
              b. Compute target distance = chainage_km × 1000 + origin_offset
              c. Interpolate point along geometry at target distance
              d. Return (lat, lon)
```

#### Calibration Formula

```
For a GPS-tagged record (lat_gps, lon_gps, chainage_csv):
  nearest_point = nearest_point_on_geometry(NH_geom, (lat_gps, lon_gps))
  measured_dist = cumulative_distance(NH_geom_start, nearest_point)  # meters
  offset = measured_dist - chainage_csv * 1000                       # meters

Final offset for NH: median(offset_1, offset_2, ..., offset_n)
```

The median (not mean) is used to discard outliers caused by:
- GPS points that snapped to the wrong highway (parallel NH/SH)
- CSV records where the `black_spot_id` highway number is incorrect
- OSM geometry gaps where the assembled route deviates from the real road

#### Strengths

- **No origin dependency** — chainage is calibrated from actual GPS data,
  not assumed from NH origin
- **Self-correcting** — more GPS calibration points → more accurate offset
- **Incremental** — start with 1,300 points, improve as more GPS data arrives
- **Same-day viability** — OSM download + calibration can yield usable
  results in 2–3 days

#### Weaknesses

- **Calibration quality varies by NH** — NH-44 may have 200 GPS points (good),
  while NH-16 may have 50 (adequate), and NH-31 may have 5 (poor, ±5km error)
- **Requires OSM assembly** — same way-fragmentation problem as Option A
- **Assumes linear chainage** — chainage is measured along the road centerline,
  but the OSM geometry may deviate (e.g., missing a flyover, taking a detour
  through a service road)

#### Effort Estimate

| Task | Time |
|------|------|
| Download & filter OSM extract | 1 hour |
| Assemble OSM ways→continuous routes | 2–3 days |
| Extract GPS calibration points from Dataful CSV | 2 hours |
| Implement calibration algorithm | 1 day |
| Build spatial index, test coverage | 1 day |
| **Total** | **4–6 days** (same as Option A, but with calibrated chainage) |

---

## 2. Required Fields

The road centerline database should have the following schema:

```
road_centerlines
│
├── geometry: LineString (WGS84, SRID 4326)
│     Required. The path of the road as a series of (lat, lon) nodes.
│     Must be continuous (no gaps) for a single highway_number.
│     Node spacing ≤ 100m for accurate chainage interpolation.
│
├── highway_number: String (max 20)
│     Required. E.g. "NH-44", "SH-1", "MDR-5".
│     Primary identifier for matching with black_spot_id / HighwayBlackSpot.
│     Should be the canonical MoRTH designation (with hyphen).
│
├── state: String (max 50)
│     Optional. State/UT through which this segment passes.
│     Useful for filtering and validation against HighwayBlackSpot.state.
│     A single highway may span multiple states (each gets a row segment).
│
├── road_name: String (max 200)
│     Optional. E.g. "Grand Trunk Road", "Mumbai-Pune Expressway".
│     From OSM `name` tag. Not critical for chainage matching.
│
├── chainage_start_km: Float
│     Required. The chainage value at the start of this geometry segment.
│     For NH-44: chainage_start = 0.0 at Delhi origin.
│     Computed during calibration (not available from OSM directly).
│
├── chainage_end_km: Float
│     Required. The chainage value at the end of this geometry segment.
│     For a 500km NH with one row: chainage_end = 500.0.
│
├── start_latitude: Float
│     Computed (denormalized). Latitude of geometry's first node.
│     Speeds up bounding-box queries without touching geometry column.
│
├── start_longitude: Float
│     Same, longitude.
│
├── end_latitude: Float
│     Computed. Latitude of geometry's last node.
│
├── end_longitude: Float
│     Same, longitude.
│
├── source: String (max 50)
│     Required. "OSM", "NHAI", "Hybrid" — provenance of this geometry.
│
├── calibration_points: Integer
│     Required (for Hybrid). Number of GPS calibration points used.
│     Determines confidence in chainage offset.
│     If 0 (pure OSM, no calibration): chainage_start/end are estimates.
│
├── calibration_rmse_m: Float
│     Required (for Hybrid). Root-mean-square error of calibration
│     point residuals. Higher RMSE = lower interpolation confidence.
│     Estimated < 200m for well-calibrated NH.
│
└── last_updated: DateTime
      Required. When this row was last calibrated/recomputed.
```

### Index Requirements

```sql
CREATE INDEX idx_road_centerlines_hwy ON road_centerlines(highway_number);
CREATE INDEX idx_road_centerlines_state ON road_centerlines(state);
CREATE SPATIAL INDEX idx_road_centerlines_geom ON road_centerlines(geometry);
-- The spatial index is critical for nearest-point queries.
-- In SQLite: use SpatiaLite extension.
-- In PostGIS: CREATE INDEX ... USING GIST (geometry);
```

### Partitioning Strategy (Optional)

If the DB grows large (>50,000 segments), partition by highway type:

```
road_centerlines_nh     — National Highways (NH-1 through NH-999)
road_centerlines_sh     — State Highways (SH-1 through SH-999)
road_centerlines_mdr    — Major District Roads
```

For the initial implementation, a single table suffices (Indian NH count is
~600 highways, each ~500km → ~300 segments of 1km each).

---

## 3. Chainage Matching Algorithm

### 3.1 Algorithm: `chainage_to_latlon(highway_number, chainage_km)`

```
Input:  highway_number = "NH-44"
        chainage_km     = 120.0

┌─────────────────────────────────────────────────────────────┐
│  1. Fetch geometry                                            │
│                                                               │
│     SELECT geometry, chainage_start_km                        │
│     FROM road_centerlines                                     │
│     WHERE highway_number = 'NH-44'                            │
│     LIMIT 1                                                   │
│                                                               │
│     → geometry: LineString(77.1,28.6  77.2,28.7 ...)         │
│     → chainage_start_km: 0.0  (calibrated origin)            │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  2. Compute target distance along geometry                    │
│                                                               │
│     target_distance_m = (chainage_km - chainage_start_km)     │
│                        × 1000.0                               │
│                                                               │
│     → target_distance_m = (120.0 - 0.0) × 1000                │
│     → target_distance_m = 120,000 meters                      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  3. Interpolate point on geometry                             │
│                                                               │
│     [shapely]                                                 │
│     point = geometry.interpolate(target_distance_m)            │
│                                                               │
│     → This walks the LineString, accumulating segment         │
│       lengths until it reaches 120,000m, then interpolates    │
│       between the two surrounding nodes.                      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  4. Validate                                                   │
│                                                               │
│     total_length_m = geometry.length                           │
│     assert target_distance_m <= total_length_m,                │
│         'chainage out of range'                                │
│                                                               │
│     → total_length_m = 500,000 (NH-44 is ~500km)              │
│     → 120,000 <= 500,000 → OK                                  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  5. Return                                                     │
│                                                               │
│     → (point.y, point.x)  → (28.6129, 77.2295)                │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Edge Cases

| Case | Problem | Resolution |
|------|---------|------------|
| `chainage_km < chainage_start_km` | Before known start | Return start point, log warning |
| `chainage_km > geometry_end_in_km` | Past known end | Return end point, log warning |
| `chainage_start_km = 0` (uncalibrated) | Origin unknown | Use OSM geometry from first node. Distance from first node is the chainage value. Error ±5–50km. |
| No geometry found for highway | Missing in DB | Return `None`. Caller skips record. |
| Multiple geometry rows per NH | Highway split into segments | Merge contiguous segments into a single LineString before interpolating. |
| Node resolution too sparse | >1km between nodes | `shapely.interpolate()` still works correctly — it interpolates linearly between nodes. Accuracy degrades with curvature. |

### 3.3 Handling Multiple Segments per Highway

OSM stores highways as fragmented ways. The assembly step merges them:

```python
def assemble_highway(highway_number, ways):
    """
    Input: List of OSM way geometries for the same highway_number.
    Output: Single continuous LineString, ordered from origin to terminus.

    Algorithm:
      1. Start with any way (seed).
      2. Find the closest unconnected way by endpoint proximity (< 100m).
      3. Append or prepend based on which endpoint matches.
      4. Repeat until all ways connected.
      5. For disconnected ways (bridges, parallel routes):
         - Check if they share a node (intersection).
         - If not, leave as separate row with a segment_id.
    """
    merged = shapely.ops.linemerge(ways)
    # linemerge() handles endpoint matching automatically.
    # It returns a MultiLineString if ways don't form a single line.
    return merged
```

### 3.4 Calibration Algorithm (Hybrid Option Only)

```
For each highway_number:
  1. Collect all GPS calibration points (from Dataful CSV lat/lon rows)
     where highway_number matches.

  2. For each point (lat, lon, chainage_csv):
     a. Find nearest point on OSM geometry.
     b. Measure cumulative distance from geometry start (measured_m).
     c. offset_m = measured_m - chainage_csv * 1000
     d. Store offset_m.

  3. Compute final offset:
     offsets = sorted([offset_1, offset_2, ..., offset_n])
     if n >= 10:
       offset = median(offsets)               ← robust to outliers
       rmse = sqrt(mean([o - offset]**2))      ← calibration quality
     elif n >= 3:
       offset = mean(offsets)
       rmse = large (estimate ± 1000m)
     else:
       offset = 0  (uncalibrated, use raw OSM)
       rmse = INF

  4. chainage_start = offset / 1000            ← in km
     For the origin: chainage_start = -offset / 1000 if offset < 0
     (Negative offset means OSM geometry starts at negative chainage,
      i.e., the geometry extends beyond the NH origin.)

  5. Store: {
       "chainage_start_km": chainage_start,
       "calibration_points": n,
       "calibration_rmse_m": rmse
     }
```

### 3.5 Calibration Coverage by Highway (Estimated)

NH-44 alone accounts for ~300 of the 1,300 GPS points:

| Highway | GPS Points Expected | Calibration RMSE | Confidence |
|---------|-------------------|-------------------|------------|
| NH-44 (Delhi–Amritsar) | ~300 | ±100m | ★★★★★ |
| NH-48 (Delhi–Mumbai) | ~200 | ±120m | ★★★★★ |
| NH-16 (Kolkata–Chennai) | ~100 | ±150m | ★★★★☆ |
| NH-19 (Delhi–Kolkata) | ~80 | ±150m | ★★★★☆ |
| NH-27 (East–West corridor) | ~50 | ±200m | ★★★☆☆ |
| NH-31 (unconnected) | ~5 | ±3000m | ★☆☆☆☆ |
| SH (State Highways) | 0–2 each | ±5000m+ | ☆☆☆☆☆ |

### 3.6 Performance: Interpolation Latency

| Operation | Time | Notes |
|-----------|------|-------|
| Fetch geometry from indexed table | ~5ms | SQLite with spatial index |
| `shapely.interpolate()` | ~1ms | 500-node LineString |
| Total per call | ~6ms | Negligible in import pipeline |

Batch of 7,000 chainage→lat/lon conversions: ~42 seconds.

---

## 4. Python Libraries Needed

### 4.1 Core Libraries

| Library | Version | Purpose | Used By |
|---------|---------|---------|---------|
| **geopandas** | ≥0.14 | Read and filter OSM PBF/GeoJSON. Load road geometries into a GeoDataFrame for processing and export. | Import script, assembly |
| **shapely** | ≥2.0 | Geometry operations: `interpolate()`, `line_merge()`, `nearest_points()`, `distance()`, `LineString` construction | Interpolation, assembly, calibration |
| **pyproj** | ≥3.6 | Coordinate transformations (WGS84 ↔ UTM for accurate distance measurement). Needed because `shapely.distance()` in EPSG:4326 is in degrees, not meters. | Calibration, distance measurement |
| **osmnx** | ≥1.9 | Download OSM road geometries by highway type and bounding box. Alternative to Geofabrik for targeted highway downloads. | OSM acquisition (alternative) |

### 4.2 Installation

```bash
# Core geospatial stack (Windows / Linux)
pip install geopandas shapely pyproj osmnx

# Optional: spatial index for SQLite
# Required if using SQLite instead of PostGIS
pip install spatialite  # or compile mod_spatialite

# Optional: PostGIS adapter (if using PostgreSQL)
# pip install psycopg2-binary geoalchemy2
```

### 4.3 Dependency Graph

```
import geopandas         # read OSM, GeoDataFrame ops
import shapely           # geometry ops (interpolate, line_merge)
import pyproj            # coordinate transform for distance
import osmnx             # (alternative) OSM download

      │
      ▼
┌────────────────────────────────────────────┐
│  RoadCenterlineDB                          │
│────────────────────────────────────────────│
│  - geometry: shapely LineString            │
│  - crs: pyproj CRS (EPSG:4326)            │
│  - highway_number: str                     │
│  - calibration: dict                       │
│────────────────────────────────────────────│
│  + chainage_to_latlon(hwy, km) → (lat,lon) │
│  + nearest_highway(lat, lon) → (hwy, km)   │
│  + assemble_from_osm(extract_path)         │
│  + calibrate(gps_points: DataFrame)        │
│  + save(sqlite_path)                       │
│  + load(sqlite_path)                       │
└────────────────────────────────────────────┘
```

### 4.4 Library Function Reference

| Function | Library | Input | Output | Notes |
|----------|---------|-------|--------|-------|
| `shapely.LineString(coords)` | shapely | `[(lon,lat), ...]` | LineString | Build geometry from node list |
| `line.interpolate(distance)` | shapely | `distance` in meters | Point | Interpolate along geometry (requires projected CRS for meter units) |
| `line.project(point)` | shapely | Point | `distance` in meters | Inverse: measure distance from start |
| `shapely.ops.linemerge(lines)` | shapely | List of LineStrings | LineString or MultiLineString | Merge connected ways |
| `geopandas.read_file(path, layer=)` | geopandas | File path | GeoDataFrame | Read OSM PBF, GeoJSON, Shapefile |
| `gdf.cx[x1:x2, y1:y2]` | geopandas | bounding box | GeoDataFrame | Spatial bounding-box filter |
| `pyproj.Transformer.from_crs(crs1, crs2)` | pyproj | CRS strings | Transformer object | Create coordinate transformer |
| `transformer.transform(lat, lon)` | pyproj | (lat, lon) | (x, y) in target CRS | Convert degrees ↔ meters |
| `osmnx.graph_from_place('India', network_type='drive')` | osmnx | Place name | NetworkX graph | Download OSM road network |
| `osmnx.graph_to_gdfs(graph, nodes, edges)` | osmnx | networkx graph | (nodes GDF, edges GDF) | Convert OSM graph to GeoDataFrame |

---

## 5. Recommended Final Architecture

### 5.1 Decision Matrix

| Requirement | Option A (OSM) | Option B (Government) | Option C (Hybrid) |
|-------------|---------------|----------------------|-------------------|
| Time to first usable result | 4–6 days | 2–4 weeks | 4–6 days |
| Chainage accuracy (NH with ≥10 GPS points) | ±5–50km (uncalibrated) | ±10m (NHAI markers) | ±100–200m |
| Chainage accuracy (NH with <3 GPS points) | ±5–50km | ±10m (if NHAI data covers) | ±5–50km (uncalibrated) |
| Licensing cost | Free | Free (RTI) | Free |
| Maintenance effort | Low (OSM auto-updates) | Unknown (depends on NHAI) | Medium (re-calibrate quarterly) |
| Coverage risk (missing highways) | Low (OSM covers >95% of NH) | Medium (NHAI may not have all SH) | Low (OSM base guarantees coverage) |
| Legal risk | ODbL attribution required | Government data terms | ODbL + Open Government Data |

### 5.2 Recommendation: Hybrid (Option C, then B enrichment)

**Phase 1 — Immediate (4–6 days):**

Build the OSM-based system with GPS calibration using the ~1,300 Dataful points:

```
Build Road Centerline DB
  │
  ├── Download India OSM extract (Geofabrik)
  ├── Filter highway=trunk,motorway AND ref LIKE 'NH%'
  ├── Assemble OSM ways into continuous NH geometries
  │
  ├── Extract 1,300 GPS calibration points from Dataful CSV
  │   (rows where latitude IS NOT NULL)
  │
  ├── For each NH:
  │     ├── Get median chainage offset from GPS points
  │     ├── Store chainage_start_km, calibration_points, rmse
  │     └── If <3 calibration points → mark as uncalibrated
  │
  └── Deploy chainage_to_latlon() → MoRTHBlackspotsImporter
```

**Phase 2 — Improve (1–2 weeks, parallel):**

```
Improvement Paths (run in parallel)
  │
  ├── Path A: Acquire NHAI GIS data (RTI)
  │   ├── Submit RTI application to NHAI GIS cell
  │   ├── If granted → replace OSM geometry with official data
  │   └── Chainage markers become exact (±10m)
  │
  ├── Path B: Crowdsource calibration points
  │   ├── Every new GPS-tagged black spot auto-calibrates
  │   ├── Every iRAD/e-DAR FIR with GPS contributes
  │   └── Add calibration_points and rmse to RoadSegmentRisk
  │
  └── Path C: Manual calibration for poorly-covered NH
      ├── For NH with <3 GPS points:
      │   Use Google Maps / Mapillary to find known landmarks
      │   at specific chainage, record GPS coordinate
      └── 2–3 calibration points per NH is enough for ±500m
```

**Phase 3 — Production (monthly cadence):**

```
Regular Maintenance
  │
  ├── Monthly: Refresh OSM geometries (Geofabrik daily extracts)
  │   └── Only update if OSM geometry changed (>500m deviation)
  │
  ├── Quarterly: Re-calibrate chainage offsets
  │   ├── Pull all new GPS-tagged Dataful/CSV records
  │   └── Recompute median offset per NH
  │
  └── On-demand: Re-import HighwayBlackSpot data
      └── Chainage→lat/lon improves automatically with
          better calibration
```

### 5.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ROAD CENTERLINE DB                           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Build Pipeline (one-time + refresh)                        │   │
│  │                                                              │   │
│  │  Geofabrik India OSM PBF                                     │   │
│  │       │                                                      │   │
│  │       ▼                                                      │   │
│  │  osm2pgsql / geopandas.filter(ref LIKE 'NH%')                 │   │
│  │       │                                                      │   │
│  │       ▼                                                      │   │
│  │  shapely.ops.linemerge() → continuous NH geometries           │   │
│  │       │                                                      │   │
│  │       ▼                                                      │   │
│  │  Calibration (Dataful GPS points) → chainage_start_km         │   │
│  │       │                                                      │   │
│  │       ▼                                                      │   │
│  │  road_centerlines.db (SQLite + spatial index)                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Query Interface                                             │   │
│  │                                                              │   │
│  │  chainage_to_latlon('NH-44', 120.0) → (28.61, 77.23)        │   │
│  │         │                                                    │   │
│  │         ▼                                                    │   │
│  │  1. SELECT geometry, chainage_start_km                       │   │
│  │     FROM road_centerlines                                    │   │
│  │     WHERE highway_number = 'NH-44'                           │   │
│  │                                                              │   │
│  │  2. target_m = (120.0 - chainage_start_km) * 1000            │   │
│  │                                                              │   │
│  │  3. point = geometry.interpolate(target_m)                    │   │
│  │                                                              │   │
│  │  4. return (point.y, point.x)                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Consumer                                                   │   │
│  │                                                              │   │
│  │  MoRTHBlackspotsImporter.parse_csv_row()                     │   │
│  │       │                                                      │   │
│  │       ▼                                                      │   │
│  │  if lat is None and chainage_km is not None:                 │   │
│  │      lat, lon = chainage_to_latlon(hwy, chainage_km)         │   │
│  │      if lat is None → skip record                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.4 File Layout

```
backend/
├── scripts/
│   └── build_road_centerline/
│       ├── __init__.py
│       ├── download_osm.py          # Download/load Geofabrik extract
│       ├── filter_highways.py       # Filter NH/SH ways from OSM
│       ├── assemble_routes.py       # linemerge fragmented ways
│       ├── calibrate_chainage.py    # GPS calibration points → offsets
│       ├── build_db.py              # Create road_centerlines table
│       └── chainage_to_latlon.py    # Public query function
│
├── data/
│   ├── road_centerlines.db          # Built database (SQLite + SpatiaLite)
│   └── calibration_points.csv       # Extracted from Dataful CSV
│
└── docs/
    └── road_centerline_strategy.md  # This file
```

### 5.5 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OSM missing major NH segments | Low (NH are well-mapped) | Medium | Fall back to Mapbox Directions API to infer road geometry |
| Chainage calibration fails for SH roads | High (few GPS points) | Low | SH roads are not a priority — the Dataful CSV covers primarily NH |
| GPS calibration points on wrong highway | Medium | Medium | Use median (not mean) to discard outliers. Validate with ±500m highway bounding box. |
| OSM geometry has wrong node order | Low | High | `shapely.line_merge()` handles reversal. Validate by checking that chainage increases monotonically. |
| SQLite without SpatiaLite | Medium | Low | Use in-memory geometry, not spatial index. Query performance degrades but still works (6ms → 60ms per lookup). |
| Legal: ODbL requires attribution | Certain | Low | Add `"© OpenStreetMap contributors"` to app/about page. Standard practice. |

### 5.6 Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Geometry source** | OSM (Geofabrik) | Free, complete, immediately available |
| **Chainage calibration** | Hybrid (GPS from Dataful) | Solves the origin-offset problem with available data |
| **NHAI GIS pursuit** | Parallel (non-blocking) | RTI can take weeks; proceed with Hybrid in the meantime |
| **Database** | SQLite + Shapely (no SpatiaLite) | Avoids SpatiaLite compilation complexity. In-memory `shapely.interpolate()` is fast enough for batch import (~6ms/call). |
| **Storage format** | Pickled GeoDataFrame or SQLite BLOB | For < 600 NH geometries (~50MB total), either is fine. Pickle is simpler. |
| **Refresh cadence** | Quarterly | OSM NH geometry rarely changes (roads don't move). Calibration improves as more GPS data arrives. |
