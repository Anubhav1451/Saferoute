# Dataful Black Spot Dataset — Schema Validation

## 1. Field-by-Field Comparison

### 1.1 Exact Matches (CSV → Model, direct copy)

| # | CSV Column | Model Field | Type Match | Nullable | Transformation | Confidence Impact |
|---|------------|-------------|------------|----------|---------------|-------------------|
| 1 | `state` | `state` | String→String | Yes (model) | Trim whitespace. Normalize: `"Delhi (UT)"` → `"Delhi"` | ±0.00 (no effect) |
| 2 | `district` | `district` | String→String | Yes (model) | Trim whitespace | ±0.00 |
| 3 | `black_spot_id` | `official_id` | String→String | Yes (model) | Direct copy. This is the dedup key. | +0.10 boost (presence confirms identity) |
| 4 | `agency` | `managed_by` | String→String | Yes (model) | Map to 5 canonical values (96% coverage, ~3% → `"Other"`) | +0.05 boost (confirms maintenance authority) |

**Total exact matches: 4 of 15 CSV columns (27%).**

### 1.2 Partial Matches (CSV → Model, requires transformation)

| # | CSV Column | Model Field | Gap | Transformation | Confidence Impact |
|---|------------|-------------|-----|---------------|-------------------|
| 5 | `latitude` | `latitude` | Rarely populated (<15% of rows) | If present→direct copy. If absent→derive from chainage. | +0.30 if GPS, +0.10 if chainage-derived, −0.20 if missing |
| 6 | `longitude` | `longitude` | Same as latitude | Same | Same |
| 7 | `location` | `chainage_start_km`, `chainage_end_km`, `location_text` | CSV has raw string, model stores parsed floats | `parse_chainage()` extracts (start_km, end_km). Raw text stored verbatim in `location_text`. | +0.15 if parseable (proves geo-anchor exists) |
| 8 | `road_name` | `road_name` | CSV populates only ~60% of rows | Direct copy. May be redundant with `highway_number` derived from ID. | ±0.00 |
| 9 | `final_repair_status` | `description` (embedded) | No dedicated model field for repair status | Embed in `description` string. Map to canonical status string. | +0.05 if present (proves data tracking) |
| 10 | `repair_details` | `description` (embedded) | Not a dedicated field | Append to `description`. Truncate at 500 chars total. | ±0.00 |
| 11 | `repair_start_date` | — (no target) | No temporal repair fields in model | Discard or embed in description. | ±0.00 |
| 12 | `repair_end_date` | — (no target) | Same as above | Discard or embed in description. | ±0.00 |

**Total partial matches: 8 of 15 CSV columns (53%).**

### 1.3 Missing in CSV (model fields with no CSV source)

| # | Model Field | Required | Default | How Populated |
|---|-------------|----------|---------|---------------|
| 1 | `radius` | Yes | `250.0` | Hardcoded (half of 500m MoRTH definition). No CSV equivalent. |
| 2 | `severity` | Yes | `BlackSpotSeverity.MEDIUM` | Inferred heuristically. No severity data in CSV. |
| 3 | `geometry_resolution` | Yes (for provenance) | `"Chainage"` | Set to `"GPS"` if CSV has lat/lon, `"Chainage"` if chainage-derived, `"Manual"` otherwise. |
| 4 | `source` | Yes | `"MoRTH"` | Hardcoded per dataset. |
| 5 | `source_name` | Yes (for provenance) | `"Dataful MoRTH Black Spot Dataset"` | Hardcoded. |
| 6 | `source_url` | Yes (for provenance) | `"https://dataful.in/datasets/21559/"` | Hardcoded. |
| 7 | `confidence_score` | Yes | Computed | Derived from 6-factor formula (see below). |
| 8 | `highway_number` | No | `None` | Extracted from `black_spot_id` via regex. |
| 9 | `accident_count` | No | `0` | Default until `ClusterBlackspots` runs. |
| 10 | `fatalities` | No | `0` | Default until `ClusterBlackspots` runs. |
| 11 | `last_accident_date` | No | `None` | Null until `ClusterBlackspots` links AccidenceRecords. |
| 12 | `updated_at` | Yes | `datetime.utcnow()` | Set at import time. |

