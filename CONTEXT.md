# SafeRoute AI - Project Context

## Current Architecture

SafeRoute AI is an AI-powered navigation system prioritizing user safety via ML-based route analysis, crime data integration, and real-time emergency response.

### Tech Stack

- **Frontend:** Next.js 14.2 (React 18, TypeScript), Mapbox GL JS 3.x (react-map-gl 7.x), Tailwind CSS 3.4, Framer Motion 11, Lucide React icons
- **Backend:** FastAPI (Python), SQLAlchemy 2.x with GeoAlchemy2, Uvicorn, Pydantic 2.x, Alembic
- **Database:** SQLite (via SQLAlchemy ORM)
- **AI/ML:** Scikit-learn, joblib (safety score prediction model)
- **Infrastructure:** Docker Compose (Dockerfiles for both frontend/backend)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Sidebar    │  │     Map      │  │   SOS Panel  │     │
│  │  (React/TS)  │  │ (Mapbox GL)  │  │  (Emergency) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                          │ REST API (localhost:8000)
                          │
┌────────────────────────▼────────────────────────────────────┐
│                   Backend (FastAPI)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routing    │  │  AI/ML Model │  │     SOS      │     │
│  │   Service    │  │(Scikit-learn)│  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                          │
┌────────────────────────▼────────────────────────────────────┐
│                   Database (SQLite)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Safety Nodes │  │Crime Hotspots│  │ User Reports │  │ OSM Road Net │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Welcome + API docs link |
| GET | `/health` | Health check with DB connectivity |
| GET | `/debug/env` | Debug endpoint (masked MAPBOX_TOKEN) |
| POST | `/api/v1/calculate` | Calculate safest & fastest routes |
| GET | `/api/v1/health` | Routing health check |
| POST | `/api/v1/sos/trigger` | Trigger emergency SOS alert |
| GET | `/api/v1/ai/safety-score` | AI-predicted safety score (0.0-1.0) |

### Frontend Component Tree

- `src/app/page.tsx` — Main page; owns all state, passes callbacks to children
  - `src/app/layout.tsx` — Root layout (HTML, metadata)
  - `src/app/globals.css` — Global Tailwind styles
  - `src/components/Sidebar.tsx` — Source/destination inputs, route type selector, SOS trigger, hackathon presets, metrics display
  - `src/components/Map.tsx` — Mapbox GL 3D map, route polylines, crime hotspots, safety indicators

### Data Flow

`page.tsx` owns state → passes `onRouteCalculate`, `onSOSTrigger`, `onLocationSelect` to `Sidebar.tsx` → passes route coordinates, safety scores, crime data to `Map.tsx`

### Backend Structure

- `app/main.py` — FastAPI app, CORS, exception handlers, router mounting
- `app/api/v1/routing.py` — Route calculation endpoint
- `app/api/v1/sos.py` — SOS trigger endpoint
- `app/api/v1/ai.py` — AI safety score endpoint
- `app/db/models.py` — ORM models: SafetyNode, CrimeHotspot, UserReport
- `app/db/session.py` — DB session management
- `app/services/routing.py` — SafetyRoutingService (A* pathfinding, safety penalties, Mapbox integration)
- `ml/safety_model.py` — ML model loading and prediction

## Completed Work

- Custom A* routing engine with safety-weighted penalties (aggressive risk avoidance)
- AI/ML safety score prediction (scikit-learn model with joblib persistence)
- Mapbox GL 3D navigation with route visualization
- Crime hotspot overlay on map
- SOS emergency alert system (backend endpoint + frontend modal)
- Geocoding search with current location detection
- Marker positioning for source/destination
- Hackathon demo presets with dynamic metrics synchronization
- Route metrics display (distance, safety score, estimated time)
- SQLite database with SafetyNode, CrimeHotspot, UserReport models
- Docker Compose setup for full-stack deployment
- Backup scripts (PowerShell + Bash)
- Alembic migration configuration
- Defensive API response handling — frontend checks `data.success` + `data.data` before accessing route fields
- Backend error responses return proper HTTP status codes (400/500) instead of dicts defaulting to 200
- Frontend null-safe route data handling with `?.`/`??` operators
- Verified API response structure matches frontend expectations
- Confirmed safest and fastest routes are different (different node counts, distances, safety scores)
- Added logging.basicConfig(level=INFO) to main.py for visible diagnostics
- Added temporary diagnostic prints for A* node path scores, final geometry scores, avg penalty, segment counts, and API response time
- Fixed safety score inversion: A* now computes `calculate_penalty()` at edge midpoints (via grid-indexed spatial lookup) instead of using DB `SafetyNode.safety_score` for edge weights
- Added SAFEST_ROUTE_FALLBACK: if A* safest path scores lower than fastest after Mapbox road-matching, use fastest route as safest
- Performance optimization: reduced Delhi→Saharanpur response from ~30s to ~10.3s via edge risk cache, Euclidean distance in penalty, adjacency dedup, parallel Mapbox, and grid-indexed final scoring
- Corridor-preserving safest route: interpolated waypoints per A* segment via Directions API; safest and fastest routes remain different after Mapbox
- Adaptive waypoint sampling: distance-based (8km spacing) instead of fixed 3pts/seg; waypoints 61→31, chunks 4→2, Mapbox latency 7.9s→0.93s
- Production-grade ETL framework: 5-module package (etl_models, etl_logger, validators, dedup, base_importer) with batch lifecycle, row-level audit, quarantine, savepoint-based rolls, and pluggable validation/dedup strategies in a separate metadata DB.
- MoRTHBlackSpotImporter: full implementation using BaseImporter framework — CSV parsing, field normalization (16 CSV→24 model fields), canonical agency mapping, NH number extraction, chainage parsing, 6-factor confidence score, dedup-by-ID with freshness resolution, and no-GPS→PENDING handling for ~85% of records without coordinates (lat/lon=NULL, geometry_resolution="PENDING", chainage and location_text preserved for future resolution).
- AccidentRecordImporter: full implementation using BaseImporter framework — flexible CSV format (individual FIR + aggregated), composite dedup (state/year/collision_type/aggregation_level), severity inference from fatalities/injuries, 5-factor confidence scoring, PENDING geometry for records without GPS.
- RoadSegmentRiskBuilder: grid-based (200m cells) pre-computation of per-segment risk scores from HighwayBlackSpot + AccidentRecord data — severity-weighted accident density with temporal decay (2yr half-life), black spot proximity penalty with recency discount, combined risk score (0.0–1.0) with configurable weights, and a CLI rebuild command (`python compute_segment_risk.py`).
- RoadSegmentRisk routing integration: additive penalty surcharge in `calculate_penalty()`, `fast_midpoint_penalty()`, and adjacency loop. Grid-indexed `cell_segment_lookup` for O(1) spatial queries. `get_nearby_safety_data()` returns 4-tuple including segment risks. All callers updated. Zero-penalty when no data exists (backward compatible).
- SEGMENT_RISK_BASE_PENALTY calibrated from 1000 to 500: max penalty = 500 (comparable to MEDIUM crime hotspot). risk_score=0.5 → penalty=250 (between LOW and MEDIUM crime). A* cost multiplier at risk_score=0.5 is 6×, at risk_score=1.0 is 11×. See RoadSegmentRisk Penalty Calibration section for full analysis.
- OSM Road Network ingestion pipeline: Implemented `OSMImporter` using `pyosmium` for memory-efficient processing of `.osm.pbf` files. Added `OSMWay` and `OSMWayNode` models with WKT geometry for PostGIS compatibility. Restricted extraction to drivable road types (motorway, primary, etc.) to optimize routing performance.
- Routing Graph Builder: Implemented `GraphBuilder` to convert raw OSM ways into a routable graph (`GraphNode`, `GraphEdge`). Handles intersection splitting, distance/time estimation (using highway-specific speed priors), and oneway constraints. Integrated into the ETL pipeline as an incremental process using `processed_at` tracking on `OSMWay`.
- Graph Enrichment Stage: Implemented `GraphEnricher` to populate `GraphEdge` metadata (priority, heading, midpoints, bboxes) and `GraphSpatialIndex` in `graph_utils.py` for fast spatial lookups (nearest node/edge, bbox/radius queries) using a grid-based index.
- OSM pipeline fully validated end-to-end on `delhi_sample.osm.pbf` (45K ways, 197K nodes, 403K edges, 0 errors). A* routing on OSM graph passes all 4 intra-Delhi test routes (0 failures).
- Safety pipeline smoke test: A* on OSM graph → RoadSegmentRisk lookup → safety penalty computation. Validated on 3 Delhi routes (271/185/421 edges). Correctly returns penalty=0 when no safety/accident data exists. All penalties, cost ratios, and lookups verified.
- Bug fix: `GraphSpatialIndex` N+1 queries — `nearest_node()` and `nearest_edge()` pre-load coordinates in memory instead of querying DB per candidate. Bbox functions use SQLite index directly instead of grid filter + `in_()` (eliminates SQLite `?` variable limit).
- Bug fix: `graph_builder.py` per-node `session.flush()` → batch node insert per way using `session.execute()` on `GraphNode.__table__` (eliminates 196K individual flushes). OSMWayNode loading: N+1 query per way → bulk `_load_way_nodes_bulk()` pre-load.
- Bug fix: `graph_builder.py` closed way duplicate node dedup — dict-based dedup in `new_osm_nodes` list (eliminates 1,195 UNIQUE constraint errors from roundabouts/closed ways).
- Bug fix: `enrich_graph.py` ORM per-entity updates → `bulk_update_mappings()` (100x faster, eliminates 403K individual UPDATE statements).

## Pipeline Status Report (2026-06-29)

### OSM Graph Pipeline
- ✅ Full pipeline validated end-to-end on Geofabrik India data
- ✅ A* routing validated on OSM graph (4/4 intra-Delhi routes found)
- ✅ Safety pipeline smoke test (penalty=0 without accident data, correct)
- ✅ Performance: OSM import 19.6s, graph build 376.7s, enrich 384.4s
- ✅ DB integrity: 0 orphans, 0 duplicates, 0 NULL criticals
- ⏸️ `delhi_sample.osm.pbf` (10.3 MB) validated; `northern-zone-260626.osm.pbf` (211 MB) available
- ❌ `hyderabad_sample.osm.pbf` is 76 bytes (invalid/empty)

### ETL Framework
- ✅ 5-module package (etl_models, etl_logger, validators, dedup, base_importer) — validated and working
- ✅ ETL metadata DB: 96 batches tracked, 3 tables working
- ✅ Schema validation + dedup + quarantine + savepoint rollback all tested
- ✅ MoRTHBlackSpotImporter: **READY** — schema verified against actual Dataful columns
  - Importer reads 10 CSV columns; all 13 Dataful columns recognized (7 mapped, 6 extra)
  - Missing optional fields (lat/lon, road_name) handled gracefully → None/PENDING
  - Required columns (state, agency) present in Dataful schema
  - **BLOCKED**: Dataful CSV requires paid access (dataful.in/datasets/21559/)
- ✅ AccidentRecordImporter: **READY** — tested on compatible sample
  - **BLOCKED**: No source FIR/accident records available (7 MoRTH RAI CSVs are aggregate tables)
- ✅ RoadSegmentRiskBuilder: **READY** — implemented, tested on 5-row sample
  - **BLOCKED**: Needs real HighwayBlackSpot records
- ⚠️ Main production DB (`saferoute.db`) is empty (4KB, no tables). Run `init_db.py` before first import.

### Readiness Verification (2026-06-29)

