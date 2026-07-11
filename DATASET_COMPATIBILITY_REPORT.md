# SafeRoute AI — Dataset Compatibility Analysis Report

**Generated:** 2026-06-28
**Scope:** All CSV/PDF files under `data/raw/`
**Purpose:** Evaluate compatibility with ETL models (`AccidentRecord`, `HighwayBlackSpot`, `RoadSegmentRisk`)
**Constraint:** Analysis only — no imports, no code changes, no database modifications

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total files analyzed** | 7 CSV files (0 PDF) |
| **Files in `data/raw/` (root)** | 7 |
| **Files in `data/raw/<source>/` subdirs** | 0 (all empty) |
| **Aggregate-level datasets** | 7 (100%) |
| **Accident-level (FIR) datasets** | 0 (0%) |
| **Datasets with coordinates (lat/lon)** | 0 (0%) |
| **Datasets with chainage** | 0 (0%) |
| **Datasets with road/highway identifiers** | 0 (0%) |
| **Fully compatible with current models** | 0 |
| **Partially compatible** | 0 |
| **Requires new importer / not useful** | 7 |

**Bottom line:** All available datasets are **aggregate statistical tables** from MoRTH annual reports (state/city/collision-type summaries). They contain **no geospatial data**, **no chainage**, **no individual accident records**, and **no road/highway identifiers**. None can directly populate `AccidentRecord`, `HighwayBlackSpot`, or `RoadSegmentRisk` as currently modeled.

---

## 1. Per-File Analysis

### 1.1 `a583a07c-731b-4e8d-b0cb-d06e76ccc00c.csv`
**Source:** MoRTH / data.gov.in (India road accident time series)
**Rows:** 19 data rows (2007–2025) + 1 header
**Columns:** `Year`, `Fatal Road Accidents`, `Killed`, `Non-Fatal Road Accidents`, `Total`
**Data types:** Year (int), all counts (int, comma-formatted)
**Missing values:** None
**Duplicate rows:** None (unique Year)
**Level:** **Aggregate** — national yearly totals
**Coordinates:** ❌ No
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** National-level trend of fatal/non-fatal accidents and casualties over 19 years.

---

### 1.2 `abc5af52-08a7-4435-8ba1-12b99f62ee28.csv`
**Source:** Bangalore City Police / Karnataka (station-wise 2023 data)
**Rows:** 63 data rows (including subtotals/totals) + 1 header
**Columns:** `Zone`, `Sub-division`, `Station`, `2023 - Fatal Cases`, `2023 - Killed People`, `2023 - Non-Fatal`, `2023 - Injured People`, `2023 - Total Cases`
**Data types:** Zone/Sub-division/Station (string), counts (int)
**Missing values:** Empty strings for zone/sub-division on subtotal rows
**Duplicate rows:** Subtotal rows duplicate aggregated data (e.g., `,East ,Total`, `East,,East Total`)
**Level:** **Aggregate** — police station-wise totals for 2023 only
**Coordinates:** ❌ No (station names only)
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** Bengaluru traffic police jurisdiction breakdown. Stations map to police boundaries, not road segments.

---

### 1.3 `c1fe08c4-9871-4c0b-b79b-c446f24f2c03.csv`
**Source:** MoRTH "Road Accidents in India" historical table (1993–2025)
**Rows:** 33 data rows (1993–2025) + 1 header
**Columns:** `_id`, `Year`, `Fatal_Accidents`, `Grievous_Accidents`, `Minor_Accidents`, `Non_Injury_Accidents`, `Total_Accidents`, `Persons_Killed`, `Persons_Injured`, `Total_Persons_Involved`
**Data types:** _id (int), Year (int), all counts (int)
**Missing values:** None
**Duplicate rows:** None (unique Year)
**Level:** **Aggregate** — national yearly severity breakdown
**Coordinates:** ❌ No
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** 32-year national time series with severity categories (Fatal/Grievous/Minor/Non-Injury). Note: 2024/2025 marked `(P)` = provisional.

---

### 1.4 `road-accidents-2024-cities-accidents-fatalities.csv`
**Source:** MoRTH RAI 2024 report — City-wise table
**Rows:** 50 cities + 1 total row + 1 header
**Columns:** `Sl No`, `City`, `2023 Accidents`, `2024 Accidents`, `2023 Ranking Accidents`, `2024 Ranking Accidents`, `2023 Killed`, `2024 Killed`, `2023 Ranking Killed`, `2024 Ranking Killed`, `2023 Injured`, `2024 Injured`, `2023 Ranking Injured`, `2024 Ranking Injured`
**Data types:** Sl No (int), City (string), counts (int, comma-formatted), rankings (int)
**Missing values:** None in data rows; total row has empty ranking columns
**Duplicate rows:** None (unique City)
**Level:** **Aggregate** — city-level totals for 2 years
**Coordinates:** ❌ No (city names only)
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** 50 major Indian cities with accident/killed/injured counts and rankings for 2023 vs 2024.