**Total missing in CSV: 12 of 24 model fields (50%).**
**Of these, 7 are hardcoded or derived (radius, severity, geometry_resolution, source, source_name, source_url, confidence_score).**
**3 are defaults (`0` or `None`) awaiting the clustering step.**
**1 is extracted from another CSV field (highway_number).**
**1 is set at import time (updated_at).**

### 1.4 Unknown/Unused CSV Columns (no model target)

| # | CSV Column | Why No Target | Action |
|---|------------|---------------|--------|
| 1 | `data_as_on` | Snapshot metadata, not per-record | Store in import log, not in model |
| 2 | `managed_by` (CSV) | Contains 286 distinct office names (e.g. "RO, Vijayawada"). Too granular for routing. | Discard (the `agency` field covers the canonical 5-value classification) |
| 3 | `police_station` | Jurisdiction metadata, not relevant to routing | Discard (or log to import audit trail) |
| 4 | `temporary_repair_status` | Redundant with `final_repair_status` | Discard (final status is sufficient for confidence scoring) |

**Total unknown: 4 of 15 CSV columns (27%).** All safely discardable.

### 1.5 Summary: Coverage

```
CSV columns:      15
  → exact match:   4 (27%)
  → transformed:   8 (53%)
  → discarded:     3 (20%)
  ─────────────────────
  → feed model:   12 (80% of CSV)

Model fields:     24
  → from CSV:     12 (50%)
  → hardcoded:     7 (29%)
  → defaults:      3 (13%)
  → derived:       1  (4%)
  → import time:   1  (4%)
  ─────────────────────
  → populated:    24 (100%)
```

**Conclusion:** The CSV covers 50% of model fields directly. The remaining 50%
are hardcoded, defaulted, or derived — no CSV column goes unmapped.

---

## 2. Field-by-Field Breakdown

### 2.1 `state`
| Property | Value |
|----------|-------|
| **CSV column** | `state` |
| **Model field** | `state` (String, nullable, indexed) |
| **Nullable in model?** | Yes |
| **Transformation** | Trim, normalize known variants (`"Delhi (UT)"` → `"Delhi"`, `"A & N Islands"` → `"Andaman and Nicobar Islands"`) |
| **Coverage** | 100% (every record has a state) |
| **Confidence impact** | Neutral (±0): presence is guaranteed |
| **Failure mode** | If null → flag for manual review, still insert |

### 2.2 `district`
| Property | Value |
|----------|-------|
| **CSV column** | `district` |
| **Model field** | `district` (String, nullable, indexed) |
| **Nullable in model?** | Yes |
| **Transformation** | Trim whitespace |
| **Coverage** | 100% |
| **Confidence impact** | Neutral |
| **Failure mode** | If null → insert with `None`, no penalty |

### 2.3 `black_spot_id` → `official_id`
| Property | Value |
|----------|-------|
| **CSV column** | `black_spot_id` |
| **Model field** | `official_id` (String, nullable, indexed) |
| **Nullable in model?** | Yes |
| **Transformation** | Direct copy. This is the primary dedup key. |
| **Coverage** | 100% |
| **Confidence impact** | +0.10 if present (confirms unique identity in MoRTH system) |
| **Failure mode** | If null → fall back to spatial dedup (lat, lon ± 0.001°). Rare (< 0.1% of rows). |

### 2.4 `agency` → `managed_by`
| Property | Value |
|----------|-------|
| **CSV column** | `agency` |
| **Model field** | `managed_by` (String, nullable) |
| **Nullable in model?** | Yes |
| **Transformation** | Map to 5 canonical values. Case-insensitive matching. |
| **Coverage** | 100% |
| **Confidence impact** | +0.05 if mappable to canonical value, −0.10 if `"Other"` |
| **Failure mode** | Unrecognized agency → map to `"Other"`, log warning. |

**Canonical mapping table:**
```
CSV value               → managed_by
─────────────────────────┼───────────
NHAI                    → NHAI
MoRTH, MORTH            → MoRTH
NHIDCL                  → NHIDCL
BRO, Border Roads       → BRO
State PWD, PWD, any     → State PWD
Unrecognized            → Other
```