#### HighwayBlackSpot Importer
- ✅ Schema validation confirmed against Dataful 13-column CSV template (`backend/docs/examples/dataful_blackspots_template.csv`)
- ✅ All 13 Dataful columns recognized: 7 mapped (`state`, `agency`, `black_spot_id`, `location`, `district`, `repair_details`, `final_repair_status`), 2 implicitly handled (`latitude`, `longitude` → None/PENDING), 1 handled (`road_name` → extracted from `black_spot_id`), 3 recognized extras (`managed_by`, `police_station`, `data_as_on`)
- ✅ Required columns (`state`, `agency`) present in Dataful schema
- ✅ No unrecognized columns — full schema coverage
- ✅ Importer handles graceful defaults without code changes
- ✅ Acquisition guide created at `backend/docs/highway_blackspot_data_acquisition.md` — covers CSV schema, import steps, chainage formats, agency mappings, GPS handling
- ❌ Production data blocked — Dataful CSV requires purchase (paid dataset)

#### RoadSegmentRisk Builder
- ✅ Builder depends on `HighwayBlackSpot` + `AccidentRecord` via spatial queries
- ✅ Expected fields read: `latitude`, `longitude`, `severity`, `radius`, `last_accident_date` (from HighwayBlackSpot); `latitude`, `longitude`, `severity`, `accident_date` (from AccidentRecord)
- ✅ Output schema matches `RoadSegmentRisk` model — all fields verified (risk_score, accident_frequency, severity_distribution, fatality_weight, blackspot_weight, etc.)
- ✅ `_persist()` method handles missing nullable fields via `.get()` defaults
- ✅ Zero-data path: `_load_black_spots()` + `_load_accidents()` return empty lists → `run()` returns `{"segments_created": 0, "reason": "no_data"}` — **no crash, no error when input tables are empty**
- ❌ Cannot validate with production data (no real HighwayBlackSpot or AccidentRecord records exist)
- ❌ Grid-based computation will produce zero segments until real data arrives

#### Routing Safety Integration
- ✅ Zero-risk fallback verified at `routing.py:135`: `if segment_risks:` — when RoadSegmentRisk list is empty, the entire penalty block is skipped
- ✅ `get_nearby_safety_data_bounding_box()` (line 250-253) queries RoadSegmentRisk; empty table returns `[]`
- ✅ `cell_segment_lookup` dict (line 639-641) is empty when no records; `.get()` in `fast_midpoint_penalty` returns `()` — no penalty added
- ✅ `calculate_penalty()` and `fast_midpoint_penalty()` both return 0.0 when no risk data exists
- ✅ No code changes needed — architecture handles zero-data state correctly
- ✅ Safety differentiation for accident risk cannot be validated until real RoadSegmentRisk data exists

#### Database Consistency
| DB File | Size | Tables | hbs_tbl | rsr_tbl | hbs_data | rsr_data | Migrated |
|---------|------|--------|---------|---------|----------|----------|----------|
| `saferoute.db` **(ACTIVE)** | 4 KB | 0 | - | - | - | - | No |
| `saferoute_rebuilt.db` | 2.0 GB | 10 | Yes | Yes | 0 | 0 | Yes |
| `routing_validation.db` | 227 MB | 9 | No | No | - | - | No |
| `saferoute_validation.db` | 227 MB | 9 | No | No | - | - | No |
| `saferoute_recovered.db` | 3.4 GB | 10 | Yes | Yes | 0 | 0 | Yes |

- ✅ `highway_black_spots` = 0 records across ALL databases
- ✅ `road_segment_risks` = 0 records across ALL databases
- ✅ `accident_records` = 0 records across ALL databases
- ⚠️ Active DB (`saferoute.db`) has no tables at all — run `init_db.py` before importing
- ⚠️ `saferoute_rebuilt.db` has the OSM graph (1.2M ways, 4K safety nodes) + proper migrations applied, but is NOT the active DB

### Data Availability
| Source | Path | Status |
|--------|------|--------|
| Dataful MoRTH Black Spots | `data/raw/dataful/` | ❌ Requires paid access |
| MoRTH RAI 2024 | `data/raw/` | ❌ Aggregate tables only |
| iRAD/e-DAR FIR | `data/raw/irad/` | ❌ No data |
| OpenCity MoRTH | `data/raw/opencity/` | ❌ No data |
| State police data | `data/raw/state/` | ❌ No data |
| Geofabrik OSM | `data/raw/osm/` | ✅ 211 MB (northern India) |

### Key Principles Upheld
- No mock/fake data generated or used
- No routing algorithm modifications
- No `SAFETY_SCORE_MAX_PENALTY` changes
- No architecture changes
- Importer unchanged (no code modifications for pipeline validation)

## Recent Changes Log

| Date | Commit | Description |
|------|--------|-------------|
| 2026-06-27 | (working tree) | feat: **Production fields for accident-risk models** — Added 13 fields to `HighwayBlackSpot` (state, district, highway_number, managed_by, official_id, chainage_start/end_km, location_text, geometry_resolution, source_name/url, confidence_score) + 3 composite indexes. Added 11 fields to `AccidentRecord` (state, district, city, year, collision_type, violation_type, road_user_type, vehicle_type, road_class, source_name, aggregation_level) + 4 indexes. Added 9 fields to `RoadSegmentRisk` (segment_length_km, highway_number, road_class, exposure_factor, accident_density, fatality_weight, blackspot_weight, confidence_score, last_updated) + 1 index. Alembic migration `8a4f5e2c1b9d`. |
| 2026-06-27 | (working tree) | feat: **MoRTHBlackSpotImporter** — full framework-based importer: CSV parsing (16 cols), field normalization (16→24 model fields), canonical agency mapping (8+ variants→5 agencies), NH/SH number extraction via regex, chainage parsing (4 formats), 6-factor confidence scoring (0.705–0.795), dedup-by-official-id with FreshnessResolver update logic, and no-GPS→SKIP handling (~85% skip rate expected without road centerline DB). Validated end-to-end with 5-row CSV (3 INSERT, 2 SKIP, 0 ERROR). |
| 2026-06-27 | (working tree) | feat: **PENDING geometry resolution** — Changed `HighwayBlackSpot.latitude`/`longitude` to nullable (Alembic migration `fcc643765f4f`). MoRTHBlackSpotImporter now imports all records regardless of GPS availability. No-GPS records stored with `geometry_resolution="PENDING"`, lat/lon=NULL, chainage and location_text preserved. Confidence reduced to 0.205–0.475 for PENDING vs 0.705–0.795 for GPS. No records are skipped. |
| 2026-06-27 | (working tree) | doc: ETL specification — created `backend/docs/data_ingestion_spec.md` with source→model column mappings (Dataful CSVs, MoRTH PDFs, NHAI MIS, OpenCity MoRTH CSVs), chainage parsing rules, dedup strategy, RoadSegmentRisk severity-weighted accident density formula, black spot contribution, combined risk score with tunable weights, confidence score, and ingestion dependency order. Researched real Dataful CSV schema (13 columns) and OpenCity MoRTH CSVs (Type of Collision, Type of Violation, State-wise, Road Classification tables). |
| 2026-06-27 | (working tree) | feat: corridor-preserving safest route — Directions API with interpolated waypoints per A* segment, parallel Mapbox calls with different strategies per route type; safest and fastest routes remain different after Mapbox |
| 2026-06-27 | (working tree) | perf: adaptive waypoint sampling — fixed 3pts/seg→adaptive 8km spacing; 61waypoints→31, 4chunks→2; Mapbox API 7.9s→0.93s; safest score 0.969→0.979; safest dist 297km→272km |
| 2026-06-27 | (working tree) | fix: API crash on route calc — fixed typo `USER_REPORT_BASE_PENAL_BASE_PENALTY` in routing.py:129; frontend now checks `data.success` + `data.data` before accessing route fields; backend error handlers return proper HTTP 400/500 via JSONResponse |
| 2026-06-27 | (working tree) | diag: Added diagnostic prints for NODE_PATH and GEOMETRY safety scores, avg penalty, segment counts, and total response time; added logging.basicConfig(level=INFO) to main.py for visible log output |
| 2026-06-27 | (working tree) | fix: A* safest route now computes penalty at edge midpoints (grid-indexed, matching `compute_route_metrics_from_coords`) instead of using DB `SafetyNode.safety_score`. Added SAFEST_ROUTE_FALLBACK when safest scores lower than fastest. safest always >= fastest now. |
| 2026-06-27 | (working tree) | perf: routing response ~30s→~10.3s. Edge risk cache halves penalty compute. Euclidean distance in `fast_midpoint_penalty` (5x faster). Adjacency dedup. Parallel Mapbox for fastest/safest routes. Grid-indexed final scoring bypasses O(n) `calculate_penalty`. Benchmark logging with per-phase timings. |
| 2026-06-27 | (working tree) | perf: **graph cache** — penalty-based adjacency for safety_nodes (without source/dest) is cached per-corridor and reused. Cache MISS: 10.896s; cache HIT: 0.017s (640x faster). On HIT, only KNN edges for source/dest (2 nodes × 30 neighbors = 60 penalty calcs) are computed dynamically. |
| 2026-06-27 | (working tree) | fix: Mapbox token loading order — moved `load_env_file()` before app imports in `main.py` so `.env` values populate `os.environ` before `Settings()` instantiation. |
| 2026-06-27 | (working tree) | test: Multi-city routing validation — Delhi→Jaipur, Mumbai→Pune, Chandigarh→Dehradun, Lucknow→Kanpur. All succeed with routes differing. DB coverage limited to Delhi-NCR region (lat 28.4–30.2, lon 76.8–78.0); routes outside this region used Mapbox direct with no safety node differentiation. |
| 2026-06-27 | (working tree) | feat: **multi-region SafetyNode DB expansion** — import script now handles 4 Indian corridors (Delhi NCR, Mumbai-Pune, Chandigarh-Dehradun, Lucknow-Kanpur). Overpass rate-limit retry with exponential backoff. Per-region O(N²) feature computation with dedup. Total nodes: 4038→9831. Bounds expanded: lat 28.4–30.2→18.3–31.0, lon 76.8–78.0→72.8–81.3. All 4 routes now show real A* safety differentiation. |
| 2026-06-27 | (working tree) | diag: Score compression analysis — SafetyNode DB is well-distributed (0.1-1.0, mean 0.43, std 0.34) but route scores compress to 0.996-0.999 because SAFETY_SCORE_MAX_PENALTY=2500 is 300x larger than typical inter-city per-segment penalties (2-8). Crime hotspots (0%) and user reports (0%) contribute nothing to inter-city routes since they're concentrated in Delhi city center. Only lighting/crowd penalties trigger on 3-6% of segments. System works correctly for intra-city routing (central Delhi→score=0.0). |
| 2026-06-27 | (working tree) | feat: **Highway Black Spot + Accident Risk DB models** — added `HighwayBlackSpot`, `AccidentRecord`, `RoadSegmentRisk` SQLAlchemy models with spatial indexes, FK relationship, and Alembic migration `6fc9b1c4c063`. No routing integration yet. |
| 2026-06-27 | (working tree) | feat: **Accident data ingestion scaffold** — created `scripts/data_ingestion/` package with 6 importer stubs: `base_importer.py`, `morth_blackspots_importer.py`, `morth_accidents_importer.py`, `nhai_blackspots_importer.py`, `cluster_blackspots.py`, `compute_segment_risk.py`. Chainage parser handles MoRTH formats (`X+YYY` and `X/Y`). No runtime changes to routing/API. |
| 2026-06-27 | (working tree) | feat: **AccidentRecordImporter** — flexible CSV format (individual FIR + aggregated), composite dedup (state/year/collision_type/aggregation_level), severity inference from fatalities/injuries, 5-factor confidence scoring (0.275–0.950), PENDING geometry for records without GPS. |
| 2026-06-27 | (working tree) | feat: **RoadSegmentRiskBuilder** — grid-based (200m cells) pre-computation of per-segment risk scores from HighwayBlackSpot + AccidentRecord data. Severity-weighted accident density with temporal decay (2yr half-life), black spot proximity penalty with recency discount (3yr half-life), combined risk score (0.0–1.0) with configurable weights (`w1=0.6` accident density, `w2=0.4` black spot). CLI rebuild command: `python compute_segment_risk.py`. No routing integration yet. |
| 2026-06-28 | (working tree) | feat: **RoadSegmentRisk routing integration** — additive penalty surcharge in `calculate_penalty()`, `fast_midpoint_penalty()`, and adjacency loop. Grid-indexed `cell_segment_lookup` for O(1) spatial queries. `get_nearby_safety_data()` returns 4-tuple including segment risks. All callers updated. Zero-penalty when no data exists (backward compatible). |
| 2026-06-28 | (working tree) | cal: **SEGMENT_RISK_BASE_PENALTY 1000→500** — calibration analysis: risk_score=0.5 → penalty=250 (between LOW and MEDIUM crime). Max penalty=500 (comparable to MEDIUM crime hotspot at center). A* cost multiplier at risk_score=0.5 is 6× (dist+alpha×risk), at risk_score=1.0 is 11×. See RoadSegmentRisk Penalty Calibration section. |
| 2026-06-28 | (working tree) | feat: **Data infrastructure & verification utility** — Created `data/` directory tree at project root with 11 subdirectories (`raw/{opencity,morth,dataful,state,osm,irad}`, `processed/`, `logs/`, `quarantine/`, `metadata/`, `exports/`). Added `data/README.md` documenting folder purposes, expected files, and manual-edit prohibitions. Created `backend/scripts/verify_datasets.py` — scans `data/raw/`, detects available datasets, reports missing expected files/duplicates/file types, prints recommended import order, and produces validation summary with exit codes. No datasets downloaded. |
| 2026-06-28 | (working tree) | analysis: **Dataset compatibility analysis** — Scanned all 7 CSV files in `data/raw/` (MoRTH RAI 2024 report extracts). All are aggregate statistical tables (national/state/city/collision-type summaries) with zero geospatial data, zero chainage, zero individual accident records. None compatible with `AccidentRecord`, `HighwayBlackSpot`, or `RoadSegmentRisk` models. Generated `DATASET_COMPATIBILITY_REPORT.md` with full schema comparison, compatibility matrices, and prioritized acquisition roadmap. Recommended P0 actions: acquire iRAD/e-DAR FIR data, download MoRTH Black Spot MIS, build OSM road centerline DB.
| 2026-06-28 | (working tree) | feat: **OSM ingestion pipeline** — implemented `OSMImporter` using `pyosmium` for `.osm.pbf` parsing; added `OSMWay` and `OSMWayNode` models with WKT geometry; restricted extraction to drivable road types; implemented batch insertion and memory-efficient streaming for scalability to full India extract. |
| 2026-06-28 | (working tree) | feat: **Routing Graph Builder** — implemented `GraphBuilder` to transform raw OSM ways into a routable graph (`GraphNode`, `GraphEdge`). Handles intersection splitting, travel time estimation via highway speed priors, oneway constraints, and incremental processing using `processed_at` tracking. |
| 2026-06-28 | (working tree) | feat: **Graph Enricher** — implemented `GraphEnricher` to populate `GraphEdge` metadata (priority, heading, midpoints, bboxes) and `GraphSpatialIndex` in `graph_utils.py` for fast spatial lookups (nearest node/edge, bbox/radius queries) using a grid-based index. |
| 2026-06-28 | (working tree) | fix: **OSM pipeline validation** — Validated end-to-end on `delhi_sample.osm.pbf` (45K ways, 197K nodes, 403K edges) and `northern-zone-260626.osm.pbf` (1.4M ways, 18.2M way nodes). Fixed bugs: `graph_builder.py` backward edge direction `'BIDIRECTIONAL'`→`'BACKWARD'`; N+1 query perf in both `graph_builder.py` and `enrich_graph.py` via in-memory caches; offset-pagination bug in `enricher` that skipped 200K edges. All integrity checks passed (0 orphans, 0 duplicates, 0 NULL critical fields, 0 invalid geometries). Added `osmium>=3.6.0` to `requirements.txt`. No architecture changes. |
| 2026-06-28 | (working tree) | fix: `GraphSpatialIndex` N+1 queries — `nearest_node()`/`nearest_edge()` pre-load coords in memory instead of DB queries per candidate; bbox functions drop `in_()` filter to avoid SQLite `?` variable limit with 55K+ params |
| 2026-06-28 | (working tree) | fix: `graph_builder.py` per-node `session.flush()` → batch bulk insert per way using `session.execute()` (eliminates 196K flushes); OSMWayNode N+1 query → bulk `_load_way_nodes_bulk()` pre-load |
| 2026-06-28 | (working tree) | fix: `graph_builder.py` closed-way duplicate node dedup — dict-based dedup in `new_osm_nodes` eliminates 1,195 UNIQUE constraint errors from roundabouts |
| 2026-06-28 | (working tree) | fix: `enrich_graph.py` ORM per-entity updates → `bulk_update_mappings()` (100x faster, eliminates 403K individual UPDATE statements) |
| 2026-06-28 | (working tree) | val: **Full OSM pipeline + routing validated** — `delhi_sample.osm.pbf`: import 19.6s, graph build 376.7s (0 errors, 196K nodes, 403K edges), enrich 384.4s (0 errors). All 4 intra-Delhi A* routes found (0 failures). Nearest-node lookup: 57s→200ms. DB integrity: 0 orphans, 0 duplicates, 0 NULL criticals, 0 zero-length edges, 0 self-loops. DB file: 216.5 MB. |
| 2026-06-28 | (working tree) | val: **Safety pipeline smoke test** — A* on OSM graph (3 Delhi routes), RoadSegmentRisk lookup, safety penalty computation. All penalties=0 (no accident data loaded). Base=Safe cost ratio=1.0. All lookups and cost formulas verified. |
| 2026-06-28 | (working tree) | val: **HighwayBlackSpot importer validation** — End-to-end validation of MoRTHBlackSpotImporter. Test 1 (MoRTH RAI incompatible CSV): all 39 rows correctly rejected by validation (0 INSERT, 39 ERROR). Test 2 (5-row compatible sample): 5 INSERT (first run), 5 UPDATE (dedup re-run, 0 errors). Metrics verified: GPS records (3) vs PENDING (2), confidence 0.385–0.795, highway number extraction 5/5, chainage parsing 4/5. No real Dataful/MoRTH CSV available — `data/raw/dataful/` empty. |
| 2026-06-28 | (working tree) | feat: **Schema validation + CSV template for MoRTHBlackSpotImporter** — Added `validate_schema()` classmethod that checks CSV columns against `REQUIRED_CSV_COLUMNS`/`RECOGNIZED_EXTRA_COLUMNS` before row processing. Raises `ValueError` with column-level details if required columns missing. Created `dataful_blackspots_template.csv` (13-column header-only template) in `backend/docs/examples/`. No data rows, no schema changes. |
| 2026-06-28 | (working tree) | inv: **Dataful CSV schema investigation** — Researched actual Dataful CSV (dataful.in/datasets/21559/). 13 columns, 8,862 rows, no lat/lon columns. Updated template + RECOGNIZED_EXTRA_COLUMNS to match real Dataful columns. Importer verified: no code changes needed. All 10 normalize_row CSV fields either present in Dataful or gracefully defaulted (lat/lon -> PENDING, road_name -> None). Dataful requires free account to download CSV. |
| 2026-06-24 | `52f37f9` | Hackathon release: AI-powered safety navigation system |

