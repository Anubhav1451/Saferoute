# Source-to-Model Ingestion Matrix

## Dataset Rankings (by routing usefulness × data reliability ÷ integration difficulty)

| Rank | Dataset | Score | Rationale |
|------|---------|-------|-----------|
| 1 | Dataful Black Spot CSV | ★★★★★ | Already available (8,862 records), direct schema match, chainage→lat/lon pipeline defined |
| 2 | NHAI Black Spot MIS | ★★★★☆ | Subset of Dataful (3,996 records), but NHAI-specific fields valuable for highway mapping |
| 3 | iRAD/e-DAR Individual FIRs | ★★★☆☆ | Highest routing usefulness (per-coordinate FIR records), not yet publicly available |
| 4 | OpenCity MoRTH CSVs | ★★☆☆☆ | Aggregated data only — no individual records, validation/derivation only |
| 5 | MoRTH PDF Reports | ★☆☆☆☆ | Aggregate counts per state/year, no spatial data, validation only |

---

## 1. Dataful Black Spot Dataset

| Property | Value |
|----------|-------|
| **Dataset name** | Dataful MoRTH Black Spot Dataset |
| **Source authority** | MoRTH (Ministry of Road Transport & Highways) via dataful.in |
| **Source URL** | https://dataful.in/datasets/21559/ |
| **Format** | CSV, ~20 columns, 8,862 rows |
| **Time coverage** | 2014–2025 |
| **Update frequency** | Ad-hoc (dataful.in mirrors MoRTH MIS snapshots; MoRTH itself updates quarterly) |
| **License** | Open Government Data License — India |

### Expected Columns

| # | Column | Type | Example | Coverage |
|---|--------|------|---------|----------|
| 1 | `black_spot_id` | String | `AP-(02)-NH16-60` | 100% |
| 2 | `state` | String | `Andhra Pradesh` | 100% |
| 3 | `district` | String | `Krishna` | 100% |
| 4 | `agency` | String | `NHAI` | 100% |
| 5 | `managed_by` | String | `RO, Vijayawada` | ~90% |
| 6 | `location` | String | `175+300 to 175+800` | 100% |
| 7 | `police_station` | String | `Gollapudi PS` | ~85% |
| 8 | `road_name` | String | `NH-16` | ~60% (embedded in ID) |
| 9 | `repair_start_date` | Date | `2022-03-15` | ~40% |
| 10 | `repair_end_date` | Date | `2022-06-20` | ~30% |
| 11 | `repair_details` | String | `Providing crash barrier...` | ~35% |
| 12 | `temporary_repair_status` | String | `Completed` | ~70% |
| 13 | `final_repair_status` | String | `Already Rectified` | ~100% |

### Target Models

| Model | Match Level | Fields Populated |
|-------|-------------|------------------|
| **HighwayBlackSpot** | ✅ Direct (primary) | `official_id`, `state`, `district`, `managed_by`, `chainage_start_km`, `chainage_end_km`, `latitude`, `longitude` (via chainage→lat/lon), `radius` (default 250m), `severity` (inferred), `location_text`, `source_name`, `source_url`, `geometry_resolution` ("Chainage") |
| **AccidentRecord** | ❌ Not populated | No individual accident data in this source |
| **RoadSegmentRisk** | ❌ Indirect | Via clustering → `blackspot_weight` field (post-clustering step) |

### Transformation Required

| Transformation | Detail | Complexity |
|---------------|--------|------------|
| **Chainage parsing** | `X+YYY` → `chainage_start_km` (float), `X+YYY to X+YYY` → start + end. Handles `X/Y`, `X/.Y`, `X to Y` formats | Medium |
| **Chainage→lat/lon conversion** | Requires road centerline database (OSM NH/SH geometry). Without it, latitude/longitude remains NULL and record must be skipped | High |
| **Agency normalization** | Map `agency` (286 distinct office names) → canonical `managed_by` (5 values: NHAI, MoRTH, NHIDCL, BRO, State PWD) | Low |
| **Severity inference** | Derive `BlackSpotSeverity` from MoRTH black spot definition: ≥5 fatal/grievous accidents → HIGH, otherwise MEDIUM. Without `AccidentRecord` counts yet, default all to MEDIUM | Medium |
| **Dedup** | `black_spot_id` is the primary key. On conflict, update `final_repair_status`, `repair_end_date` | Low |

