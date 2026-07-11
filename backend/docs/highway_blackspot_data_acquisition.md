# Highway Black Spot Data Acquisition

## Source

The `MoRTHBlackSpotImporter` ingests the **Dataful MoRTH Black Spot Dataset**
(dataset ID 21559 on dataful.in).

| Property | Value |
|----------|-------|
| URL | https://dataful.in/datasets/21559/ |
| Records | ~8,862 rows |
| Access | Paid (requires purchase, was initially reported as free) |
| Format | Single CSV file, UTF-8 encoded |
| Columns | 13 (no geospatial columns) |

## Expected Filename and Location

Place the downloaded CSV file at:

```
data/raw/dataful/blackspots.csv
```

The importer does not enforce a specific filename — any `.csv` file in
`data/raw/dataful/` can be passed via `filepath` argument. The path above
is convention for the `verify_datasets.py` expected-file check and for
consistency across environments.

Do not place files in `backend/data/raw/`. The `data/` directory at the
project root is the designated raw-data storage.

## Import Command

```bash
cd backend
python -c "
from scripts.data_ingestion.morth_blackspots_importer import MoRTHBlackSpotImporter
imp = MoRTHBlackSpotImporter()
result = imp.run(filepath='../data/raw/dataful/blackspots.csv')
print(result)
"
```

Run `python init_db.py` first if the production database
(`backend/saferoute.db`) has not been initialized.

### Dry Run (Schema Validation Without Import)

```bash
cd backend
python -c "
from scripts.data_ingestion.morth_blackspots_importer import MoRTHBlackSpotImporter
imp = MoRTHBlackSpotImporter()
columns = imp._get_csv_columns('../data/raw/dataful/blackspots.csv')
print(imp.validate_schema(columns))
"
```

## Expected CSV Schema (13 columns)

```
data_as_on,agency,managed_by,state,district,black_spot_id,location,
police_station,repair_start_date,repair_end_date,repair_details,
temporary_repair_status,final_repair_status
```

### Column Details

| # | Column | Read by Importer | Purpose |
|---|--------|-----------------|---------|
| 1 | `data_as_on` | No (recognized extra) | Snapshot date |
| 2 | `agency` | **Yes — required** | Managing agency name |
| 3 | `managed_by` | No (recognized extra) | Agency type (NHAI/MoRTH/NHIDCL/BRO/State PWD) |
| 4 | `state` | **Yes — required** | State/UT name |
| 5 | `district` | **Yes — optional** | District name |
| 6 | `black_spot_id` | **Yes — optional** | Official black spot identifier (e.g., `AP-(02)-NH16-60`) |
| 7 | `location` | **Yes — optional** | Chainage description (e.g., `175+300 to 175+800` or `Km 45.2`) |
| 8 | `police_station` | No (recognized extra) | Jurisdiction |
| 9 | `repair_start_date` | No (recognized extra) | Repair start date |
| 10 | `repair_end_date` | No (recognized extra) | Repair end date |
| 11 | `repair_details` | **Yes — optional** | Engineering remediation description |
| 12 | `temporary_repair_status` | No (recognized extra) | Temporary repair progress |
| 13 | `final_repair_status` | **Yes — optional** | Final repair status |

### Required Columns (schema validation enforces these)

- `state` — validated with `NotNullValidator`
- `agency` — validated with `ChoiceValidator` against known agency names

The importer raises `ValueError` with column-level details before any row
processing if either required column is missing from the CSV header.

### Optional Columns (read by importer, gracefully defaulted when missing)

| Column | Default When Missing | Notes |
|--------|---------------------|-------|
| `black_spot_id` | `None` | Used for highway number extraction and dedup |
| `latitude` | `None` | Geometry set to PENDING |
| `longitude` | `None` | Geometry set to PENDING |
| `location` | `None` | Chainage parsing skipped |
| `road_name` | `None` | Highway number extracted from `black_spot_id` instead |
| `final_repair_status` | `None` | Repair description excluded |
| `repair_details` | `None` | Description shortened |
| `district` | `None` | Left as NULL |

## Validation Flow

1. **Schema validation** — `validate_schema()` classmethod checks CSV header
   against `REQUIRED_CSV_COLUMNS`, `KNOWN_CSV_COLUMNS`, and
   `RECOGNIZED_EXTRA_COLUMNS`. Reports missing required, missing optional,
   and unrecognized columns.

2. **Row-level validation** — per-row rules applied via `ValidatorRegistry`:
   - `state` must be non-null
   - `agency` must match one of the canonical agency keys

3. **Normalization** — `normalize_row()` transforms raw CSV fields into
   the `HighwayBlackSpot` model schema:
   - Agency mapped via `CANONICAL_AGENCIES` dictionary
   - State normalized via `STATE_NORMALIZE` dictionary
   - Highway number extracted from `black_spot_id` via regex
   - Chainage parsed from `location` field (see formats below)
   - Confidence score computed from GPS/ID/repair availability

4. **Dedup** — `ByIdStrategy` using `official_id` field. Records with the
   same `official_id` are updated (via `FreshnessResolver` on `updated_at`)
   rather than inserted.

5. **Persist** — valid records are inserted/updated; records failing
   validation are quarantined to the ETL metadata DB.

## What Happens When GPS Is Missing

The Dataful CSV does not include `latitude` or `longitude` columns.
The importer handles this correctly:

1. `normalize_row()` calls `row.get("latitude")` → returns `None`
2. `row.get("longitude")` → returns `None`
3. `has_gps = False`
4. Output record gets:
   - `latitude = NULL`
   - `longitude = NULL`
   - `geometry_resolution = "PENDING"`