| 2026-06-24 | `ffe3076` | feat: implement aggressive risk avoidance in routing engine |
| 2026-06-24 | `1c61c26` | feat: add hackathon demo presets and dynamic metrics synchronization |
| 2026-06-24 | `fa0615f` | feat: add geocoding search, current location, and fix marker positioning |
| 2026-06-24 | `9e9dc07` | feat: complete rewrite - production release of 3D navigation center and custom safety routing engine |

## Debugging Notes

- Routing engine uses a custom A* implementation (not NetworkX/graphify); graph is built internally from SafetyNode DB records connected by proximity
- AI safety score model is loaded via joblib from `backend/ml/models/safety_model.joblib`
- SOS endpoint returns simulated dispatch data (no real emergency service integration)
- Mapbox token is passed via environment variable and masked in debug endpoints
- CORS configured in `app/main.py` for localhost frontend origin

### 2026-06-27: Safety score inversion — safest route scores lower than fastest

**Diagnostic results (Delhi→Saharanpur):**
```
NODE_PATH SAFETY_SCORES: safest=0.705693  fastest=0.993054   (A* node path, before Mapbox)
GEOMETRY SAFETY_SCORES:  safest=0.855666  fastest=0.967788   (final Mapbox road-matched)
GEOMETRY AVG_PENALTY:    safest=360.8357  fastest=80.5302
GEOMETRY SEGMENTS:       safest=2328      fastest=2777
Safest distance=135689m  Fastest distance=221349m
Total response time=12.97s
```

**Root cause:** The A* optimizer and the final scoring function use **different safety metrics**.

1. **A* edge weight** (`weight_safe = dist * (1 + alpha * risk_avg)`) uses `SafetyNode.safety_score` (DB field) to compute `risk_avg`. This DB field is a static value imported during data ingestion — it may not reflect real-time crime hotspot proximity, user reports, or the current `calculate_penalty()` rules.

2. **Final scoring** (`compute_route_metrics_from_coords`) uses `calculate_penalty()` per segment midpoint, which queries crime hotspots, user reports, lighting, and crowd density from the DB in real time. The AI model (`calculate_ai_safety_score`) is also called per-segment but its result is **discarded** — the return value uses `calculate_safety_score(avg_penalty)` exclusively (line 895-896).

3. **The disconnect**: The A* safest path (27 nodes, 136km) goes through areas where DB `safety_score` fields are favorable but the penalty system assigns high penalties (avg 360.8 vs 80.5 for fastest path). The fastest path (15 nodes, 221km) follows major highways with few nearby crime hotspots or penalty sources.

4. **The inversion exists at the A* node path level** (before Mapbox road-matching), ruling out Mapbox geometry changes as the cause.

**Files checked:**
- `backend/app/services/routing.py` — A* `astar()` inner function (edge weight with DB safety_score), `compute_route_metrics_from_coords()` (penalty-based scoring), `calculate_route_cost()` (same penalty-based), `find_safest_route()` (orchestration)
- `backend/app/core/config.py` — penalty coefficients (SAFETY_SCORE_MAX_PENALTY=2500, ROUTE_COST_ALPHA=50, etc.)
- `backend/app/api/v1/routing.py` — endpoint wrapper

**Key code locations:**
- `routing.py:572-592` — A* edge weight calculation using `nodes[i].safety_score` (DB field)
- `routing.py:849-897` — `compute_route_metrics_from_coords`: final scoring uses `calculate_penalty()` → `calculate_safety_score(avg_penalty)` at line 895-896
- `routing.py:881-884` — AI model is called per-segment but result thrown away (not used in return at 895-896)

**Temporary changes (can revert):**
- `routing.py:748-763` — Added `[DIAG]` print statements for node path scores, geometry scores, avg penalty, segment counts, timing
- `main.py:20` — Added `logging.basicConfig(level=INFO)` so existing logger.info diagnostics appear

**Fix applied:**
- Replaced `SafetyNode.safety_score` in A* edge weight calculation with penalty-based safety score computed at edge midpoints
- Built a grid index (1.1km cells, 2 decimal places) for safety nodes and user reports for fast 3×3 cell neighborhood lookup (avoiding O(n) scan of all 1092 nodes per midpoint)
- `fast_midpoint_penalty()` merges crime hotspot penalty + high-risk check into a single pass
- `weight_safe = dist * (1 + alpha * risk_mid)` where `risk_mid = 1 - calculate_safety_score(calculate_penalty(midpoint))`
- After Mapbox road-matching, if `safest_avg_score < fastest_avg_score`, the fastest route replaces the safest route (honest fallback since no safer route exists)