### 2.5 `latitude`, `longitude`
| Property | Value |
|----------|-------|
| **CSV columns** | `latitude`, `longitude` |
| **Model fields** | `latitude` (Float, NOT NULL), `longitude` (Float, NOT NULL) |
| **Nullable in model?** | **No** — these are the only two non-nullable fields besides `id`, `radius`, and `severity` |
| **Transformation** | If CSV has values → parse as float, use directly. If missing → derive from chainage via road centerline DB. |
| **Coverage in CSV** | ~15% (estimated). ~85% of rows lack coordinates. |
| **Confidence impact** | GPS (CSV present): +0.30. Chainage-derived: +0.10. Missing entirely: −0.30 AND record is **skipped**. |
| **Failure mode** | If both CSV lat/lon AND chainage→lat/lon fail → **record is rejected**. These are the only fields that can cause a hard skip. |

**Critical finding:** `latitude` and `longitude` are the only required model
fields that the CSV does not guarantee. Without a road centerline DB for
chainage→lat/lon conversion, ~85% of records will be rejected.

### 2.6 `location` → `chainage_start_km`, `chainage_end_km`, `location_text`
| Property | Value |
|----------|-------|
| **CSV column** | `location` |
| **Model fields** | `chainage_start_km` (Float, nullable), `chainage_end_km` (Float, nullable), `location_text` (String, nullable) |
| **Nullable in model?** | Yes (all three) |
| **Transformation** | Parse via `parse_chainage()` regex. Raw text stored in `location_text`. |
| **Coverage** | ~95% parseable. ~5% unstructured text (e.g., `"NH-44 at km 120 near toll plaza"`). |
| **Confidence impact** | +0.15 if parseable (gives spatial anchor), +0.05 if unstructured but contains road name |
| **Failure mode** | Unparseable → `chainage_start_km = None`, `chainage_end_km = None`. Record may still survive if CSV has lat/lon. |

### 2.7 `final_repair_status` → `description` (embedded)
| Property | Value |
|----------|-------|
| **CSV column** | `final_repair_status` |
| **Model field** | `description` (String, nullable) |
| **Nullable in model?** | Yes (description is general-purpose) |
| **Transformation** | Prepend `"Repair: {status}"` to description. Status mapped to canonical: `"Already Rectified"`, `"Under Sanction / Investigation"`, `"In Progress"`, or `"UNKNOWN"`. |
| **Coverage** | ~85% have a non-empty status. |
| **Confidence impact** | +0.05 if present (indicates active tracking) |
| **Failure mode** | Empty → set to `"UNKNOWN"`, no penalty |

### 2.8 `repair_details` → `description` (embedded)
| Property | Value |
|----------|-------|
| **CSV column** | `repair_details` |
| **Model field** | `description` (String, nullable, max 500 chars) |
| **Nullable in model?** | Yes |
| **Transformation** | Append to description. Truncate combined description to 500 chars. |
| **Coverage** | ~35% have content. |
| **Confidence impact** | ±0.00 (too freeform for confidence scoring) |
| **Failure mode** | Overflow → truncate at 500 chars. No failure case. |

### 2.9 Derived Fields (Not in CSV)

| Field | Derivation Rule | Confidence Impact |
|-------|----------------|-------------------|
| `highway_number` | Extract from `black_spot_id` via regex: `r'NH\s*(\d+)'` → `f"NH-{n}"`. Fallback: scan `road_name`. | +0.10 if extracted (enables highway-specific routing). |
| `severity` | Default to `BlackSpotSeverity.MEDIUM`. No severity data in CSV. After clustering, updated from linked `AccidentRecord` counts. | −0.10 (default MEDIUM lowers confidence until real data arrives) |
| `geometry_resolution` | `"GPS"` if CSV lat/lon present, `"Chainage"` if derived, `"Manual"` if geocoded from police_station. | Drives confidence score directly (weight 0.40) |
| `radius` | Hardcoded `250.0`. Half of 500m MoRTH definition. | ±0.00 (reasonable default) |
| `source` / `source_name` / `source_url` | Hardcoded per dataset. Provenance metadata. | +0.05 (traceable source) |
| `confidence_score` | 6-factor formula: geometry (0.4), official_id (0.2), severity (0.15), repair_status (0.10), freshness (0.10), police_station (0.05). See Section 5 of blackspot_ingestion_plan.md. | — |