---

### 1.5 `road-accidents-2024-states-fatalities.csv`
**Source:** MoRTH RAI 2024 report — State-wise fatalities table
**Rows:** 36 states/UTs + 1 total + 1 footnote + 1 header
**Columns:** `Sl No`, `State`, `2020 Killed`–`2024 Killed`, `% change from 2023 to 2024`, `2020 Ranking`–`2024 Ranking`
**Data types:** Sl No (int), State (string), counts (int, comma-formatted), % change (float), rankings (int)
**Missing values:** Ladakh has `NA` for 2020; footnote row mostly empty
**Duplicate rows:** None (unique State)
**Level:** **Aggregate** — state/UT fatalities 2020–2024
**Coordinates:** ❌ No
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** 5-year fatality trend by state with YoY % change and rankings.

---

### 1.6 `road-accidents-2024-states-road-accidents.csv`
**Source:** MoRTH RAI 2024 report — State-wise total accidents table
**Rows:** 36 states/UTs + 1 total + 1 footnote + 1 header
**Columns:** `Sl No`, `State`, `2020 Accidents`–`2024 Accidents`, `Change from 2023 to 2024`, `% change from 2023 to 2024`, `2020 Ranking`–`2024 Ranking`
**Data types:** Same pattern as fatalities file
**Missing values:** Ladakh `NA` for 2020; Kerala missing 2024 ranking
**Duplicate rows:** None (unique State)
**Level:** **Aggregate** — state/UT total accidents 2020–2024
**Coordinates:** ❌ No
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** 5-year total accident trend by state with change metrics and rankings.

---

### 1.7 `road-accidents-2024-type-of-collision.csv`
**Source:** MoRTH RAI 2024 report — Collision type breakdown
**Rows:** 10 collision types (each with data row + % share row) + total + 1 header
**Columns:** `Type of collision`, `2023-Accidents`, `2023-Killed`, `2023-injured`, `2024-Accidents`, `2024-Killed`, `2024-injured`, `%Change-Accidents`, `%Change-killed`, `%Change-Injured`
**Data types:** Collision type (string), counts (int, comma-formatted), % change (float)
**Missing values:** % change columns empty for % share rows
**Duplicate rows:** Each collision type appears twice (data + % share)
**Level:** **Aggregate** — national collision-type breakdown for 2 years
**Coordinates:** ❌ No
**Chainage:** ❌ No
**Road/Highway IDs:** ❌ No

**Content:** 9 collision categories (Hit and Run, With parked Vehicle, Hit from Back, Hit from side, Run off Road, Fixed object, Vehicle overturn, Head on collision, Others) with 2023/2024 counts and YoY % change.

---

## 2. Compatibility Matrix vs ETL Models

| Dataset | AccidentRecord | HighwayBlackSpot | RoadSegmentRisk | Verdict |
|---------|---------------|------------------|-----------------|---------|
| a583a07c (national time series) | ❌ No coords, no FIR fields | ❌ No location, no chainage | ❌ No segment geometry | **Not useful** |
| abc5af52 (Bangalore stations) | ❌ Aggregate, no FIR fields | ❌ Police stations ≠ road segments | ❌ No segment geometry | **Not useful** |
| c1fe08c4 (national severity) | ❌ No coords, no accident-level | ❌ No location, no chainage | ❌ No segment geometry | **Not useful** |
| cities-accidents-fatalities | ❌ City-level aggregate | ❌ City centroid only, no road data | ❌ No segment geometry | **Not useful** |
| states-fatalities | ❌ State-level aggregate | ❌ No location, no chainage | ❌ No segment geometry | **Not useful** |
| states-road-accidents | ❌ State-level aggregate | ❌ No location, no chainage | ❌ No segment geometry | **Not useful** |
| type-of-collision | ❌ National aggregate by type | ❌ No spatial info | ❌ No segment geometry | **Not useful** |

**Legend:** ❌ = Missing critical field(s) required by model

---

## 3. Schema Mismatch Details

### 3.1 `AccidentRecord` Model Requirements (from `models.py` + migration `8a4f5e2c1b9d`)