### Confidence Score Recommendation

**Per-record:** `0.3` for chainage-only records (lat/lon approximate), `0.7` for records with lat/lon verified against road centerline. Overall dataset confidence: `0.6`.

---

## 2. NHAI Black Spot MIS

| Property | Value |
|----------|-------|
| **Dataset name** | NHAI Black Spot MIS Export |
| **Source authority** | NHAI (National Highways Authority of India) via blackspot.morth.gov.in |
| **Source URL** | https://blackspot.morth.gov.in/ |
| **Format** | Web portal with CSV export, ~3,996 rows (NHAI portion) |
| **Time coverage** | 2014–2025 |
| **Update frequency** | Quarterly (coincides with MoRTH review cycles) |
| **License** | Public government data |

### Expected Columns

| # | Column | Type | Example | Coverage |
|---|--------|------|---------|----------|
| 1 | `black_spot_id` | String | `UP-05-NH44-120` | 100% |
| 2 | `state` | String | `Uttar Pradesh` | 100% |
| 3 | `district` | String | `Meerut` | 100% |
| 4 | `agency` | String | `NHAI` | 100% |
| 5 | `location` | String | `120+000` | 100% |
| 6 | `final_repair_status` | String | `In Progress` | 100% |
| 7 | `repair_expenses` | Number | `2500000` | ~60% |
| 8 | `latitude` | Float | `28.9845` | ~15% (some rows have GPS) |
| 9 | `longitude` | Float | `77.7067` | ~15% |

### Target Models

| Model | Match Level | Fields Populated |
|-------|-------------|------------------|
| **HighwayBlackSpot** | ✅ Direct (subset) | Same mapping as Dataful CSV, but `agency` always `"NHAI"`. May have lat/lon for ~15% of records. `managed_by` = `"NHAI"` |
| **AccidentRecord** | ❌ Not populated | No individual accident data |
| **RoadSegmentRisk** | ❌ Indirect | Same as Dataful — via clustering |

### Transformation Required

| Transformation | Detail | Complexity |
|---------------|--------|------------|
| **Chainage parsing** | Identical to Dataful format | Medium |
| **Highway extraction** | `UP-05-NH44-120` → `highway_number` = `"NH-44"` via regex | Low |
| **Repair expense parsing** | Parse currency string → numeric (some entries are empty or approximate) | Low |
| **Overlap dedup** | May overlap with Dataful records (same `black_spot_id`). Dedup by `official_id` taking the record with more populated fields | Medium |

### Confidence Score Recommendation

**Per-record:** `0.4` for chainage-only, `0.8` for GPS-verified. Overall dataset confidence: `0.5` (smaller sample size, lower GPS coverage).

---

## 3. iRAD / e-DAR Individual FIR Records

| Property | Value |
|----------|-------|
| **Dataset name** | iRAD/e-DAR Accident FIR Database |
| **Source authority** | MoRTH + State Police via irad.parivahan.gov.in |
| **Source URL** | https://irad.parivahan.gov.in/ |
| **Format** | JSON API, CSV export (not yet publicly available for download) |
| **Time coverage** | 2023–2024 (expected release 2025–2026) |
| **Update frequency** | Real-time (police file FIR → system updates within 24h) |
| **License** | Restricted government data (RTI-accessible, not yet open data) |

### Expected Columns (per iRAD schema)