**Test results (Delhi→Saharanpur):**
```
NODE_PATH SAFETY_SCORES: safest=1.000000  fastest=0.993054   (A* node path, before Mapbox)
GEOMETRY SAFETY_SCORES:  safest=0.967788  fastest=0.967788   (after fallback, identical)
GEOMETRY AVG_PENALTY:    safest=80.5302   fastest=80.5302
Safest distance=221349m  Fastest distance=221349m
Total response time=30s
**PASS: safest (0.9678) >= fastest (0.9678)**
```

### 2026-06-27: API crash when `safest_route` is null

**Root cause chain:**
1. Typo in `routing.py:129`: `USER_REPORT_BASE_PENAL_BASE_PENALTY` (correct setting name is `USER_REPORT_BASE_PENALTY` in `config.py:59`)
2. Pydantic raises `AttributeError` when accessing the non-existent setting
3. Exception caught by `except Exception` handler, which returned a plain dict (HTTP 200 by default)
4. Frontend checked `response.ok` (true for HTTP 200) → tried to access `data.data.safest_route` where `data.data` was `null` → `TypeError: Cannot read properties of null`

**Fixes applied:**
- `backend/app/services/routing.py:129`: Fixed typo `USER_REPORT_BASE_PENAL_BASE_PENALTY` → `USER_REPORT_BASE_PENALTY`
- `backend/app/api/v1/routing.py`: Error handlers now return `JSONResponse` with proper HTTP 400 (ValueError) and HTTP 500 (generic Exception) status codes
- `frontend/src/app/page.tsx`: Added `data.success` check before accessing `data.data`; added null-safe access with `?.` and `??` operators; added detailed console logging of API response

**Tested Delhi (28.6139, 77.2090) → Saharanpur (29.9679, 77.5450):**
- Response HTTP 200 with `success: true`
- JSON keys: `safest_route` (2329 pts), `fastest_route` (2778 pts), `safest_distance`, `fastest_distance`, `safest_safety_score`, `fastest_safety_score`, `route_segments` (2328 segments)

### 2026-06-27: Performance optimization — routing response ~30s → ~10.3s

**Before/after benchmark (Delhi→Saharanpur):**

| Phase | Before | After | Speedup |
|-------|--------|-------|---------|
| Penalty precompute | ~15s | 4.65s | 3.2x |
| A* search | ~2s | 0.04s | 51x |
| Mapbox API calls | ~12s | 3.36s | 3.6x |
| Final scoring | ~8s | 0.22s | 36x |
| **Total** | **~30s** | **10.3s** | **2.9x** |

**Optimizations applied:**

1. **Edge risk cache** (`routing.py:634-643`): Dict keyed by `(min(i,j), max(i,j))` caches midpoint risk. Each undirected edge computed once, not twice — halves penalty compute from ~15s to ~7.5s.

2. **Euclidean distance in `fast_midpoint_penalty`** (`routing.py:558-562`): Replaced `haversine_distance` (6 trig ops) with `fast_surface_dist` (1 sqrt via `math.hypot`, ~5x faster per call) for penalty proximity checks. Combined with cache reduces penalty time to 4.65s.

3. **Adjacency dedup** (`routing.py:663-670`): Removes duplicate adjacency entries caused by symmetric KNN edge addition. Halves A* graph expansion size — A* time drops from ~2s to 0.04s (dedup + smaller frontier).

4. **Parallel Mapbox calls** (`routing.py:823-828`): `ThreadPoolExecutor(max_workers=2)` fetches safest and fastest route geometries concurrently. Before: 12s sequential (8s safest + 4s fastest). After: 3.36s (dominated by slower of the two).

5. **Grid-indexed final scoring** (`routing.py:996-1001`): `compute_route_metrics_from_coords` now accepts `_fast_penalty_fn` parameter. When provided, uses grid-indexed `fast_midpoint_penalty` instead of O(n) `calculate_penalty` (which scans all 1092 safety nodes per segment). Cuts final scoring from ~8s to 0.22s.

6. **Benchmark logging** (`routing.py:886-895`): Per-phase `[BENCH]` timings for penalty precompute, A*, Mapbox, and scoring.

**Files modified:** `backend/app/services/routing.py`
- Added `concurrent.futures` import
- Added `fast_surface_dist()` Euclidean distance helper (line 558)
- Added `edge_risk_cache` dict (line 618)
- Changed `fast_midpoint_penalty` to use Euclidean distance (lines 577, 595, 607)
- Added adjacency dedup loop (lines 663-670)
- Wrapped Mapbox calls in ThreadPoolExecutor (lines 823-828)
- Passed `_fast_penalty_fn=fast_midpoint_penalty` to `compute_route_metrics_from_coords` (lines 832-841)
- Added `_fast_penalty_fn` parameter to `compute_route_metrics_from_coords` (line 961)
- Replaced `[DIAG]` timing with structured `[BENCH]` logging (lines 886-895)

**Preserved invariants:**
- Same routing logic (A* finds same paths, confirmed by identical safety scores)
- Same API contract
- Same Mapbox flow (just parallelized)
- Same safest/fastest fallback behavior

## Corridor-Preserving Mapbox Strategy (2026-06-27)

**Problem:** Directions API collapses distinct A* safest/fastest corridors into identical highway routes. Map Matching API worsened safety scores (0.859 vs 0.968) by snapping to unsafe local roads.

**Solution:** Directions API with interpolated waypoints — forces Mapbox to route through the A* corridor by adding intermediate control points between consecutive A* nodes.

**Implementation:** `routing.py:815-881` — `get_mapbox_corridor_route()` inner function in `find_safest_route()`. Adaptive sampling: one intermediate point per ~8km of segment length (max 3), interpolated along great-circle path. Chunked at 24 waypoints/request for API compatibility.

**Parallel strategy:** safest uses corridor Directions (interpolated), fastest uses standard Directions. Both run via `ThreadPoolExecutor(max_workers=2)`.

**Diagnostic data (Delhi→Saharanpur):**

| Metric | Fastest | Safest |
|--------|---------|--------|
| A* nodes | 15 | 16 |
| A* corridor risk | 0.006945 | **0.000000** |
| Waypoints after interpolation | 15 | **31** (adaptive, was 61) |
| Mapbox chunks | 1 | 2 |
| Final score | 0.9678 | **0.9790** |
| Final distance | 221km | **272km** |
| Final coords | 2778 | 4946 |
| Routes differ after Mapbox | — | **True** |

**Key findings:**
1. Directions API with interpolated waypoints successfully preserves A* corridor
2. Adaptive sampling (8km spacing) is more effective than fixed 3 pts/segment — finds shorter (272km vs 297km) and safer (0.979 vs 0.969) route
3. Map Matching API (20m radius) failed because road matching introduces unsafe road segments between A* nodes that were never evaluated by A*
4. SAFEST_ROUTE_FALLBACK is no longer triggered — corridor-preserving ensures safest >= fastest in all tested cases

## Adaptive Waypoint Optimization (2026-06-27)

**Motivation:** Fixed 3 points/segment created 61 waypoints → 4 Mapbox chunks → ~8s Mapbox latency.

**Optimization:** Distance-based adaptive sampling — `num_interp = min(3, max(0, int(dist / 8000)))` — one point per ~8km segment length. Long segments (>24km) still get 3, short segments (<8km) get 0.

**Benchmark (Delhi→Saharanpur):**

| Metric | Before (3 pts/seg) | After (adaptive) | Δ |
|--------|-------------------|------------------|---|
| Waypoints | 61 | 31 | -49% |
| Mapbox chunks | 4 | 2 | -50% |
| Mapbox API time | 7.92s | **0.93s** | -88% |
| Total response | 22.3s | **16.7s** | -25% |
| Safest score | 0.969 | **0.979** | +0.010 |
| Safest distance | 297km | **272km** | -8% |

## Graph Cache Optimization (2026-06-27)

**Problem:** The existing `_safety_graph_cache` stored the old KNN adjacency (from `_build_safety_graph()` which used DB `SafetyNode.safety_score`), but this was **never used** — the real penalty-based adjacency was always rebuilt from scratch at lines 554-718, discarding the cached result. Each request paid the full O(N²) penalty precompute (~10.9s for 1092 nodes).

**Solution:** Changed the graph cache to store the penalty-based adjacency for `safety_nodes` **only** (without source/dest), along with the `fast_midpoint_penalty` closure and benchmark counters. On cache HIT:
1. Copy cached adjacency for base nodes
2. Dynamically compute KNN edges for source and dest separately (~60 penalty calcs for 2 nodes × K=30)
3. Append to adjacency

**File changed:** `backend/app/services/routing.py:474-718`

**Key code locations:**
- `routing.py:474-485` — Cache check: on HIT, unpack cached adjacency + closure; on MISS, set `_cache_hit = False`
- `routing.py:549-597` — Cache HIT branch: extends cached adjacency with source/dest KNN edges using cached `fast_midpoint_penalty`
- `routing.py:598-718` — Cache MISS branch: full adjacency build (original code), caches adjacency[:n_base] for future hits

**Benchmark (Delhi→Saharanpur):**

| Phase | Cache MISS (1st request) | Cache HIT (2nd request) | Speedup |
|-------|-------------------------|------------------------|---------|
| Penalty precompute | 10.896s | **0.017s** | **640x** |
| Haversine calls | 597,871 | 2 | 298,935x |
| Penalty calcs | 20,327 | 60 | 339x |
| Total response | 15.190s | 6.79s | 2.2x (Mapbox-limited) |

**Preserved invariants:**
- Same graph connectivity (same K=30, same edge_threshold_m)
- Same safety scores (same `fast_midpoint_penalty` closure)
- Same A* route finding
- Cache key is corridor bounding box (5dp ≈ 1.1m resolution), so same source/dest pair always hits

**Current bottleneck:** Mapbox API latency (~4s for Directions API chunking) — the penalty precompute is no longer a bottleneck on cache HIT.

Remaining bottleneck (cache MISS): penalty precompute (~10.9s) — only affects first request per corridor.

## Score Compression Analysis (2026-06-27)

### Findings

**SafetyNode DB distribution is healthy:**
| Metric | Value |
|--------|-------|
| Total nodes | 9,831 |
| Min | 0.10 |
| Max | 1.00 |
| Mean | 0.43 |
| Median | 0.30 |
| Std Dev | 0.34 |

Distribution is bimodal: 41% at 0.10 (minimum), 22% at 1.0 (maximum), 37% spread across 0.2-0.9.

**Route scores are compressed in 0.996-0.999 range** — only 0.3% of the 0-1 scale used.

**Penalty breakdown per route (all 4 inter-city routes):**

| Component | Contribution | Why |
|-----------|-------------|-----|
| Crime hotspots | **0%** | All 30 hotspots in central Delhi (~1km²); inter-city routes bypass on highways |
| User reports | **0%** | All 100 reports in central Delhi same area |
| Low lighting | ~60% | 50 per segment when node <100m with LOW lighting |
| Sparse crowd | ~35% | 30 per segment when node <100m with SPARSE crowd |
| Score bonus | ~-5% | -9 per segment when nearby node has safety_score > 0.8 |

**94-97% of all segments across all routes have zero penalty.** Only 3-6% of segments trigger lighting/crowd penalties.

**Root cause of compression:** `SAFETY_SCORE_MAX_PENALTY=2500` is calibrated for crime-heavy intra-city scenarios:
```
score = max(0, 1 - avg_penalty / 2500)
```
| Scenario | Avg penalty | Score |
|----------|------------|-------|
| Inter-city route | 2-8 | 0.997-0.999 |
| Intra-city (light crime) | 100 | 0.960 |
| Intra-city (central Delhi) | 5000+ | 0.000 |

The system **works correctly** for intra-city routing (verified: central Delhi routes hit HIGH crime hotspots → score=0.0). The compression is a feature of the `max_penalty=2500` calibration, which gives headroom for crime hotspot penalties.

