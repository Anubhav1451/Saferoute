# Data Ingestion Specification — SafeRoute AI

## Overview

Three target database models must be populated from external government data sources:

```
┌─────────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Dataful Black Spot │     │  OpenCity MoRTH │     │  NHAI Black Spot │
│  CSV (8,862 rows)   │     │  Accidents CSV  │     │  MIS (3,996)     │
└─────────┬───────────┘     └────────┬────────┘     └────────┬─────────┘
          │                          │                       │
          ▼                          ▼                       ▼
  ┌───────────────┐         ┌───────────────┐        ┌───────────────┐
  │ HighwayBlack  │         │  Accident     │        │  HighwayBlack │
  │ Spot          │         │  Record       │        │  Spot         │
  └───────┬───────┘         └───────┬───────┘        └───────┬───────┘
          │                         │                        │
          └──────────────┬──────────┘                        │
                         │  clustering (500m window)         │
                         ▼                                   │
                ┌───────────────┐                             │
                │  HighwayBlack │◄────────────────────────────┘
                │  Spot (merged)│
                └───────┬───────┘
                        │
                        ▼
               ┌────────────────┐
               │  RoadSegment   │
               │  Risk          │
               │  (pre-computed)│
               └────────────────┘
```

---

## 1. HighwayBlackSpot Mapping

### 1.1 Source: Dataful Black Spot Dataset

**Source URL:** https://dataful.in/datasets/21559/
**Format:** CSV, 20 columns, 8,862 rows
**Time period:** 2014–2025
**Agencies:** NHAI, MoRTH (PWD NH), NHIDCL, BRO, State PWD, Other

#### Field Mapping

| # | CSV Column | Target Field | Requirement | Transformation |
|---|------------|-------------|-------------|---------------|
| 1 | `black_spot_id` | `black_spot_official_id` (planned) | Optional | Store raw ID string, e.g. `"AP-02-NH16-60"`. Used for dedup. |
| 2 | `state` | `state` (planned) | Optional | Direct copy. String (max 50). |
| 3 | `district` | `district` (planned) | Optional | Direct copy. String (max 100). |
| 4 | `agency` | `managed_by` (planned) | Optional | Maps to canonical: `"NHAI"`, `"MoRTH"`, `"NHIDCL"`, `"BRO"`, `"State PWD"` |
| 5 | `managed_by` | — | — | Store in `description` or discard. Contains office name (286 distinct values). |
| 6 | `location` | `chainage_start_km`, `chainage_end_km` (planned), `description` | Required | Parse chainage via `parse_chainage()` to extract start/end. Store raw text in `description`. |
| 7 | `police_station` | `police_station` (planned) | Optional | Direct copy. |
| 8 | `latitude`, `longitude` | `latitude`, `longitude` | **Required** | If absent, derive from chainage via `chainage_to_latlon()`. Record is **skipped** if both chainage and lat/lon are unavailable. |
| 9 | — | `radius` | Required | Default to `250.0` (half of 500m MoRTH definition). |
| 10 | — | `severity` | Required | Inferred from accident/fatality counts if available, else `BlackSpotSeverity.MEDIUM`. |
| 11 | — | `accident_count` | Optional | May need to aggregate from `AccidentRecord` clustering. Default `0` if unknown. |
| 12 | — | `fatalities` | Optional | Same as accident_count. Default `0`. |
| 13 | — | `last_accident_date` | Optional | Derived from latest linked `AccidentRecord`. Null until clustering runs. |
| 14 | — | `road_name` | Optional | Concatenation of `highway_number` + location description. |
| 15 | — | `source` | Required | Set to `"MoRTH"` for this source. |
| 16 | `final_repair_status` | `investigation_status` (planned) | Optional | Map canonical values: `"Already Rectified"`, `"Under Sanction / Investigation"`, `"In Progress"`, `"Rectified"`, empty → `"UNKNOWN"` |
| 17 | `repair_details` | `repair_details` (planned) | Optional | Truncate to 500 chars. |