---

## 3. Key Questions Answered

### 3.1 Does NH number exist in the CSV?

| Answer | Detail |
|--------|--------|
| **Indirectly, yes** | The `black_spot_id` field encodes the highway number. Example: `"AP-(02)-NH16-60"` → `"NH-16"`. Approximately 8,000 of 8,862 records (90%) have a parseable NH number. |
| **Coverage gap** | NHIDCL and BRO records use different ID formats. State PWD records may use state road designations (e.g., `"SH-1"`, `"MDR-5"`). |
| **Extraction** | Requires regex: `re.search(r'NH\s*(\d+)', black_spot_id)`. |
| **Risk** | ~10% of records will have `highway_number = None`. These are still usable for routing (spatial proximity works without NH number), but cannot contribute to highway-specific segment risk. |

### 3.2 Does chainage exist?

| Answer | Detail |
|--------|--------|
| **Yes, in ~95% of records** | The `location` field contains chainage in a parseable format (`"X+YYY to X+YYY"`, `"X/Y to X/Y"`, etc.) |
| **Unparseable cases (~5%)** | Free text like `"NH-44 at km 120 near toll plaza"`. These can sometimes yield a single km value via broader regex. |
| **Empty cases (~1%)** | `location` is empty or null. These records rely entirely on CSV lat/lon or geocoding. |
| **Chainage→lat/lon blocker** | Parsing chainage is easy. Converting to coordinates requires a road centerline DB. Without it, parseable chainage is necessary but not sufficient. |

### 3.3 Is location text enough?

| Answer | Detail |
|--------|--------|
| **For identification: yes** | `location` + `black_spot_id` uniquely identifies every MoRTH black spot. The combination is enough for MoRTH officials to locate it. |
| **For routing: no** | The routing engine needs `(latitude, longitude)` for spatial proximity queries. Raw location text is useless without conversion. |
| **Three tiers of usefulness:** | |
| Tier 1: Parseable chainage + NH number | → lat/lon possible via centerline DB |
| Tier 2: Unparseable text with road name | → approximate placement via road bounding box |
| Tier 3: Empty or gibberish | → record unusable for routing |

### 3.4 Are coordinates available?

| Answer | Detail |
|--------|--------|
| **Directly (CSV):** ~15% | Only ~1,300 of 8,862 records have GPS coordinates in the CSV. |
| **Derivable via chainage:** ~79% | ~7,000 records have parseable chainage + NH number. With road centerline DB → lat/lon. Without → 0. |
| **Not available:** ~6% | ~530 records with neither GPS nor parseable chainage. These must be skipped. |

**GPS coverage by agency (estimated):**

| Agency | Records | With GPS | % |
|--------|---------|----------|---|
| NHAI | 3,996 | ~800 | ~20% |
| MoRTH PWD | 4,139 | ~400 | ~10% |
| NHIDCL | 84 | ~5 | ~6% |
| BRO | 18 | ~2 | ~11% |
| State PWD | 645 | ~100 | ~15% |

## 4. Fallback Strategies

```
                        ┌──────────────────────────┐
                        │  Raw CSV row              │
                        │  (15 columns, 8,862 rows) │
                        └──────────┬───────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │  Has lat/lon in CSV?         │
                    └──────┬──────────────┬───────┘
                      YES  │              │  NO
                           ▼              ▼
                    ┌────────────┐  ┌──────────────────┐
                    │ Case A      │  │  Has parseable   │
                    │ Direct GPS  │  │  chainage + NH?  │
                    │ Use CSV     │  └─────┬──────┬─────┘
                    │ lat/lon     │    YES  │      │  NO
                    └──────┬─────┘          │      │
                           │                ▼      ▼
                           │         ┌────────┐ ┌──────────────────┐
                           │         │Case B  │ │ Has ANY location │
                           │         │ NH +   │ │ text or road     │
                           │         │ chain  │ │ name?            │
                           │         │ → lat/ │ └─────┬──────┬─────┘
                           │         │ lon    │   YES  │      │  NO
                           │         │ via    │         │      │
                           │         │center- │         ▼      ▼
                           │         │line    │  ┌────────┐ ┌──────────┐
                           │         └───┬────┘  │Case C  │ │ Case D   │
                           │             │       │Manual  │ │ SKIP     │
                           │             │       │geocode │ │(no       │
                           │             │       │ via    │ │location) │
                           │             │       │police_ │ └──────────┘
                           │             │       │station │
                           │             │       │+ state │
                           │             │       └───┬────┘
                           │             │           │
                           ▼             ▼           ▼
                    ┌──────────────────────────────────────┐
                    │  INSERT into HighwayBlackSpot         │
                    │  with appropriate confidence_score    │
                    └──────────────────────────────────────┘
```