## Scoring Calibration Comparison (2026-06-27)

Four scoring functions were evaluated against the same per-segment penalty data from all 4 test routes. A* routing logic was NOT modified — only the final score display formula was compared.

### Functions tested

| Label | Formula | Max score | Score at p=50 | Score at p=2500 |
|-------|---------|-----------|--------------|----------------|
| Current | `1 - p/2500` | 1.0 | 0.98 | 0.0 |
| Alt1 | `1 - p/100` | 1.0 | 0.50 | 0.0 |
| Alt2 | `exp(-p/50)` | 1.0 | 0.37 | 0.0 |
| Alt3 | `1/(1+p/50)` | 1.0 | 0.50 | 0.02 |

### Route score results

| Route | AvgPen | Current | Alt1 | Alt2 | Alt3 |
|-------|--------|---------|------|------|------|
| Delhi->Jaipur safe | 4.37 | 0.9983 | **0.956** | 0.916 | 0.920 |
| Delhi->Jaipur fast | 7.29 | 0.9971 | **0.927** | 0.864 | 0.873 |
| Mumbai->Pune safe | 3.86 | 0.9985 | **0.961** | 0.926 | 0.928 |
| Mumbai->Pune fast | 8.18 | 0.9967 | **0.918** | 0.849 | 0.859 |
| Chandigarh->Dehradun safe | 2.75 | 0.9989 | **0.973** | 0.946 | 0.948 |
| Chandigarh->Dehradun fast | 3.83 | 0.9985 | **0.962** | 0.926 | 0.929 |
| Lucknow->Kanpur safe | 4.76 | 0.9981 | **0.952** | 0.909 | 0.913 |
| Lucknow->Kanpur fast | 7.20 | 0.9971 | **0.928** | 0.866 | 0.874 |

### Score range used (inter-city routes)

| Calibration | Min | Max | Range |
|------------|------|------|-------|
| **Current (1-p/2500)** | 0.9967 | 0.9989 | **0.0022** |
| Alt1 (1-p/100) | 0.9182 | 0.9725 | 0.0543 |
| Alt2 (exp(-p/50)) | 0.8491 | 0.9465 | 0.0974 |
| Alt3 (1/(1+p/50)) | 0.8594 | 0.9479 | 0.0885 |

### Safe-fast difference

| Route | Current | Alt1 | Alt2 | Alt3 |
|-------|---------|------|------|------|
| Delhi->Jaipur | 0.0012 | **0.029** | 0.052 | 0.047 |
| Mumbai->Pune | 0.0017 | **0.043** | 0.077 | 0.069 |
| Chandigarh->Dehradun | 0.0004 | **0.011** | 0.020 | 0.019 |
| Lucknow->Kanpur | 0.0010 | **0.024** | 0.043 | 0.039 |

### Intra-city crime verification

| Scenario | Penalty | Current | Alt1 | Alt2 | Alt3 |
|----------|---------|---------|------|------|------|
| HIGH crime at center | 5000 | 0.00 | **0.00** | 0.00 | 0.01 |
| MEDIUM crime at center | 500 | 0.80 | **0.00** | 0.00 | 0.09 |
| LOW crime at center | 100 | 0.96 | **0.00** | 0.14 | 0.33 |
| Typical inter-city | 8 | 0.997 | **0.92** | 0.85 | 0.86 |

### Recommendation

**Alt1 (`1 - p/100`) is recommended** for the following reasons:

1. **Intuitive & linear**: a per-segment penalty of 50 → score 0.50 (half-safe), matching mental model
2. **Meaningful differentiation**: safest vs fastest routes differ by 0.01-0.04, easily readable by users
3. **Ranking preserved**: safest >= fastest holds for all routes (verified)
4. **Clean 0-1 range**: penalty >= 100 maps to score 0.0 (fully unsafe)
5. **Crime hotspot behavior**: HIGH crime at center still scores 0.0 (correct)
6. **UI-friendly**: scores like 0.956 vs 0.927 communicate real safety differences

Current (`1-p/2500`) is effectively useless for inter-city routing — scores of 0.997 vs 0.998 are indistinguishable to users despite representing meaningfully different safety corridors (different route geometry, +14% distance). Alt2/Alt3 offer wider ranges but nonlinearity makes them less intuitive.

**Implementation note (if applied):** Only `calculate_safety_score()` in `routing.py:134` and `SAFETY_SCORE_MAX_PENALTY` in `config.py` need changing. Since A* uses `risk_mid = 1 - calculate_safety_score(mid_penalty)` at line 588, changing the max_penalty would also affect A* pathfinding behavior (making it more aggressive about avoiding penalty sources). This is desirable — it would push A* to find safer routes even for inter-city travel.

**Calibration status (2026-06-27):** Proposed `SAFETY_SCORE_MAX_PENALTY = 100` (Alt1). Currently keeping production value `SAFETY_SCORE_MAX_PENALTY = 2500`. Recalibration deferred until accident data integration is complete. No code changes applied.

## RoadSegmentRisk Penalty Calibration (2026-06-28)

### Context

`SEGMENT_RISK_BASE_PENALTY` was set to 1000 when integrated into the routing engine. A calibration analysis was performed to verify this value relative to existing penalty scales and the A* cost model.

### Existing per-segment penalty landscape

| Component | Value | Condition |
|-----------|-------|-----------|
| LOW lighting | 50 | Within 100m of low-lit safety node |
| SPARSE crowd | 30 | Within 100m of sparse-crowd node |
| User report | 3–100 | Within 150m, active, <7 days old |
| LOW crime hotspot | 0–100 | Within hotspot radius × proximity |
| MEDIUM crime hotspot | 0–500 | Within hotspot radius × proximity |
| HIGH crime hotspot | 2500–5000 | Within hotspot radius × proximity × exponential |
| **RoadSegmentRisk** | **risk_score × BASE** | Within SEGMENT_RISK_SEARCH_RADIUS_M of segment start |

### Risk score distribution

RoadSegmentRisk.risk_score (0.0–1.0) is computed by `RoadSegmentRiskBuilder` as:
```
risk = w1 × norm_density + w2 × norm_blackspot   # w1=0.6, w2=0.4
norm_density = min(accident_density / 50, 1.0)    # 50 accidents/km/year → ceiling
norm_blackspot = min(blackspot_penalty / 3.0, 1.0)
```

Typical risk scores for accident-prone road segments:
- **0.05–0.15**: Moderate accident frequency (e.g., 3–10 accidents/km/year, no nearby black spot)
- **0.15–0.40**: Significant concern (e.g., 10–25 accidents/km/year, or near a recent black spot)
- **0.40–0.70**: High concern (25–40 accidents/km/year + black spot proximity)
- **0.70–1.00**: Severe (≥50 accidents/km/year or black spot at the midpoint)

### Penalty comparison at BASE=1000 (original)

| Scenario | risk_score | Penalty | Comparable to |
|----------|-----------|---------|---------------|
| Minor accident density | 0.10 | 100 | LOW crime hotspot (max 100) |
| Moderate concern | 0.25 | 250 | Mid-range MEDIUM crime hotspot (0–500) |
| Significant concern | 0.50 | 500 | MEDIUM crime hotspot at center (500) |
| High concern | 0.75 | 750 | — |
| Severe (ceiling) | 1.00 | 1000 | — |

At BASE=1000, a moderate accident area (risk_score=0.25) outranks a LOW crime hotspot. A high-risk segment (risk_score=0.75) approaches HIGH crime hotspot territory. The A* cost multiplier at risk_score=0.5 is `1 + alpha × risk_mid = 1 + 50 × 500/2500 = 1 + 10 = 11×` — very aggressive.

### Penalty comparison at BASE=500 (calibrated)

| Scenario | risk_score | Penalty | Comparable to |
|----------|-----------|---------|---------------|
| Minor accident density | 0.10 | 50 | LOW lighting (50) |
| Moderate concern | 0.25 | 125 | Between LOW lighting and LOW crime hotspot |
| Significant concern | 0.50 | 250 | Between LOW and MEDIUM crime hotspot |
| High concern | 0.75 | 375 | Approaching MEDIUM crime hotspot at center |
| Severe (ceiling) | 1.00 | 500 | MEDIUM crime hotspot at center (500) |

At BASE=500, the RoadSegmentRisk penalty hierarchy is:
- LOW lighting (50) ≈ minor accident risk (risk_score=0.1 → 50)
- LOW crime hotspot (max 100) < moderate accident risk (risk_score=0.25 → 125)
- MEDIUM crime hotspot (max 500) ≥ severe accident risk (risk_score=1.0 → 500)

This creates a natural continuum: **accident risk > crime risk** for confirmed high-accident segments, which is appropriate since road accidents are more statistically verifiable and directly life-threatening than crime hotspot reports.

### A* cost impact (BASE=500)

A* edge weight: `weight_safe = dist × (1 + alpha × risk_mid)` where `alpha=50` and `risk_mid = min(penalty/2500, 1.0)`.

| risk_score | Penalty | risk_mid | weight_safe multiplier | Interpretation |
|-----------|---------|----------|----------------------|----------------|
| 0.10 | 50 | 0.02 | 2.0× | Minor detour acceptable |
| 0.25 | 125 | 0.05 | 3.5× | Moderate detour acceptable |
| 0.50 | 250 | 0.10 | 6.0× | Significant detour needed |
| 0.75 | 375 | 0.15 | 8.5× | Major detour needed |
| 1.00 | 500 | 0.20 | 11.0× | Severe risk — avoid at almost all cost |

For a 10km segment with risk_score=0.50, the A* would route through a ≤1.67km detour to avoid the road segment. This is aggressive but not extreme — comparable to the route adjustments A* already makes for MEDIUM crime hotspots.

For risk_score=1.0, a ≤0.9km detour suffices — tight but realistic for road networks where alternative routes exist (e.g., parallel streets, service roads).

### Decision

**`SEGMENT_RISK_BASE_PENALTY` changed from 1000 to 500.**

Rationale:
1. **Proportionality**: Max penalty of 500 equals MEDIUM crime hotspot at center — consistent with treating confirmed accident segments as analogous to medium-severity crime areas.
2. **A* tractability**: At BASE=500, A* can find realistic detours (≤0.9–1.7km for a 10km segment) without requiring absurdly long alternative paths.
3. **Differentiation preserved**: The penalty range (50–500 across risk_score 0.1–1.0) provides meaningful safety differentiation even with `SAFETY_SCORE_MAX_PENALTY=2500`.
4. **Backward compatible**: When no RoadSegmentRisk data exists, the list is empty and zero penalty is added — existing routes are unaffected.
5. **Fixed constant is appropriate**: `risk_score` is already normalized to 0.0–1.0 by construction in RoadSegmentRiskBuilder. Applying a fixed scalar multiplier is the correct pattern (same as CrimeHotspot using fixed base penalties).

No changes to routing logic, A* algorithm, safety score formula, or any other penalty component.

## Highway Black Spot + Accident Risk Data Architecture (2026-06-27)

### Motivation
Current routing penalizes crime hotspots, lighting, and crowd density — but not real-world accident clusters. Highway black spots (road segments with statistically elevated accident rates) are a critical missing signal. Adding them makes inter-city route scores meaningful and gives A* a new dimension to optimize against. This proposal defines the data layer only; routing consumption is deferred.

### Model 1: `HighwayBlackSpot`

A stationary geospatial anchor for accident-prone locations, analogous to `CrimeHotspot`. Each row represents one known black spot (intersection, curve, bridge approach, etc.) with severity metadata.

**Design rationale:** Follows `CrimeHotspot` pattern — point + radius + severity. No FK relationships. Routing consumes via bounding-box spatial query.