| # | Field | Type | Example | Coverage |
|---|-------|------|---------|----------|
| 1 | `fir_number` | String | `2023/AP/000123` | 100% |
| 2 | `accident_datetime` | Timestamp | `2023-12-15 14:30:00` | 100% |
| 3 | `latitude` | Float | `28.6129` | ~90% (GPS from mobile app) |
| 4 | `longitude` | Float | `77.2295` | ~90% |
| 5 | `state` | String | `Delhi` | 100% |
| 6 | `district` | String | `Central` | 100% |
| 7 | `city` | String | `New Delhi` | ~80% |
| 8 | `police_station` | String | `Paharganj` | 100% |
| 9 | `road_class` | String | `NH` | 100% |
| 10 | `highway_number` | String | `NH-44` | ~60% (when on NH) |
| 11 | `road_name` | String | `GT Karnal Road` | ~70% |
| 12 | `collision_type` | String | `Head on collision` | 100% |
| 13 | `collision_nature` | String | `Front` | ~80% |
| 14 | `weather_condition` | String | `Clear` | ~90% |
| 15 | `light_condition` | String | `Daylight` | 100% |
| 16 | `cause` | String | `Overspeeding` | ~90% |
| 17 | `traffic_violation` | String | `Jumping red light` | ~40% |
| 18 | `road_feature` | String | `Straight` | ~85% |
| 19 | `vehicle_types` | JSON | `["Truck", "Car"]` | ~95% |
| 20 | `fatalities` | Integer | `2` | 100% |
| 21 | `grievous_injuries` | Integer | `1` | 100% |
| 22 | `simple_injuries` | Integer | `3` | 100% |

### Target Models

| Model | Match Level | Fields Populated |
|-------|-------------|------------------|
| **HighwayBlackSpot** | ❌ Not populated directly | Used in clustering step to create/update HighwayBlackSpot (step 4) |
| **AccidentRecord** | ✅ Direct (primary) | `latitude`, `longitude`, `accident_date`, `severity`, `fatalities`, `injuries`, `vehicles_involved`, `road_name`, `weather_condition`, `time_of_day`, `collision_type`, `violation_type`, `road_user_type`, `vehicle_type`, `road_class`, `state`, `district`, `city`, `year`, `source_name`, `aggregation_level` |
| **RoadSegmentRisk** | ❌ Indirect | Via aggregation of AccidentRecord → `accident_density`, `fatality_weight` fields |

### Transformation Required

| Transformation | Detail | Complexity |
|---------------|--------|------------|
| **Severity derivation** | `fatalities > 0` → FATAL, `grievous_injuries > 0` → GRIEVOUS, else → SIMPLE | Low |
| **Vehicle type normalization** | JSON list→ single `vehicle_type` (pick most relevant or concatenate). Model stores single string, not JSON | Low |
| **Road user type extraction** | Derive from collision_type + vehicle_type: pedestrian hit → Pedestrian, bicycle involved → Cyclist | Medium |
| **Year extraction** | `accident_datetime.year` → `year` column for indexing | Low |
| **Black spot linking** | Spatial join: nearest HighwayBlackSpot within 200m → set `black_spot_id` FK | Medium |
| **Dedup** | `fir_number` is unique. Skip on conflict | Low |
| **Geocoding fallback** | If lat/lon missing but police_station + road_name available, geocode via Nominatim/other | High |

### Confidence Score Recommendation

**Per-record:** `0.95` for GPS-verified FIRs, `0.6` for geocoded records. Overall dataset confidence: `0.9` (gold standard source).

---

## 4. OpenCity MoRTH Accident CSVs

| Property | Value |
|----------|-------|
| **Dataset name** | OpenCity MoRTH Road Accidents in India |
| **Source authority** | MoRTH via data.opencity.in |
| **Source URL** | https://data.opencity.in/dataset/road-accidents-in-india-2022 |
| **Format** | Multiple CSVs, time-series (2018–2022 or 2019–2023) |
| **Update frequency** | Annual (MoRTH publishes yearly "Road Accidents in India" report) |
| **License** | Open Government Data License — India |

### Sub-Datasets & Columns

#### 4a. Road Accidents Numbers (2018–2022)

| Column | Type | Example |
|--------|------|---------|
| `Year` | Integer | `2022` |
| `Accidents` | Integer | `461312` |
| `Fatalities` | Integer | `168491` |
| `Persons injured` | Integer | `443366` |