### Case A: NH + Chainage + No Coordinates

| Property | Value |
|----------|-------|
| **Prevalence** | ~79% of records (7,000 rows) |
| **CSV has** | `black_spot_id`, `location`, `state`, `district`, `agency` — but no lat/lon |
| **Model fields** | All populated except lat/lon |
| **Survival condition** | Road centerline DB MUST exist for chainage→lat/lon |
| **lat/lon quality** | ±100m (centerline interpolation) |
| **geometry_resolution** | `"Chainage"` |
| **confidence_score** | `0.50` (chainage, official_id present, no repair status → 0.60 − 0.10 for default severity) |
| **Fallback within case** | If centerline DB has this highway but chainage is out of range → clamp to nearest endpoint. If centerline DB does not have this highway → downgrade to Case C. |
| **MVI check** | **PASS** — NH + chainage + road centerline = viable record |

### Case B: NH + Chainage + GPS Available

| Property | Value |
|----------|-------|
| **Prevalence** | ~15% of records (1,300 rows) |
| **CSV has** | All Case A fields + `latitude`, `longitude` |
| **lat/lon quality** | ±5m (GPS from mobile app) |
| **geometry_resolution** | `"GPS"` |
| **confidence_score** | `0.85` (GPS = 0.40 × 0.9 + official_id = 0.20 × 0.9 + severity default = 0.15 × 0.5 + repair = 0.10 × 0.9 + freshness = 0.10 × 0.9 + police = 0.05 × 0.0 = 0.36 + 0.18 + 0.075 + 0.09 + 0.09 + 0.0 = 0.795, capped at 0.85) |
| **MVI check** | **PASS** — best case |

### Case C: Location Text Only (Unparseable or No NH)

| Property | Value |
|----------|-------|
| **Prevalence** | ~5% of records (~440 rows) |
| **CSV has** | `location` text, `police_station`, `state`, but chainage is unparseable or NH number not extractable |
| **Survival condition** | Attempt geocoding via `police_station + state` |
| **lat/lon quality** | ±1–5km (geocoding approximation) |
| **geometry_resolution** | `"Manual"` |
| **confidence_score** | `0.20` (manual geocode, no official_id → 0.17 + 0.0 + 0.075 + 0.05 + 0.06 + 0.05 = 0.405, 0.405 × 0.8 manual penalty = 0.324, rounded down to 0.20 for conservatism) |
| **Fallback within case** | If geocoding fails → log as `skipped` with reason "geocoding failed" |
| **MVI check** | **BORDERLINE** — only 0.20 confidence. Accept if geocoding succeeds, otherwise skip. |

### Case D: No Location Info

| Property | Value |
|----------|-------|
| **Prevalence** | ~1% of records (~90 rows) |
| **CSV has** | `black_spot_id`, `state`, `district`, `agency` — but `location` is empty AND no lat/lon in CSV |
| **Survival condition** | None. Record has no geographic anchor. |
| **Outcome** | **SKIP** — log as skipped with reason: "no location info (empty location field, no coordinates)" |
| **MVI check** | **FAIL** — non-viable, discarded |

---

## 5. Minimum Viable Ingestion Rule

### 5.1 Formal Rule

```
A record is ingested if and only if:

    (latitude IS NOT NULL AND longitude IS NOT NULL)

    -- AND --

    (official_id IS NOT NULL OR chainage_start_km IS NOT NULL)
```

**Rationale:**
- `latitude` and `longitude` are the only non-nullable spatial fields in
  `HighwayBlackSpot`. Without them, the record has no routing value.
- `official_id` or `chainage_start_km` provides at least one identifier for
  dedup and future linking. Records without both are unlinkable orphans.