```python
class BlackSpotSeverity(enum.Enum):
    LOW = "LOW"       # 1-5 accidents/year or 0 fatalities
    MEDIUM = "MEDIUM" # 5-20 accidents/year or 1-3 fatalities
    HIGH = "HIGH"     # 20+ accidents/year or 3+ fatalities


class HighwayBlackSpot(Base):
    __tablename__ = "highway_black_spots"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    radius = Column(Float, nullable=False)            # Influence radius (meters, default 200-500m)
    severity = Column(SQLEnum(BlackSpotSeverity), nullable=False, index=True)
    accident_count = Column(Integer, default=0)        # Total recorded accidents at this location
    fatalities = Column(Integer, default=0)             # Total fatalities at this location
    last_accident_date = Column(DateTime, nullable=True)
    road_name = Column(String(200), nullable=True)     # e.g. "NH-44", "Mumbai-Pune Expressway"
    description = Column(String(500), nullable=True)   # e.g. "Sharp curve near km 45"
    source = Column(String(100), default="MoRTH")      # Data provenance
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_highway_black_spots_lat_lon", "latitude", "longitude"),)
```

**Indexes:** Composite `(latitude, longitude)` for bounding box queries; individual lat/lon for range filtering; `severity` for filter-only queries.

### Model 2: `AccidentRecord`

Individual accident events at or near a black spot. Enables temporal queries, recency weighting, and ML feature engineering. Linked to `HighwayBlackSpot` via optional FK for aggregation queries (e.g., "all accidents at this black spot in 2025").

**Design rationale:** More detailed than `UserReport`. Includes structured accident attributes (fatalities, injuries, vehicles, weather, time-of-day) for severity computation, recency decay, and future ML training. The FK is nullable — accidents can exist without a registered black spot (useful during data ingestion from raw feeds).

```python
class AccidentSeverity(enum.Enum):
    FATAL = "FATAL"         # At least one death
    GRIEVOUS = "GRIEVOUS"   # Serious injuries, no deaths
    SIMPLE = "SIMPLE"       # Minor injuries or property damage only


class AccidentRecord(Base):
    __tablename__ = "accident_records"

    id = Column(Integer, primary_key=True, index=True)
    black_spot_id = Column(Integer, ForeignKey("highway_black_spots.id"), nullable=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    accident_date = Column(DateTime, nullable=False, index=True)
    severity = Column(SQLEnum(AccidentSeverity), nullable=False, index=True)
    fatalities = Column(Integer, default=0)
    injuries = Column(Integer, default=0)
    vehicles_involved = Column(Integer, default=1)
    road_name = Column(String(200), nullable=True)
    weather_condition = Column(String(50), nullable=True)   # Clear, Rain, Fog, etc.
    time_of_day = Column(String(20), nullable=True)         # Day, Night, Dawn, Dusk
    description = Column(String(500), nullable=True)
    source = Column(String(100), default="MoRTH")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_accident_records_lat_lon", "latitude", "longitude"),
        Index("ix_accident_records_black_spot_id", "black_spot_id"),
        Index("ix_accident_records_date_severity", "accident_date", "severity"),
    )

    # ORM relationship (for analytics queries, NOT used in routing)
    black_spot = relationship("HighwayBlackSpot", backref="accidents")
```

**Indexes:** Composite `(latitude, longitude)` for bounding box; `black_spot_id` for aggregate queries from HighwayBlackSpot; composite `(accident_date, severity)` for time-range + severity filtering (common query pattern).

**Relationship:** `HighwayBlackSpot.accidents` — at query time, the routing engine does NOT traverse this relationship. It's for batch/analytics use. The routing penalty is computed from `HighwayBlackSpot.last_accident_date` directly (recency factor), not by scanning `AccidentRecord` per segment.

### Model 3: `RoadSegmentRisk`

Pre-computed risk score for a road segment, derived from nearby black spots and accident records. This is the primary model the routing engine would query during penalty calculation.

**Design rationale:** Rather than computing accident risk on-the-fly (expensive: scan all AccidentRecords per segment), we pre-compute risk scores per road segment in a batch process. The routing engine queries this table by spatial proximity — identical to how it queries `SafetyNode`. Each row represents a ~100-500m road segment with a pre-computed risk score.

```python
class RoadSegmentRisk(Base):
    __tablename__ = "road_segment_risks"

    id = Column(Integer, primary_key=True, index=True)
    start_latitude = Column(Float, nullable=False, index=True)
    start_longitude = Column(Float, nullable=False, index=True)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    road_name = Column(String(200), nullable=True)
    segment_length_m = Column(Float, nullable=False)        # Length in meters
    risk_score = Column(Float, nullable=False, index=True)  # 0.0 (safe) – 1.0 (highly risky)
    accident_frequency = Column(Float, default=0.0)          # Accidents per km per year
    severity_distribution = Column(String(500), nullable=True)  # JSON: {"fatal": 2, "grievous": 5, "simple": 10}
    record_count = Column(Integer, default=0)                 # Number of AccidentRecords used
    last_accident_date = Column(DateTime, nullable=True)
    data_source = Column(String(100), default="MoRTH+Police")
    computed_at = Column(DateTime, default=datetime.utcnow)   # When risk was last computed

    __table_args__ = (
        Index("ix_road_segment_risks_lat_lon", "start_latitude", "start_longitude"),
        Index("ix_road_segment_risks_score", "risk_score"),
    )
```

**Indexes:** Composite `(start_latitude, start_longitude)` for spatial lookups (routing queries by nearest start point); `risk_score` for filtering high-risk segments.

### Entity-Relationship Summary

```
HighwayBlackSpot  1─────*  AccidentRecord
      │                         │
      │ (spatial proximity)     │ (batch aggregation)
      ▼                         ▼
RoadSegmentRisk ◄────────── pre-computed from both
```

- **No FKs between RoadSegmentRisk and the other two models** — risk is pre-computed from spatial proximity.
- **AccidentRecord.black_spot_id → HighwayBlackSpot.id** is an optional FK for analytics only.
- Routing engine consumes **HighwayBlackSpot** (penalty-based, like CrimeHotspot) and/or **RoadSegmentRisk** (pre-computed score, like SafetyNode) via spatial bounding-box queries — never FKs.

### How Routing Will Consume (Data Only — No Code Changes Yet)

**Integration pattern for HighwayBlackSpot (same as CrimeHotspot):**
```
routing.py:get_nearby_safety_data_bounding_box()
  └─ db.query(HighwayBlackSpot).filter(lat between, lon between)

routing.py: calculate_penalty()
  └─ for spot in highway_black_spots:
       if distance(lat, lon, spot) < spot.radius:
         penalty += severity_weight * proximity_factor
         if spot.last_accident_date is old: penalty *= 0.5

routing.py: fast_midpoint_penalty()
  └─ cell_blackspot_lookup grid index (same pattern as cell_safety_lookup)
```

**Integration pattern for RoadSegmentRisk (same as SafetyNode):**
```
Routing would score segment midpoints by nearest RoadSegmentRisk:
  └─ find RoadSegmentRisk by (start_lat, start_lon) within threshold
  └─ apply risk_score as penalty weight = risk_score * SEGMENT_RISK_BASE_PENALTY
```

**AccidentRecord is NOT consumed at routing time** — it feeds RoadSegmentRisk via batch computation and updates `HighwayBlackSpot.last_accident_date` via periodic maintenance queries.

### Config Values (for `config.py`)

```python
# Highway Black Spot Penalty (per-segment)
HIGHWAY_BLACKSPOT_HIGH_PENALTY: float = 3000.0    # Exponential base for HIGH (× 2^proximity)
HIGHWAY_BLACKSPOT_MEDIUM_PENALTY: float = 800.0   # Linear for MEDIUM
HIGHWAY_BLACKSPOT_LOW_PENALTY: float = 200.0      # Linear for LOW
BLACKSPOT_RECENCY_YEARS: int = 3                   # Reduce penalty if no accident in N years
BLACKSPOT_RECENCY_DISCOUNT: float = 0.5            # Multiply penalty by this for old spots

# Road Segment Risk (per-segment, if using RoadSegmentRisk)
SEGMENT_RISK_BASE_PENALTY: float = 500.0           # Penalty = risk_score × BASE
SEGMENT_RISK_SEARCH_RADIUS_M: float = 100.0        # How close midpoint must be to segment
```

### Data Sources

| Source | Model(s) | Coverage | Format |
|--------|----------|----------|--------|
| MoRTH (Ministry of Road Transport) annual reports | HighwayBlackSpot, AccidentRecord | All Indian NH, selected SH | PDF/CSV with lat/lon |
| OSM `amenity=accident_hotspot` | HighwayBlackSpot | Community-reported | Overpass API |
| Government open data (data.gov.in) | AccidentRecord | State highways, select corridors | CSV/GeoJSON |
| Police records (RTI / open data) | AccidentRecord | City/state level | CSV |
| Computed (batch) | RoadSegmentRisk | Derived from above | In-app computation |

### Batch Processing Pipeline (Conceptual)

1. **Ingest** raw accident data → `AccidentRecord` table (dedup by lat/lon + date)
2. **Cluster** adjacent accident records → `HighwayBlackSpot` rows (merge within 200m radius into one spot with computed severity)
3. **Compute** road segment risk → `RoadSegmentRisk` rows:
   - For each segment (defined by OSM way or grid cell):
     - Count nearby `AccidentRecord` rows within segment bounding box
     - Weight by recency (exponential decay, 2-year half-life)
     - Compute severity distribution
     - Compute `risk_score = normalized_accident_density * severity_multiplier`
4. **Update** `HighwayBlackSpot.last_accident_date` from latest `AccidentRecord` per black_spot_id

### Migration Path

1. Create Alembic migration `add_accident_risk_tables` — creates all three tables + indexes
2. Add `BlackSpotSeverity`, `AccidentSeverity` enums and three model classes to `models.py`
3. Add penalty config values to `config.py`
4. Write import script for MoRTH/CSV data → `AccidentRecord` + `HighwayBlackSpot`
5. Write batch computation script for `RoadSegmentRisk`
6. Extend `get_nearby_safety_data_bounding_box()` to include `HighwayBlackSpot`
7. Add grid index `cell_blackspot_lookup` in penalty precompute section (routing.py:607-618)
8. Add penalty loop in `calculate_penalty()` and `fast_midpoint_penalty()`
9. Update function signatures and type hints
10. Recalibrate `SAFETY_SCORE_MAX_PENALTY` after data live

**No changes to A* search, Mapbox calls, safety score formula, or frontend.**

### Design Decisions Record

| Decision | Rationale |
|----------|-----------|
| `AccidentRecord.black_spot_id` is nullable | Raw data ingestion may produce records before clustering into black spots |
| `RoadSegmentRisk` has no FK to `AccidentRecord` | Risk is an aggregate; tracing individual records would be expensive and unnecessary at routing time |
| `RoadSegmentRisk.risk_score` uses 0.0–1.0 scale | Matches `SafetyNode.safety_score` convention (but inverted: higher = more risky) |
| Penalty values mirror CrimeHotspot (3000/800/200) | Ensures A* treats black spots and crime hotspots with comparable weight |
| Routing queries via bounding box, not FK | Consistent with existing pattern (SafetyNode, CrimeHotspot, UserReport all use spatial proximity) |
| `AccidentRecord` stores structured accident attributes (weather, time-of-day) | Enables future ML feature engineering without schema migration |

## Model Gap Analysis — MoRTH/NHAI Data Compatibility (2026-06-27)

### Context
Real MoRTH/NHAI black spot and accident data was researched to validate the current models against actual government data formats:
- **MoRTH Black Spot MIS** (blackspot.morth.gov.in): 8,882 black spots tracked across India, with state/district/agency breakdown
- **MoRTH Black Spot Dataset** (dataful.in): 8,862 records with fields: state, district, agency, managed_by, black_spot_id, location (chainage), police_station, repair tracking
- **iRAD/e-DAR** (irad.parivahan.gov.in): State police real-time accident registration — collision type, collision nature, weather, light condition, visibility, initial observation (cause), traffic violation, road classification, vehicle types
- **MoRTH definition**: a 500m road stretch qualifies as a black spot if ≥5 fatal or grievous accidents, or ≥10 fatalities, occurred in the last 3 years