#### 4b. Type of Collision Breakdown

| Column | Type | Example |
|--------|------|---------|
| `Type of collision` | String | `Head on collision` |
| `2021 Accidents` | String | `76,304` |
| `2021 Killed` | String | `27,248` |
| `2021 Injured` | String | `78,502` |
| `2022 Accidents` | String | `77,886` |
| `2022 Killed` | String | `26,413` |
| `% Change in Accidents` | String | `2.1` |

Values: `Hit and Run`, `With parked Vehicle`, `Hit from Back`, `Hit from side`, `Run off Road`, `Fixed object`, `Vehicle overturn`, `Head on collision`, `Others`.

#### 4c. State-wise Accidents

| Column | Type | Example |
|--------|------|---------|
| `States` | String | `Tamil Nadu` |
| `2018 Accidents` | Integer | `64873` |
| `2019 Accidents` | Integer | `57359` |
| `2020 Accidents` | Integer | `46423` |
| `2021 Accidents` | Integer | `54210` |
| `2022 Accidents` | Integer | `64521` |

#### 4d. Major Cities by Type of Violation

| Column | Type | Example |
|--------|------|---------|
| `Cities` | String | `Delhi` |
| `Overspeeding accidents` | Integer | `1423` |
| `Drunken Driving accidents` | Integer | `567` |
| `Wrong side Accidents` | Integer | `234` |
| `Jumping red light accidents` | Integer | `89` |
| `Use of Mobile Phone accidents` | Integer | `45` |

#### 4e. Road Classification Table (PDF)

| Column | Type | Example |
|--------|------|---------|
| `State/UT` | String | `Maharashtra` |
| `National Highways (Cases)` | Integer | `15678` |
| `National Highways (Injured)` | Integer | `18234` |
| `National Highways (Died)` | Integer | `5432` |
| `State Highways (Cases)` | Integer | `8932` |
| `Expressways (Cases)` | Integer | `1234` |
| `Other Roads (Cases)` | Integer | `23456` |

### Target Models

| Model | Match Level | Fields Populated |
|-------|-------------|------------------|
| **HighwayBlackSpot** | ❌ Not populated | No individual spot data |
| **AccidentRecord** | 🟡 Derived (synthetic rows) | If individual records are unavailable, aggregate CSVs can be expanded into synthetic rows per (state, year, collision_type) with proportional distribution. Fields: `state`, `year`, `collision_type`, `severity` (inferred from killed/injured ratio), `aggregation_level` |
| **RoadSegmentRisk** | ❌ Indirect | Validation only — aggregate totals can verify coverage of computed scores |

### Transformation Required

| Transformation | Detail | Complexity |
|---------------|--------|------------|
| **Proportional distribution** | Expand aggregate counts into synthetic AccidentRecord rows. E.g., if state X has 1,000 accidents in 2022, generate 1,000 rows with random spatial distribution within state bounds | High (low spatial accuracy) |
| **Collision type → severity mapping** | Higher killed-per-accident ratio for "Head on collision" vs "Hit from Back". Use statistical priors to assign severity | Medium |
| **Numeric normalization** | CSV contains comma-formatted strings (`"76,304"`) → `76304` int | Low |
| **PDF parsing** | Road Classification table is in PDF format; requires tabula-py or camelot for extraction | Medium |
| **Validation** | Compare aggregated counts from CSV against SUM of individual AccidentRecord records per (state, year) — flag discrepancies > 5% | Low |

### Confidence Score Recommendation

**Per-record:** N/A (synthetic rows). **Validation purpose:** `0.8` for total counts (authoritative MoRTH data), `0.3` for spatial distribution (synthetic). Overall confidence: `0.4`.

---

## 5. MoRTH PDF Annual Reports