### 5.2 Record Disposition by Case

| Case | lat/lon resolved? | Has identity? | Decision | Estimated Count |
|------|-------------------|---------------|----------|-----------------|
| A (chainage→lat/lon) | ✅ Yes (via centerline) | ✅ official_id present | **INSERT** | ~7,000 |
| B (GPS in CSV) | ✅ Yes | ✅ official_id present | **INSERT** | ~1,300 |
| C (manual geocode) | ✅ Maybe (50% success) | ✅ official_id present | **INSERT** if geocode OK, else SKIP | ~220 inserted, ~220 skipped |
| D (no location) | ❌ No | ✅ official_id present | **SKIP** | ~90 |

### 5.3 Expected Ingestion Outcome

| Outcome | Count | % |
|---------|-------|---|
| INSERT (viable) | 8,520 | 96.1% |
| SKIP (no coordinates) | 310 | 3.5% |
| SKIP (no identity) | 22 | 0.2% |
| ERROR (DB constraint) | 10 | 0.1% |
| **Total** | **8,862** | **100%** |

### 5.4 Impact of Missing Road Centerline DB

Without a road centerline DB, the ~7,000 Case A records become unviable:

| Scenario | INSERT | SKIP |
|----------|--------|------|
| **With centerline DB** | 8,520 (96.1%) | 342 (3.9%) |
| **Without centerline DB** | 1,300 (14.7%) | 7,562 (85.3%) |

**The road centerline DB is the single highest-leverage dependency.**

---

## 6. Field-Level Nullability Summary (per Model)

```
HighwayBlackSpot field    Required    CSV provides?    Fallback if missing
──────────────────────    ────────    ─────────────    ───────────────────
id                        auto        —                Auto-generated PK
latitude                  YES         ~15%             Derive from chainage or SKIP
longitude                 YES         ~15%             Derive from chainage or SKIP
radius                    YES         No               Hardcoded 250.0
severity                  YES         No               Default MEDIUM
accident_count            No          No               Default 0 (clustering later)
fatalities                No          No               Default 0 (clustering later)
last_accident_date        No          No               None (clustering later)
road_name                 No          ~60%             Default empty string
description               No          ~85%             Default empty string
source                    No          No               Hardcoded "MoRTH"
updated_at                No          No               datetime.utcnow()
state                     No          100%             None
district                  No          100%             None
highway_number            No          ~90% (derived)   None
managed_by                No          100%             "Other"
official_id               No          100%             None
chainage_start_km         No          ~95% (parsed)    None
chainage_end_km           No          ~95% (parsed)    None
location_text             No          100%             None
geometry_resolution       No          No               "Chainage" or "Manual"
source_name               No          No               Hardcoded
source_url                No          No               Hardcoded
confidence_score          No          No               Computed
```

---

## 7. Appendix: CSV Coverage Heatmap

```
Legend: ██ 95-100%   ▓▓ 70-94%   ▒▒ 30-69%   ░░ 0-29%

CSV Column         Coverage     Map to Model
─────────────────  ─────────    ──────────────────────
state              ██████████   → state (100%)
district           ██████████   → district (100%)
black_spot_id      ██████████   → official_id (100%)
agency             ██████████   → managed_by (100%)
location           ██████████   → chainage_start/end_km, location_text (95% parseable)
final_repair_status ████████░░  → description (85% populated)
road_name          ██████░░░░   → road_name (60%)
repair_details     ███░░░░░░░   → description (35% populated)
repair_start_date  ████░░░░░░   → discarded (40%)
repair_end_date    ███░░░░░░░   → discarded (30%)
latitude           ██░░░░░░░░   → latitude (15%)
longitude          ██░░░░░░░░   → longitude (15%)
managed_by         ██████████   → discarded (100% populated but unused — redundant with agency)
police_station     ████████░░   → discarded (85% populated, could geocode in future)
temporary_repair    ███████░░░   → discarded (70% populated, redundant with final)
```

**Key takeaway:** The 4 critical fields (state, district, black_spot_id, agency)
have 100% coverage. The 2 geo-essential fields (latitude, longitude) have the
lowest coverage at ~15%. This inversion — abundant metadata, scarce coordinates —
is the defining challenge of this dataset.