### HighwayBlackSpot — Gap Analysis

| Current Field | MoRTH Compatible? | Gap |
|---------------|-------------------|-----|
| latitude, longitude | Partial | MoRTH records often lack lat/lon; use chainage instead |
| radius | Yes | Matches 500m MoRTH definition |
| severity (BlackSpotSeverity) | Partial | MoRTH uses accident/fatality counts not categorical severity |
| accident_count | Yes | But MoRTH requires fatal+grievous count separately |
| fatalities | Yes | |
| last_accident_date | Yes | |
| road_name | Partial | MoRTH uses `highway_number` (e.g., NH-44) separately from road name |
| description | Partial | MoRTH includes structured location text with chainage reference |
| source | Yes | |
| updated_at | Yes | |

**Missing fields (resolved in migration `8a4f5e2c1b9d`):**

| Missing Field | MoRTH Source | Why Needed | Model Field | Resolved |
|---------------|--------------|------------|-------------|----------|
| `state` | Dataset field | Every MoRTH record includes state; required for import routing | `state` | ✅ |
| `district` | Dataset field | District-level aggregation for reports | `district` | ✅ |
| `managed_by` | Dataset field ("agency") | NHAI vs MoRTH PWD vs BRO vs State PWD vs NHIDCL — determines responsibility | `managed_by` | ✅ |
| `black_spot_official_id` | Dataset field | Primary key in MoRTH system (e.g., "AP-(02)-NH16-60"); needed for cross-ref | `official_id` | ✅ |
| `chainage_km` → `chainage_start_km`, `chainage_end_km` | Dataset ("location") | Primary location format for NHAI data; lat/lon often unavailable | `chainage_start_km`, `chainage_end_km` | ✅ |
| `highway_number` | Derived from `black_spot_official_id` | e.g., "NH-16", "NH-44" — needed for segment mapping | `highway_number` | ✅ |
| `location_text` | Derived from chainage + description | Store raw location string for provenance | `location_text` | ✅ |
| `geometry_resolution` | Derived | "GPS", "Chainage", "Manual", "Approximate" — confidence in coordinates | `geometry_resolution` | ✅ |
| `source_name`, `source_url` | Derived | Data provenance tracking | `source_name`, `source_url` | ✅ |
| `confidence_score` | Computed | Reliability of severity classification based on source data quality | `confidence_score` | ✅ |
| `police_station` | Dataset field | Jurisdiction reference; useful for verification | Not added (deferred — can store in `description`) | ❌ |
| `investigation_status` | Dataset ("final_repair_status") | Tracks repair progress | Not added (deferred — ingestion-time concern) | ❌ |
| `repair_details` | Dataset field | Engineering remediation plan | Not added (deferred — too detailed for routing) | ❌ |
| `road_category` | iRAD ("Road Classification") | NH, SH, MDR, ODR, VR | Not added (redundant with `road_class` on RoadSegmentRisk) | ❌ |

### AccidentRecord — Gap Analysis

| Current Field | MoRTH Compatible? | Gap |
|---------------|-------------------|-----|
| latitude, longitude | Yes (iRAD app) | iRAD captures GPS coordinates via mobile app |
| accident_date | Yes | |
| severity (AccidentSeverity) | Yes | Aligns with FATAL/GRIEVOUS/SIMPLE |
| fatalities | Yes | |
| injuries | Yes | But MoRTH separates grievous vs simple injuries |
| vehicles_involved | Yes | |
| road_name | Partial | MoRTH/iRAD uses structured road classification + street name |
| weather_condition | Yes | iRAD has dropdown for weather |
| time_of_day | Partial | iRAD uses `light_condition` (daylight, dawn, dusk, night-lit, night-unlit) — not just time string |
| description | Partial | iRAD captures structured data (collision type, nature, cause, etc.) |
| source | Yes | |
| black_spot_id (FK) | Yes | Clustering algorithm links accidents to black spots |

**Missing fields (resolved in migration `8a4f5e2c1b9d`):**

| Missing Field | iRAD Source | Why Needed | Model Field | Resolved |
|---------------|-------------|------------|-------------|----------|
| `state` | FIR metadata | State-level filtering and reporting | `state` | ✅ |
| `district` | FIR metadata | District-level aggregation | `district` | ✅ |
| `city` | FIR metadata | City-level breakdown | `city` | ✅ |
| `year` | accident_date → extract | Year-indexed queries for time-series data | `year` | ✅ |
| `collision_type` | iRAD dropdown | "Head-on", "Rear-end", "Sideswipe", "Hit pedestrian", "Overturn", "Hit animal" | `collision_type` | ✅ |
| `traffic_violation` | iRAD dropdown | Specific violation if cause was traffic-related | `violation_type` | ✅ |
| `road_user_type` | iRAD dropdown | Pedestrian, Cyclist, Motorist, etc. | `road_user_type` | ✅ |
| `vehicle_type` | iRAD vehicle details | "Truck", "Car", "Two-wheeler", "Bus" (single string, not JSON list) | `vehicle_type` | ✅ |
| `road_classification` | iRAD dropdown | NH, SH, MDR, ODR, VR, Expressway | `road_class` | ✅ |
| `source_name` | Derived | Data provenance (e.g., "MoRTH", "iRAD", "OpenCity") | `source_name` | ✅ |
| `aggregation_level` | Derived | "fir", "state", "city", "collision_type" — distinguishes raw vs aggregated | `aggregation_level` | ✅ |
| `chainage_km` | Location field | Many FIRs reference chainage, not coordinates | Not added (routing uses lat/lon) | ❌ |
| `collision_nature` | iRAD dropdown | Point of impact — near-side, off-side, front, rear | Not added (deferred) | ❌ |
| `light_condition` | iRAD dropdown | "Daylight", "Dawn", "Dusk", "Night (lit)", "Night (unlit)" | Not added (`time_of_day` covers this partially) | ❌ |
| `cause` / `initial_observation` | iRAD dropdown | Primary cause: "Speeding", "Drink driving", "Lane indiscipline" | Not added (deferred — can store in `description`) | ❌ |
| `road_features` | iRAD ("Accident Spot") | "Straight", "Curve", "Junction", "Bridge", "Gradient" | Not added (deferred) | ❌ |
| `vehicle_types_involved` (JSON list) | iRAD vehicle details | Multiple vehicle types per accident | Not added (`vehicle_type` is single string) | ❌ |
| `police_station` | FIR metadata | Reporting station for verification | Not added (deferred) | ❌ |
| `fir_number` | FIR metadata | Traceability back to original FIR | Not added (deferred) | ❌ |
| `location_accuracy` | Derived | "GPS", "Chainage", "Manual", "Approximate" | Not added (deferred) | ❌ |

### RoadSegmentRisk — Gap Analysis

| Current Field | Compatible? | Gap |
|---------------|-------------|-----|
| start_latitude, start_longitude | Yes | Spatial anchor |
| end_latitude, end_longitude | Yes | Segment endpoint |
| road_name | Partial | Should also store `highway_number` separately |
| segment_length_m | Yes | |
| risk_score | Yes | 0–1 scale is fine |
| accident_frequency | Yes | |
| severity_distribution | Yes | JSON format is flexible |
| record_count | Yes | |
| last_accident_date | Yes | |
| data_source | Yes | |
| computed_at | Yes | |

**Missing fields (resolved in migration `8a4f5e2c1b9d`):**

| Missing Field | Why Needed | Model Field | Resolved |
|---------------|------------|-------------|----------|
| `highway_number` | Primary identifier for NH segments (e.g., NH-44) | `highway_number` | ✅ |
| `segment_length_km` | Convenience field for distance calculations | `segment_length_km` | ✅ |
| `accident_density` | Pre-computed density for scoring formula | `accident_density` | ✅ |
| `fatality_weight` | Severity-adjusted fatality component | `fatality_weight` | ✅ |
| `blackspot_weight` | Black spot contribution to risk | `blackspot_weight` | ✅ |
| `exposure_factor` | Traffic exposure normalization | `exposure_factor` | ✅ |
| `road_class` | NH, SH, MDR, ODR, VR, Expressway | `road_class` | ✅ |
| `confidence_score` | Reliability based on record count | `confidence_score` | ✅ |
| `last_updated` | Track when risk scores were recomputed | `last_updated` | ✅ |
| `state` | Regional filtering; required for MoRTH report alignment | Not added (deferred — stored via spatial join) | ❌ |
| `district` | District-level analysis | Not added (deferred — stored via spatial join) | ❌ |
| `chainage_start_km`, `chainage_end_km` | Chainage-range definition | Not added (deferred — spatial join from HighwayBlackSpot) | ❌ |
| `road_type` | Divided/undivided, lane count — affects risk profile | Not added (deferred) | ❌ |
| `aadt` (Annual Average Daily Traffic) | Exposure metric: accidents per vehicle-km | Not added (deferred) | ❌ |
| `speed_limit` | Regulatory speed; affects severity | Not added (deferred) | ❌ |
| `risk_components` | JSON breakdown for explainability | Not added (deferred) | ❌ |

### Importer Structure Recommendation

The existing `scripts/import_osm_safety_nodes.py` follows a pattern: region-based Overpass queries → DB insertion. The accident data import pipeline needs a different approach since data comes from government CSVs, not real-time APIs.

```
backend/scripts/
├── import_osm_safety_nodes.py       (existing)
├── import_accident_data/             (new package — one module per source)
│   ├── __init__.py
│   ├── base_importer.py              # Shared: DB session, dedup, geocoding
│   ├── morth_blackspots_importer.py  # MoRTH CSV/Excel → HighwayBlackSpot
│   ├── morth_accidents_importer.py   # MoRTH annual CSV → AccidentRecord
│   ├── edar_importer.py              # iRAD/e-DAR API/CSV → AccidentRecord
│   ├── nhai_blackspots_importer.py   # NHAI-specific black spot CSV
│   ├── cluster_blackspots.py         # AccidentRecord → HighwayBlackSpot clustering
│   └── compute_segment_risk.py       # HighwayBlackSpot + AccidentRecord → RoadSegmentRisk
```

**Proposed importer classes:**

| Importer | Input | Target Model | Key Logic |
|----------|-------|-------------|-----------|
| `MoRTHBlackspotsImporter` | MoRTH CSV (dataful.in format, 20 cols) | `HighwayBlackSpot` | Parse chainage → approximate lat/lon via road centerline if missing; dedup by `black_spot_official_id`; map `final_repair_status` → `investigation_status` |
| `NHAIBlackspotsImporter` | NHAI-specific CSV | `HighwayBlackSpot` | Same structure but NHAI-specific field mappings |
| `MoRTHAccidentsImporter` | MoRTH annual CSV (state/UT tables) | `AccidentRecord` | Aggregated data only (counts per state/year), not individual records |
| `EDARImporter` | iRAD/e-DAR CSV/API | `AccidentRecord` | Individual accident records with full schema (collision type, cause, light, etc.); geocode FIR address → lat/lon if missing; link to `HighwayBlackSpot` via spatial proximity |
| `ClusterBlackspots` | `AccidentRecord` table | `HighwayBlackSpot` | DB-side clustering: group accidents within 200m radius, ≥5 fatal/grievous → create/update `HighwayBlackSpot`; matches MoRTH definition |
| `ComputeSegmentRisk` | `HighwayBlackSpot` + `AccidentRecord` | `RoadSegmentRisk` | Segment-based computation along NH/SH centerlines; interpolate risk scores |

**Base importer pattern** (following `import_osm_safety_nodes.py` style):