#### Chainage Parsing Rules

MoRTH locations use kilometer chainage in multiple formats:

| Format | Example | Parsed | Rule |
|--------|---------|--------|------|
| `X+YYY` | `175+300` | 175.300 km | `X + YYY/1000` — YYY is meters (3 digits) |
| `X/Y` | `282/5` | 282.500 km | `X + Y/10` — Y is hundreds of meters (1 digit) |
| `X/.Y` | `23/.4` | 23.400 km | Normalize `/.` → `/` before parsing |
| `X to Y` | `23 to 24` | 23.0–24.0 km | Plain km range |

Always store both `chainage_start_km`/`chainage_end_km` (float) and `latitude`/`longitude` (derived from road centerline at import time). The routing engine requires lat/lon.

#### Dedup Strategy

- **Primary dedup key:** `black_spot_official_id` (unique per MoRTH record)
- **Fallback dedup:** (lat, lon) rounded to 5 decimal places (~1.1m) ± 0.001 tolerance
- On conflict: update existing record with newer data (upsert)

### 1.2 Source: MoRTH PDF Reports

**Source:** https://morth.nic.in/road-accident-in-india
**Format:** PDF (tabulated data, parsed via PDF scraping or manual conversion)
**Coverage:** National and state-level black spot counts per year

**Mapping:** Same as Dataful CSV above, but limited fields (no lat/lon, chainage, or repair tracking). Only provides aggregate counts — useful for validation, not per-record ingestion.

### 1.3 Source: NHAI Black Spot MIS

**Source:** https://blackspot.morth.gov.in/
**Format:** Web portal (exportable to CSV)
**Agency coverage:** NHAI (3,996 black spots), MoRTH PWD NH (4,139), NHIDCL (84), BRO (18)

**Mapping:** Same as Dataful CSV (the dataful dataset aggregates all agencies). NHAI-specific records:
- `black_spot_id` format: `"AP-02-NH16-60"` where NH16 is the highway number
- `agency` value: `"NHAI"`
- May include `repair_expenses` fields not in Dataful schema

**Extraction heuristic:**
```python
highway_number = extract_highway_from_id(black_spot_id)
# "AP-02-NH16-60" → "NH-16"
```

---

## 2. AccidentRecord Mapping

### 2.1 Source: OpenCity MoRTH Accident CSVs

**Source URL:** https://data.opencity.in/dataset/road-accidents-in-india-2022
**Format:** Multiple CSVs, time-series (2018–2024)

The MoRTH annual data is **aggregated** by various dimensions. Individual FIR-level records are not yet available in the public dataset. Each CSV covers one dimension:

#### CSV 1: Road Accidents Numbers (2018–2022)

| CSV Column | Target Field | Notes |
|------------|-------------|-------|
| `Year` | `accident_date` | Set to Jan 1 of year (aggregated) |
| `Accidents` | — | Total count — not per-record |
| `Fatalities` | — | Total count |
| `Persons injured` | — | Total count |

**Usage:** Validation only. Aggregated counts are used to verify individual record coverage.

#### CSV 2: Type of Collision

| CSV Column | Target Field | Notes |
|------------|-------------|-------|
| `Type of collision` | `collision_type` (planned) | Values: `Hit and Run`, `With parked Vehicle`, `Hit from Back`, `Hit from side`, `Run off Road`, `Fixed object`, `Vehicle overturn`, `Head on collision`, `Others` |
| `* Accidents` | — | Count per collision type per year |

**Usage:** When individual records exist, the collision type distribution guides expected ratios.

#### CSV 3: State-wise Accidents

| CSV Column | Target Field | Notes |
|------------|-------------|-------|
| `States` | `state` (planned) | State/UT name |
| `Accidents 2018..2022` | — | Annual total |

**Usage:** State field for record attribution.

#### CSV 4: Major Cities by Type of Violation