| Property | Value |
|----------|-------|
| **Dataset name** | Road Accidents in India — Annual Report |
| **Source authority** | MoRTH Transport Research Wing (TRW) |
| **Source URL** | https://morth.nic.in/road-accident-in-india |
| **Format** | PDF (150–200 pages per year) |
| **Time coverage** | 2014–2023 (annual reports available) |
| **Update frequency** | Annual (report published ~18 months after calendar year) |
| **License** | Public government document |

### Tables Available

| Table | Content | Granularity |
|-------|---------|-------------|
| State/UT wise accidents | Total cases, killed, injured per year | State |
| Road classification | NH, SH, Expressway, Other Roads breakdown | State × road class |
| Collision type distribution | Head-on, Rear-end, etc. distribution | National |
| Time of day | Day, Night, Dawn, Dusk | National |
| Cause of accidents | Overspeeding, Drunken driving, etc. | National |
| Vehicle type involvement | Truck, Car, Two-wheeler, Bus, etc. | National |
| Monthly distribution | Accidents per month | National |
| Age group of drivers | 18–25, 25–35, etc. | National |
| Severity analysis | Fatal, Grievous, Simple injury accidents | State |
| National highway wise | Accidents on select NH corridors | NH-specific |
| Black spot status (2022+) | Number of black spots identified/rectified per state | State |

### Target Models

| Model | Match Level | Fields Populated |
|-------|-------------|------------------|
| **HighwayBlackSpot** | 🟡 Validation only | Black spot count per state can verify completeness of HighwayBlackSpot table |
| **AccidentRecord** | 🟡 Validation only | Aggregate totals can verify coverage |
| **RoadSegmentRisk** | 🟡 Validation only | Segment-level risk distributions can be compared against NH-specific accident counts |

### Transformation Required

| Transformation | Detail | Complexity |
|---------------|--------|------------|
| **PDF table extraction** | Use tabula-py or camelot to locate and parse tabular data from PDF | Medium |
| **Table identification** | Must identify correct table by context (page headers, column patterns). No machine-readable labels | High |
| **Numeric cleaning** | Indian number formatting (`1,53,972`) → `153972` integer | Medium |
| **Normalization** | Different PDF editions may have different column ordering. Requires per-edition mapping | High |
| **State name normalization** | "A & N Islands" → "Andaman and Nicobar Islands", "Delhi (UT)" → "Delhi". Standardize to Census names | Low |

### Confidence Score Recommendation

**Per-record:** N/A (validation purpose). **Validation confidence:** `0.9` for totals (official MoRTH publication), `0.5` for NH-specific data (reporting delays). Overall: `0.7` for validation.

---

## 6. Auxiliary: Road Centerline Database (for chainage→lat/lon)

| Property | Value |
|----------|-------|
| **Dataset name** | Indian National Highways / State Highways OSM Geometry |
| **Source authority** | OpenStreetMap contributors (via Overpass API or Geofabrik extract) |
| **Source URL** | https://download.geofabrik.de/asia/india.html |
| **Format** | OSM PBF or GeoJSON |
| **Time coverage** | Continuous |
| **Update frequency** | Daily (Geofabrik), Real-time (Overpass API) |
| **License** | ODbL |

### Usage

This is a **supporting dataset**, not a primary ingestion target. It is required to convert MoRTH chainage references into lat/lon coordinates:

```
highway = "NH-44"
chainage_start = 120.0 → nearest way node on NH-44 at 120km from origin → lat/lon
```

### Target Models

| Model | Fields Populated |
|-------|------------------|
| **HighwayBlackSpot** | `latitude`, `longitude` for chainage-only records |
| **AccidentRecord** | `latitude`, `longitude` for chainage-only FIRs |

### Confidence Impact

With road centerline DB → chainage records get `0.7` confidence instead of `0.3`, and record rejection drops to near 0%.

---

## 7. Full Coverage Matrix