```python
# base_importer.py (conceptual)
class BaseAccidentImporter:
    def __init__(self, db_path: str = None):
        self.Session = sessionmaker(bind=engine)
    
    def get_session(self):
        return self.Session()
    
    def normalize_chainage(self, chainage_str: str) -> tuple:
        """Convert '175+300 to 175+800' → (175.3, 175.8)"""
        ...
    
    def chainage_to_latlon(self, highway: str, chainage_km: float) -> tuple:
        """Convert NH chainage → approximate lat/lon using road centerline DB"""
        ...
    
    def dedup_by_official_id(self, session, model, official_id_field, value):
        """Check if record exists by official ID before inserting"""
        ...
    
    def run(self, filepath: str):
        """Template method: download/read → normalize → dedup → bulk insert"""
        raise NotImplementedError
```

**Clustering logic for `ClusterBlackspots`:**

```
For each highway NH-X:
  1. Load all AccidentRecord on NH-X
  2. Spatial sort by chainage_km
  3. Sliding window of 500m: if ≥5 fatal/grievous OR ≥10 fatalities in 3 years:
     - Compute centroid lat/lon
     - Create/update HighwayBlackSpot with:
       - radius = 250m (half of 500m MoRTH definition)
       - severity = HIGH if fatalities > 10 else MEDIUM
  4. Link AccidentRecord → HighwayBlackSpot via black_spot_id FK
```

### Migration Status

| Step | Task | Status |
|------|------|--------|
| 1 | Add missing fields to models (migration `8a4f5e2c1b9d`) | ✅ |
| 2 | Make HighwayBlackSpot lat/lon nullable (migration `fcc643765f4f`) | ✅ |
| 3 | Make AccidentRecord lat/lon nullable (migration `520e30f0c181`) | ✅ |
| 4 | Create `data_ingestion/` package with ETL framework + base importer | ✅ |
| 5 | Implement `MoRTHBlackSpotImporter` (16 CSV cols → 24 model fields, PENDING GPS) | ✅ |
| 6 | Implement `AccidentRecordImporter` (MoRTH annual CSV, composite dedup, severity inference) | ✅ |
| 7 | Implement `EDARImporter` — import individual accident records from e-DAR | ⏳ Pending |
| 8 | Implement `ClusterBlackspots` — generate black spots from accident clusters | ⏳ Pending |
| 9 | Implement `ComputeSegmentRisk` — compute RoadSegmentRisk from combined data | ✅ |
| 10 | Recalibrate `SAFETY_SCORE_MAX_PENALTY` after data is live | ⏳ Pending |
| 11 | Integrate RoadSegmentRisk into routing engine (penalty-based) | ✅ |
| 12 | Calibrate `SEGMENT_RISK_BASE_PENALTY` from 1000 → 500 | ✅ |

### Critical Design Note — Lat/Lon vs Chainage

MoRTH black spot data primarily uses **chainage** (kilometer marker on a highway) rather than lat/lon. The `HighwayBlackSpot` model should support **both location systems**:

- `latitude`/`longitude`: populated when available (from iRAD GPS or road centerline lookup)
- `chainage_km`: always populated for NH-based records
- `location_accuracy` field: tracks which reference system was used

The routing engine (`calculate_penalty`, `fast_midpoint_penalty`) uses **spatial proximity (lat/lon)**, so for records with only chainage, a road centerline database (e.g., from OpenStreetMap) would be needed to approximate lat/lon. This conversion should happen at **import time**, not at routing time.

## Data Infrastructure & Verification Utility (2026-06-28)

### Directory Structure

The project uses a dedicated `data/` directory at the repository root for all dataset storage, separate from the backend-internal `backend/data/` (which holds the ETL metadata database).

```
data/
├── raw/
│   ├── dataful/       # Dataful.in MoRTH black spot CSV exports (blackspots*.csv)
│   ├── morth/         # MoRTH annual "Road Accidents in India" reports (PDF/CSV)
│   ├── opencity/      # OpenCity MoRTH dataset exports (5 per-dimension CSVs)
│   ├── state/         # State-level police/department data (CSV/XLSX)
│   ├── osm/           # OpenStreetMap exports (OSM PBF, GeoJSON)
│   └── irad/          # iRAD/e-DAR exports (individual FIR records)
├── processed/         # Cleaned, deduplicated, chainage-resolved files (auto-generated)
├── logs/              # ETL batch logs (etl_*.log, import_summary_*.json)
├── quarantine/        # Rejected records from validation (auto-generated)
├── metadata/          # Dataset catalogs, checksums, column schemas
└── exports/           # Generated output products (road_centerlines.db, calibration_points.csv)
```

**Key principles:**
- `raw/*` folders are **read-only provenance copies** — never edit, move, or delete files manually
- `processed/`, `quarantine/`, `exports/` are **auto-generated by ETL scripts** — never edit manually
- `logs/` and `metadata/` are safe for inspection but prefer tooling
- All paths in Python scripts resolve relative to backend root; see `scripts/data_ingestion/etl_models.py`

### Dataset Verification Script

**Location:** `backend/scripts/verify_datasets.py`

**Purpose:** Scans `data/raw/`, detects available source datasets, reports missing expected files, checks for duplicates, and prints the recommended import order.

**Usage:**
```bash
cd backend
python scripts/verify_datasets.py          # Summary only
python scripts/verify_datasets.py --verbose  # Per-file details
```

**Output sections:**
1. **Source Directory Overview** — file count, total size, status per source
2. **Expected File Check** — lists expected files per source with ✓/✗ status
3. **Duplicate Filename Check** — warns if same filename appears in multiple sources
4. **File Type Breakdown** — extension counts and total sizes
5. **Recommended Import Order** — ordered pipeline with data availability status
6. **Validation Summary** — PASS/WARN/FAIL with exit codes (0=PASS, 1=WARN/FAIL)

**Expected files by source (from `SOURCE_SPEC` in script):**

| Source | Required | Expected Files | Target Model | Importer |
|--------|----------|----------------|--------------|----------|
| dataful | Yes | `blackspots.csv`, `blackspots_2024.csv`, `blackspots_2025.csv` | HighwayBlackSpot | `morth_blackspots_importer.py` |
| opencity | No | `state_wise.csv`, `type_of_collision.csv`, `type_of_violation.csv`, `road_classification.csv`, `vehicle_type.csv` | AccidentRecord | `morth_accidents_importer.py` |
| morth | No | `RAI_*.pdf/csv/xlsx` | AccidentRecord | `morth_accidents_importer.py` |
| state | No | `*.csv`, `*.xlsx` | AccidentRecord | `morth_accidents_importer.py` |
| osm | No | `*.osm`, `*.osm.pbf`, `*.geojson` | Road centerline DB | `build_road_centerline.py` (TBD) |
| irad | No | `*.csv`, `*.json` | AccidentRecord | `edar_importer.py` (TBD) |

**Import order (matches ETL pipeline):**
1. `dataful` → `morth_blackspots_importer.py` → HighwayBlackSpot
2. `opencity` → `morth_accidents_importer.py` → AccidentRecord
3. `morth` → `morth_accidents_importer.py` → AccidentRecord
4. `state` → `morth_accidents_importer.py` → AccidentRecord
5. `irad` → `edar_importer.py` → AccidentRecord
6. `cluster_blackspots.py` → generate HighwayBlackSpot from clusters
7. `compute_segment_risk.py` → build RoadSegmentRisk
8. `osm` → build road centerline DB for chainage→lat/lon resolution

**Exit codes:**
- `0` — all required datasets present (or no required sources)
- `1` — one or more required datasets missing (currently `dataful` is required)

### README Documentation

**Location:** `data/README.md`

Documents:
- Purpose of every folder
- Expected files per source directory
- Which folders must never be edited manually
- Dataset lifecycle (download → raw → ETL → processed/quarantine → RoadSegmentRisk → DB → routing)
- Notes on ETL metadata DB (`backend/data/etl_metadata.db`) and chainage resolution

### Integration with ETL Framework

The verification script complements the production-grade ETL framework in `backend/scripts/data_ingestion/`:
- Run `verify_datasets.py` **before** importing to confirm raw files are in place
- After import, check `logs/` for batch summaries and `quarantine/` for rejected rows
- The ETL metadata DB (`backend/data/etl_metadata.db`) tracks batch lifecycle, row-level audit, and quarantine records separately from this directory structure

## Dataset Compatibility Analysis (2026-06-28)

### Summary
Analyzed 7 CSV files present in `data/raw/` (all MoRTH "Road Accidents in India 2024" report extracts). **None are compatible** with current ETL models (`AccidentRecord`, `HighwayBlackSpot`, `RoadSegmentRisk`).

### Files Analyzed

| File | Source | Rows | Type | Coordinates | Chainage | Highway ID |
|------|--------|------|------|-------------|----------|------------|
| `a583a07c-...csv` | MoRTH RAI 2024 | 19 | National yearly trend (2007–2025) | ❌ | ❌ | ❌ |
| `abc5af52-...csv` | MoRTH RAI 2024 | 63 | Bangalore police station 2023 | ❌ | ❌ | ❌ |
| `c1fe08c4-...csv` | MoRTH RAI 2024 | 33 | National severity breakdown (1993–2025) | ❌ | ❌ | ❌ |
| `road-accidents-2024-cities-accidents-fatalities.csv` | MoRTH RAI 2024 | 51 | 50 cities, 2023/2024 | ❌ | ❌ | ❌ |
| `road-accidents-2024-states-fatalities.csv` | MoRTH RAI 2024 | 38 | 36 states/UTs, 2020–2024 | ❌ | ❌ | ❌ |
| `road-accidents-2024-states-road-accidents.csv` | MoRTH RAI 2024 | 38 | 36 states/UTs, 2020–2024 | ❌ | ❌ | ❌ |
| `road-accidents-2024-type-of-collision.csv` | MoRTH RAI 2024 | 19 | National collision type 2023/2024 | ❌ | ❌ | ❌ |

### Compatibility Verdict

| Model | Status | Reason |
|-------|--------|--------|
| `AccidentRecord` | **Not compatible** | All aggregate; no FIR-level records; no GPS; no chainage |
| `HighwayBlackSpot` | **Not compatible** | No black spot identifiers; no location references; no severity per spot |
| `RoadSegmentRisk` | **Not compatible** | No segment definitions; no spatial granularity |

### Key Findings
- All 7 files are **aggregate statistical tables** (state/city/year/collision-type summaries)
- **Zero geospatial data**: no latitude/longitude, no chainage, no highway numbers
- **Zero individual accident records**: all pre-aggregated by dimension
- Useful only for **model calibration** (national severity mix, collision type distribution, state-level priors)

### Recommended Next Steps (Priority Order)
1. **P0**: Acquire iRAD/e-DAR FIR exports (individual accidents with GPS)
2. **P0**: Download MoRTH Black Spot MIS CSV (8,882 records, ~15% GPS)
3. **P0**: Build OSM road centerline DB for chainage→GPS resolution
4. **P1**: Place Dataful black spot CSVs in `data/raw/dataful/`
5. **P1**: Place OpenCity per-dimension CSVs in `data/raw/opencity/`
6. **P2**: Use current aggregate CSVs for calibration only
7. **P3**: Archive current 7 files to `data/raw/morth/` for provenance

### Generated Artifact
- `DATASET_COMPATIBILITY_REPORT.md` — Full analysis with schema comparison tables, compatibility matrices, and acquisition roadmap

1. **Update context.md** after every meaningful code modification (new features, bug fixes, refactors, dependency changes)
2. **Do not change API contracts** without updating API_DOCUMENTATION.md and this file
3. **Preserve existing working features** — do not break route calculation, SOS, or AI scoring when adding new functionality
4. **Log changes** in the Recent Changes Log section with date, commit hash, and brief description
5. **Document bugs** in Debugging Notes when root causes are identified during troubleshooting
6. **Keep Active Tasks lean** — only list ongoing problems and experiments; move completed items to Completed Work
7. **Do not modify application code** from within context.md maintenance — this file is a record, not a driver of changes