| Required Field | Available in Any Dataset? | Notes |
|----------------|---------------------------|-------|
| `latitude` / `longitude` | ❌ No | All datasets are aggregate; no GPS |
| `accident_date` | ❌ No | Only year available, no date |
| `severity` (FATAL/GRIEVOUS/SIMPLE) | ⚠️ Partial | `c1fe08c4` has severity breakdown but national totals only |
| `fatalities` / `injuries` | ⚠️ Partial | Aggregate counts only |
| `vehicles_involved` | ❌ No | Not in any dataset |
| `road_name` | ❌ No | City/state names only |
| `weather_condition` | ❌ No | Not collected |
| `time_of_day` | ❌ No | Not collected |
| `collision_type` | ⚠️ Partial | `type-of-collision` has categories but national totals only |
| `violation_type` | ❌ No | Not collected |
| `road_user_type` | ❌ No | Not collected |
| `vehicle_type` | ❌ No | Not collected |
| `road_class` | ❌ No | Not collected |
| `source_name` | ✅ Yes | Can infer "MoRTH RAI 2024" |
| `aggregation_level` | ✅ Yes | All are "state" / "city" / "national" / "collision_type" |
| `black_spot_id` (FK) | ❌ No | No black spot linkage |
| `state` / `district` / `city` / `year` | ⚠️ Partial | State/city/year available in some; district never |

**Critical Gap:** `AccidentRecord` expects **individual accident records** (one row = one FIR/event). All 7 datasets are **pre-aggregated statistical tables**. Cannot decompose aggregates into individual records without loss of information.

---

### 3.2 `HighwayBlackSpot` Model Requirements

| Required Field | Available in Any Dataset? | Notes |
|----------------|---------------------------|-------|
| `latitude` / `longitude` | ❌ No | No geospatial data in any file |
| `radius` | ❌ No | Not applicable |
| `severity` (LOW/MEDIUM/HIGH) | ⚠️ Partial | Could infer from fatality counts but no location |
| `accident_count` | ⚠️ Partial | Aggregate totals only |
| `fatalities` | ⚠️ Partial | Aggregate totals only |
| `last_accident_date` | ❌ No | Only year available |
| `road_name` / `highway_number` | ❌ No | No road identifiers |
| `chainage_start_km` / `chainage_end_km` | ❌ No | No chainage data |
| `geometry_resolution` | ❌ No | Would be "NONE" |
| `confidence_score` | ❌ No | Cannot compute without location |
| `official_id` | ❌ No | No MoRTH black spot IDs |

**Critical Gap:** `HighwayBlackSpot` requires a **specific road location** (point + radius or chainage). All datasets are jurisdictional aggregates (state/city/police station) — cannot map to road segments.

---

### 3.3 `RoadSegmentRisk` Model Requirements

| Required Field | Available in Any Dataset? | Notes |
|----------------|---------------------------|-------|
| `start_latitude` / `start_longitude` | ❌ No | No segment geometry |
| `end_latitude` / `end_longitude` | ❌ No | No segment geometry |
| `highway_number` | ❌ No | No highway identifiers |
| `road_class` | ❌ No | Not in datasets |
| `segment_length_km` | ❌ No | No segment definition |
| `risk_score` (0–1) | ❌ No | Cannot compute without segment-level data |
| `accident_density` | ❌ No | Requires segment geometry + exposure |
| `fatality_weight` / `blackspot_weight` | ❌ No | Requires segment-level severity |
| `exposure_factor` | ❌ No | Requires AADT/traffic data |
| `confidence_score` | ❌ No | Cannot compute |

**Critical Gap:** `RoadSegmentRisk` is **derived** from `HighwayBlackSpot` + `AccidentRecord` via spatial clustering along road centerlines. Without raw accident data or road geometry, it cannot be computed.

---

## 4. Compatibility Classification

| Dataset | Classification | Reason |
|---------|----------------|--------|
| a583a07c (national time series) | **Not useful for SafeRoute AI** | National aggregate only; no spatial/temporal granularity for routing |
| abc5af52 (Bangalore stations) | **Not useful for SafeRoute AI** | Police jurisdiction aggregates; stations ≠ road segments; no GPS |
| c1fe08c4 (national severity) | **Not useful for SafeRoute AI** | National yearly severity totals; no location |
| cities-accidents-fatalities | **Not useful for SafeRoute AI** | City-level aggregates; city centroid ≠ road network |
| states-fatalities | **Not useful for SafeRoute AI** | State-level aggregates; no road data |
| states-road-accidents | **Not useful for SafeRoute AI** | State-level aggregates; no road data |
| type-of-collision | **Not useful for SafeRoute AI** | National collision-type breakdown; no spatial component |

**None are "Partially compatible" or "Fully compatible"** — all lack the **geospatial anchoring** (coordinates, chainage, road identifiers) required by the three ETL models.

---

## 5. Minimum Changes Required for Utility

To make these datasets useful, **one of the following must happen**:

### Option A: Acquire Individual FIR / Accident-Level Data (Recommended)
| Source | What It Provides | ETL Target |
|--------|------------------|------------|
| iRAD / e-DAR API or CSV exports | Individual accident records with GPS, collision type, severity, road class, vehicle types, timestamps | `AccidentRecord` (direct) → `HighwayBlackSpot` (cluster) → `RoadSegmentRisk` (compute) |
| State police open data portals | FIR-level data with location (often lat/lon or landmark) | Same as above |
| NHAI / MoRTH black spot MIS (blackspot.morth.gov.in) | 8,882 pre-identified black spots with chainage, state, district, agency | `HighwayBlackSpot` (direct) |

### Option B: Build Road Centerline Database First
| Step | Tool/Source | Output |
|------|-------------|--------|
| 1. Download OSM India extract highway network | Geofabrik `india-latest.osm.pbf` or Overpass API | `road_centerlines.db` (spatial index) |
| 2. Map chainage → lat/lon | NHAI chainage markers + linear referencing | Enables `HighwayBlackSpot` chainage resolution |
| 3. Import MoRTH black spot CSV (dataful) | `morth_blackspots_importer.py` | `HighwayBlackSpot` with GPS or PENDING |
| 4. Cluster AccidentRecord → HighwayBlackSpot | `cluster_blackspots.py` | New black spots from FIR data |
| 5. Compute segment risk | `compute_segment_risk.py` | `RoadSegmentRisk` |

### Option C: Use Aggregate Data for Calibration Only
These datasets **can** inform model calibration (e.g., national fatality rates, collision type distributions, state-level risk priors) but **cannot** populate the operational tables directly.

| Use Case | Datasets Applicable |
|----------|---------------------|
| Calibrate `SEGMENT_RISK_BASE_PENALTY` | `c1fe08c4` (national severity mix), `type-of-collision` (collision distribution) |
| Validate state-level risk priors | `states-fatalities`, `states-road-accidents` |
| City-level heuristic weights | `cities-accidents-fatalities` |

---

## 6. Recommendations

| Priority | Action | Effort |
|----------|--------|--------|
| **P0** | Obtain iRAD/e-DAR FIR exports (individual accidents with GPS) | High (external dependency) |
| **P0** | Download MoRTH Black Spot MIS CSV (8,882 records, ~15% GPS) | Medium (public portal) |
| **P0** | Build OSM road centerline DB for chainage→GPS resolution | Medium (one-time) |
| **P1** | Download Dataful MoRTH black spot CSV (expected in `data/raw/dataful/`) | Low (already scoped) |
| **P1** | Download OpenCity MoRTH per-dimension CSVs (5 files) | Low (already scoped) |
| **P2** | Use aggregate CSVs for model calibration / validation only | Low (analysis only) |
| **P3** | Archive current 7 CSVs under `data/raw/morth/` or `data/raw/opencity/` for provenance | Trivial |

---

## 7. File Placement for ETL Pipeline

Current location: `data/raw/*.csv` (root)

**Required relocation for `verify_datasets.py` detection:**

```
data/raw/
├── dataful/
│   ├── blackspots.csv              # ← MoRTH Black Spot MIS (P0)
│   ├── blackspots_2024.csv
│   └── blackspots_2025.csv
├── opencity/
│   ├── state_wise.csv              # ← OpenCity exports (P1)
│   ├── type_of_collision.csv
│   ├── type_of_violation.csv
│   ├── road_classification.csv
│   └── vehicle_type.csv
├── morth/
│   ├── RAI_2024.pdf                # ← Annual reports (P1)
│   └── ... (CSV extracts)
├── state/                          # ← State police data (P0)
├── irad/                           # ← iRAD/e-DAR exports (P0)
└── osm/                            # ← OSM PBF/GeoJSON (P0)
```

Move the 7 analyzed files to `data/raw/morth/` for provenance (they are MoRTH RAI 2024 report extracts).

---

## 8. Conclusion

**No dataset in `data/raw/` is currently compatible** with `AccidentRecord`, `HighwayBlackSpot`, or `RoadSegmentRisk` models. All are aggregate statistical tables lacking:
- Geospatial coordinates (lat/lon)
- Chainage / linear referencing
- Road / highway identifiers
- Individual accident records (FIR-level granularity)

**Next steps must focus on data acquisition** (iRAD, MoRTH MIS, OSM centerlines) rather than importer development for existing files. The current ETL framework (`morth_blackspots_importer.py`, `morth_accidents_importer.py`, `compute_segment_risk.py`) is ready — it awaits compatible source data.

---

*Report generated by automated analysis. No code or database modifications performed.*