| CSV Column | Target Field | Notes |
|------------|-------------|-------|
| `Cities` | `district` (planned) | City name |
| `Overspeeding accidents` | `cause` (planned) | If cause = overspeeding |
| `Drunken Driving accidents` | `cause` (planned) | If cause = drunken driving |
| `Wrong side Accidents` | `cause` (planned) | If cause = wrong side |
| `Jumping red light accidents` | `cause` (planned) | If cause = red light jumping |
| `Use of Mobile Phone accidents` | `cause` (planned) | If cause = mobile phone use |

### 2.2 Source: e-DAR / iRAD System (Future)

**Source:** https://irad.parivahan.gov.in/
**Format:** JSON API or CSV export (expected availability: 2025–2026 for 2023–2024 data)
**Coverage:** Individual FIR-level accident records with GPS coordinates

#### Expected Field Mapping (when available)

| e-DAR Field | AccidentRecord Field | Required | Notes |
|-------------|---------------------|----------|-------|
| FIR Number | `fir_number` (planned) | Yes | Unique identifier |
| Date of accident | `accident_date` | Yes | Timestamp |
| Time of accident | `time_of_day` | Optional | HH:MM format |
| Latitude | `latitude` | Yes | From GPS |
| Longitude | `longitude` | Yes | From GPS |
| Road classification | `road_classification` (planned) | Yes | NH/SH/MDR/ODR/VR |
| Highway number | `highway_number` (planned) | Optional | e.g. "NH-44" |
| Road name | `road_name` | Optional | Street name |
| Chainage | `chainage_start_km`, `chainage_end_km` (planned) | Optional | Kilometer marker range |
| Collision type | `collision_type` (planned) | Yes | Head-on, Rear-end, etc. |
| Collision nature | `collision_nature` (planned) | Optional | Point of impact |
| Weather condition | `weather_condition` | Optional | Clear, Rain, Fog |
| Light condition | `light_condition` (planned) | Yes | Daylight, Dawn, Dusk, Night-lit, Night-unlit |
| Visibility | — | Optional | Approximate distance (stored in `description`) |
| Initial observation (cause) | `cause` (planned) | Yes | Speeding, Drink driving, etc. |
| Traffic violation | `traffic_violation` (planned) | Optional | Specific violation type |
| Accident spot (road feature) | `road_features` (planned) | Yes | Straight, Curve, Junction, Bridge, Gradient |
| Vehicle types involved | `vehicle_types_involved` (planned) | Optional | JSON list |
| Fatalities | `fatalities` | Yes | Integer |
| Grievous injuries | `injuries` | Yes | Integer |
| Simple injuries | — | Optional | Could extend `injuries` as JSON |
| State | `state` (planned) | Yes | State name |
| District | `district` (planned) | Yes | District name |
| Police station | `police_station` (planned) | Yes | Jurisdiction |
| Location accuracy | `location_accuracy` (planned) | Yes | `"GPS"`, `"Chainage"`, `"Manual"`, `"Approximate"` |
| Data source | `source` | Yes | Set to `"iRAD"` or `"e-DAR"` |

### 2.3 Source: MoRTH Annual Road Classification Tables (PDF)

**Format:** PDF tables — state/UT wise breakdown by road classification
**Example columns:**
```
State/UT | National Highways (Cases/Injured/Died) | State Highways (Cases/Injured/Died) | Expressways | Other Roads | Total
```

**Usage:** Assigns `road_classification` to accident records when available. Helps segment accidents by NH/SH for targeted routing penalties.

---

## 3. RoadSegmentRisk Generation

### 3.1 Overview

RoadSegmentRisk is a **pre-computed** table. It aggregates `AccidentRecord` and `HighwayBlackSpot` data into per-segment risk scores. The routing engine queries this table at request time — it does **not** compute accident risk on-the-fly.

### 3.2 Input Sources