5. Confidence score drops from ~0.705–0.795 to ~0.205–0.475 (the GPS
   factor contributes 40% × 0.9 = 0.36 when present, or 40% × 0.1 = 0.04
   when absent)

All records are still imported. No records are skipped due to missing GPS.
The `location_text` field preserves the raw chainage string for future
GPS resolution via a road centerline database.

## What Happens When Chainage Is Missing

If the `location` column is empty or does not match any known chainage
format:

1. `location_raw` is empty string → `chainage_start = None`,
   `chainage_end = None`
2. The `location_text` is set to `None` (empty string is coerced to `None`)
3. The record is still imported with NULL chainage values
4. Confidence score is unaffected (chainage is not a confidence factor)

### Accepted Chainage Formats

The `parse_chainage()` method handles these formats in the `location` field:

| Format | Example | Parsed Result |
|--------|---------|---------------|
| `X+YYY to Z+WWW` | `175+300 to 175+800` | `(175.3, 175.8)` |
| `X/YYY to Z/WWW` | `45/200 to 46/100` | `(45.2, 46.1)` |
| `X.Y to Z.W` | `45.2 to 46.1` | `(45.2, 46.1)` |

Single-point locations or unrecognized formats produce `(None, None)`.
The raw string is preserved in `location_text` regardless.

## Accepted Agency Variations

The `CANONICAL_AGENCIES` mapping normalizes these 14 variants into 5
canonical agencies:

| Raw Value | Canonical |
|-----------|-----------|
| `nhai` | NHAI |
| `morth` | MoRTH |
| `morh` | MoRTH |
| `morth pwd` | MoRTH |
| `morth (pwd)` | MoRTH |
| `morth pwd nh` | MoRTH |
| `nhidcl` | NHIDCL |
| `bro` | BRO |
| `border roads` | BRO |
| `border roads organisation` | BRO |
| `state pwd` | State PWD |
| `pwd` | State PWD |
| `state pwd (nh)` | State PWD |
| `public works department` | State PWD |

Unrecognized agency values are mapped to `"Other"`.

## Output Schema

Each CSV row produces a `HighwayBlackSpot` record with these fields:

| Field | Source | Notes |
|-------|--------|-------|
| `latitude` | CSV `latitude` | `NULL` if missing |
| `longitude` | CSV `longitude` | `NULL` if missing |
| `radius` | Fixed: 250.0 | Half of 500m MoRTH black spot definition |
| `severity` | Fixed: MEDIUM | No severity info in Dataful CSV |
| `accident_count` | Fixed: 0 | Not available from Dataful CSV |
| `fatalities` | Fixed: 0 | Not available from Dataful CSV |
| `last_accident_date` | Fixed: `NULL` | Not available from Dataful CSV |
| `road_name` | CSV `road_name` or `NULL` | Often missing in Dataful CSV |
| `description` | Composite from `location` + `final_repair_status` + `repair_details` | Truncated to 500 chars |
| `source` | Fixed: `"MoRTH"` | |
| `state` | CSV `state` | Normalized |
| `district` | CSV `district` | |
| `highway_number` | Extracted from `black_spot_id` | e.g., `NH-16` |
| `managed_by` | Mapped from CSV `agency` | Canonical agency name |
| `official_id` | CSV `black_spot_id` | Used for dedup |
| `chainage_start_km` | Parsed from CSV `location` | |
| `chainage_end_km` | Parsed from CSV `location` | |
| `location_text` | CSV `location` raw string | |
| `geometry_resolution` | `"GPS"` if lat/lon present, else `"PENDING"` | |
| `source_name` | Fixed: `"Dataful MoRTH Black Spot Dataset"` | |
| `source_url` | Fixed: `"https://dataful.in/datasets/21559/"` | |
| `confidence_score` | Computed: 0.205–0.475 (no GPS) or 0.705–0.795 (with GPS) | |

## Expected Import Metrics (Estimated)

Based on the Dataful dataset description and importer logic:

| Metric | Expected Value |
|--------|----------------|
| Total CSV rows | ~8,862 |
| Inserted (first run) | ~8,862 |
| Inserted (subsequent runs) | ~0 (all dedup-updated) |
| Updated (subsequent runs) | ~8,862 |
| Rejected by validation | ~0 (data should validate) |
| Quarantined | ~0 |
| GPS resolution | ~0% (no lat/lon in Dataful CSV) |
| PENDING resolution | ~100% |
| Confidence range | 0.205–0.475 |
| Highway numbers extracted | ~95%+ (most black_spot_ids contain NH/SH) |
| Chainage parsed | ~90%+ (most location values are chainage) |
| Dedup keys | `official_id` |

## Troubleshooting

### Schema Validation Fails (MISSING REQUIRED columns)

Ensure the CSV header contains `state` and `agency` columns. These are the
only required columns. If the CSV source has different column names (e.g.,
`State` with capital S), rename the column or update
`REQUIRED_CSV_COLUMNS` in the importer.

### All Records Get PENDING Geometry

Expected if the source CSV does not include `latitude`/`longitude` columns.
The Dataful CSV does not include geospatial coordinates, so ~100% of
records will have `geometry_resolution = "PENDING"`. This is correct
behavior — the raw location text and chainage are preserved for future
GPS resolution via a road centerline database.

### Agency Validation Fails

If new agency values appear that are not in the `CANONICAL_AGENCIES`
dictionary, they are mapped to `"Other"`. To add a new canonical mapping,
update the `CANONICAL_AGENCIES` dict in `morth_blackspots_importer.py`.

### Dedup Produces Unexpected Updates

The importer uses `official_id` (from `black_spot_id`) as the dedup key.
If two CSV rows share the same `black_spot_id`, the second one will update
the first (based on `updated_at` timestamp). This is intentional — each
official black spot ID should appear exactly once in the dataset.