```
Source                     │ HighwayBlackSpot │ AccidentRecord │ RoadSegmentRisk │ Step
───────────────────────────┼──────────────────┼────────────────┼─────────────────┼──────
Dataful CSV (8,862 rows)   │ ✅ Populate      │ —              │ —               │ 1
NHAI MIS (3,996 rows)      │ ✅ Populate      │ —              │ —               │ 1
iRAD/e-DAR FIRs            │ —                │ ✅ Populate    │ —               │ 2
OpenCity CSVs              │ —                │ 🟡 Validate    │ —               │ 3
MoRTH PDF Reports          │ 🟡 Validate      │ 🟡 Validate    │ 🟡 Validate     │ 3
ClusterBlackspots          │ ✅ Update        │ —              │ —               │ 4
ComputeSegmentRisk         │ —                │ —              │ ✅ Populate     │ 5
Road Centerline DB         │ 🟡 Enrich        │ 🟡 Enrich      │ —               │ (support)
```

---

## 8. Per-Model Source Dependency Summary

### HighwayBlackSpot

| Source | Dependency | Order |
|--------|-----------|-------|
| Dataful CSV | Required (primary population) | 1a |
| NHAI MIS | Optional (NHAI-specific enrichment) | 1b |
| ClusterBlackspots | Required (update severity/counts from AccidentRecord) | 4 |
| Road Centerline DB | Required (chainage→lat/lon, or records skipped) | Parallel to 1 |

### AccidentRecord

| Source | Dependency | Order |
|--------|-----------|-------|
| iRAD/e-DAR FIRs | Required (primary population) | 2 |
| OpenCity CSVs | Optional (validation + synthetic expansion) | 3 |
| MoRTH PDF Reports | Optional (validation only) | 3 |

### RoadSegmentRisk

| Source | Dependency | Order |
|--------|-----------|-------|
| HighwayBlackSpot | Required (blackspot_weight input) | 5 (after step 4) |
| AccidentRecord | Required (accident_density input) | 5 (after step 2) |
| ComputeSegmentRisk script | Required (batch computation) | 5 |

---

## 9. Recommended Implementation Sequence

```
Phase 1: Foundation
  └─ Road Centerline DB (OSM) — prerequisite for all chainage data
  └─ Dataful CSV Importer → HighwayBlackSpot
  └─ NHAI MIS Importer → HighwayBlackSpot (optional supplement)

Phase 2: Individual Records
  └─ iRAD/e-DAR Importer → AccidentRecord (when data available)

Phase 3: Aggregation & Validation
  └─ OpenCity CSV Importer → AccidentRecord (synthetic expansion, optional)
  └─ MoRTH PDF Validator → validation reports only

Phase 4: Clustering & Risk
  └─ ClusterBlackspots → HighwayBlackSpot (update severity/counts)
  └─ ComputeSegmentRisk → RoadSegmentRisk

Phase 5: Routing Integration (FUTURE)
  └─ Extend calculate_penalty() with HighwayBlackSpot proximity
  └─ Extend fast_midpoint_penalty() with RoadSegmentRisk lookup
  └─ Recalibrate SAFETY_SCORE_MAX_PENALTY
```

---

## 10. Ranking Summary

| # | Dataset | Difficulty (1–5) | Usefulness (1–5) | Reliability (1–5) | Composite |
|---|---------|-----------------|------------------|-------------------|-----------|
| 1 | Dataful CSV | 3 (chainage parser + road centerline needed) | 5 (8,862 direct black spot records) | 4 (govt source, well-documented) | **4.0** |
| 2 | iRAD/e-DAR FIRs | 2 (clean schema, GPS coords) | 5 (per-coordinate accident data) | 5 (FIR-level, mobile GPS) | **3.7** (not yet available) |
| 3 | NHAI MIS | 3 (same as Dataful, smaller set) | 4 (NHAI-specific fields) | 3 (smaller, partial GPS) | **3.3** |
| 4 | OpenCity CSVs | 4 (aggregated → synthetic) | 2 (validation only without spatial) | 4 (official MoRTH aggregates) | **2.7** |
| 5 | MoRTH PDF Reports | 5 (PDF scraping, per-edition mapping) | 1 (validation only) | 5 (gold standard totals) | **2.3** |

**Composite = (usefulness × reliability) / difficulty** (higher is better).