```
AccidentRecord.road_name ─────────┐
                                  ├──► group by highway
HighwayBlackSpot.road_name ───────┘
                                          │
                                  segment into 200m intervals
                                          │
                                          ▼
                              per-segment risk score
                                  (0.0 – 1.0)
                                          │
                                          ▼
                                  RoadSegmentRisk
```

### 3.3 Segment Generation

**Algorithm:**
1. Collect distinct `road_name` values from `AccidentRecord` and `HighwayBlackSpot`
2. For each road, sort records by chainage (or infer order from lat/lon along road centerline)
3. Divide road into segments of `SEGMENT_LENGTH_M = 200` meters
4. Each segment midpoint = (start_lat, start_lon) for spatial lookup

**Segment boundary alignment:**
```
Highway: NH-44
Chainage: 0.0 ── 0.2 ── 0.4 ── 0.6 ── 0.8 ── 1.0 ... (km)
Segment:  [0]    [1]    [2]    [3]    [4]    [5]
Midpoint: 0.1    0.3    0.5    0.7    0.9    1.1
```

### 3.4 Risk Score Formula

#### 3.4.1 Severity-Weighted Accident Density

For each segment, find all `AccidentRecord` rows within `ACCIDENT_SEARCH_RADIUS_M = 200m`:

```
accident_density = Σ(severity_weight × recency_weight) / segment_length_km × years_of_data

severity_weight:
  AccidentSeverity.FATAL     = 3.0
  AccidentSeverity.GRIEVOUS  = 1.5
  AccidentSeverity.SIMPLE    = 1.0

recency_weight:
  weight = 2^(-years_ago / 2.0)
  where years_ago = (now - accident_date) in years
  half_life = 2 years
```

**Normalized accident density** (0.0 – 1.0):
```
norm_density = min(accident_density / ACCIDENT_DENSITY_MAX, 1.0)
```

where `ACCIDENT_DENSITY_MAX` is calibrated from historical data (suggested initial value: 50 accidents/km/year, tunable).

#### 3.4.2 Black Spot Contribution

For each segment, find all `HighwayBlackSpot` records within `BLACKSPOT_INFLUENCE_RADIUS_M = 500m`:

```
blackspot_penalty = Σ(proximity × severity_weight × recency_weight)

proximity = 1.0 - (distance_to_center / spot.radius)
  Range: 0.0 (at edge of radius) → 1.0 (at center)

severity_weight:
  BlackSpotSeverity.HIGH   = 1.0
  BlackSpotSeverity.MEDIUM = 0.6
  BlackSpotSeverity.LOW    = 0.3

recency_weight:
  if spot.last_accident_date is None: weight = 0.3
  else: weight = 2^(-years_since_last_accident / 3.0)
  half_life = 3 years
```

**Normalized black spot penalty** (0.0 – 1.0):
```
norm_blackspot = min(blackspot_penalty / BLACKSPOT_MAX_CONTRIBUTION, 1.0)
```

where `BLACKSPOT_MAX_CONTRIBUTION` (suggested: 3.0, representing 3 overlapping HIGH severity spots).

#### 3.4.3 Combined Risk Score

```
segment.risk_score = w1 × norm_density + w2 × norm_blackspot

Default weights:
  w1 = 0.6  (accident density contributes 60%)
  w2 = 0.4  (black spot penalty contributes 40%)
```

The weights are configurable and should be tuned against known accident data.

#### 3.4.4 Additional Computed Fields

```
segment.accident_frequency = raw accident_count / (segment_length_km × years_of_data)
  Units: accidents per km per year

segment.severity_distribution = {
    "fatal": count_fatal,
    "grievous": count_grievous,
    "simple": count_simple
}  # Stored as JSON string

segment.record_count = total count of AccidentRecord rows used
  Smaller count → lower confidence
```

### 3.5 Confidence Score

```
confidence = min(record_count / MIN_RECORDS_FOR_CONFIDENCE, 1.0)
  Default MIN_RECORDS_FOR_CONFIDENCE = 5

segment.risk_score_adjusted = segment.risk_score × confidence + 0.5 × (1 - confidence)
  Low confidence → score regresses toward 0.5 (neutral)
```

### 3.6 Batch Computation Schedule

| Frequency | Trigger | Scope |
|-----------|---------|-------|
| On first import | Manual (`python compute_segment_risk.py`) | All highways with data |
| Weekly | Cron/Docker scheduled task | Highways with new accident data |
| On-demand | After `cluster_blackspots.py` run | Recompute affected highways only |

### 3.7 Performance Considerations

- **Segment count:** A 500km NH with 200m segments = 2,500 rows per highway
- **Index usage:** Queries filter by `start_latitude`/`start_longitude` spatial range — requires composite index
- **Update strategy:** `MERGE` / `INSERT ... ON CONFLICT UPDATE` for idempotent recomputation

---

## 4. Ingestion Order & Dependencies

```
Step 1: MoRTHBlackspotsImporter       ──► HighwayBlackSpot
         (Dataful CSV, ~8,862 rows)        (with chainage, lat/lon from chainage)

Step 2: EDARImporter                   ──► AccidentRecord
         (iRAD/e-DAR CSV,                 (individual FIR records, GPS coords)
          when available)

Step 3: MoRTHAccidentsImporter         ──► AccidentRecord (bulk)
         (OpenCity aggregated CSVs,       (creates synthetic records from aggregates
          validation only)                  if individual data unavailable)

Step 4: ClusterBlackspots              ──► HighwayBlackSpot (update)
         (AccidentRecord aggregation)      (create/update black spots from clusters)

Step 5: ComputeSegmentRisk             ──► RoadSegmentRisk
         (HighwayBlackSpot +               (per-segment pre-computed scores)
          AccidentRecord)

Step 6: Recalibrate SAFETY_SCORE_MAX_PENALTY
         (after live data analysis, currently 2500)
```

---

## 5. Data Quality Rules

### 5.1 Required vs Optional Fields

| Model | Required Fields | Optional Fields |
|-------|----------------|-----------------|
| `HighwayBlackSpot` | `latitude`, `longitude`, `radius`, `severity` | Everything else |
| `AccidentRecord` | `latitude`, `longitude`, `accident_date`, `severity` | Everything else |
| `RoadSegmentRisk` | `start_latitude`, `start_longitude`, `end_latitude`, `end_longitude`, `segment_length_m`, `risk_score` | Everything else |

### 5.2 Record Rejection Rules

Records are skipped (logged as `skipped`) when:
1. `HighwayBlackSpot`: Neither lat/lon nor parseable chainage available
2. `AccidentRecord`: Neither lat/lon nor chainage available
3. `AccidentRecord`: `accident_date` is null or in the future
4. `RoadSegmentRisk`: `segment_length_m` is ≤ 0 or > 10000 (10km — unreasonable segment)

### 5.3 Dedup Rules

| Source | Dedup Key | On Conflict |
|--------|-----------|-------------|
| Dataful CSV | `black_spot_official_id` | Update if existing record is older |
| NHAI MIS | `black_spot_official_id` | Update |
| e-DAR | `fir_number` | Skip (immutable record) |
| Clustered | (lat, lon proximity ± 0.001) | Merge counts |

---

## 6. Future Enhancements

1. **Road centerline database:** Required for `chainage_to_latlon()` conversion. Could use OSM way geometries for Indian NH/SH network.
2. **AADT data integration:** Exposure metric (accidents per vehicle-km) for more accurate risk scoring.
3. **Seasonal factors:** JSON breakdown for monsoon/winter accident patterns.
4. **Real-time e-DAR API:** Poll MoRTH's e-DAR system for daily accident record updates.
5. **ML-based risk prediction:** Use historical `AccidentRecord` → `RoadSegmentRisk` as training data for the existing scikit-learn model.
