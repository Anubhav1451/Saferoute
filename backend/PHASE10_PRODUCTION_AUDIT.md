# Phase 10 — Production Readiness Audit

**Date:** 2026-08-03
**Scope:** `D:\saferoute-ai` (FastAPI + SQLite GIS routing backend, `backend/`), read-only audit.
**Status:** Audit complete. **No code was changed.** This document lists findings only.
**Method:** Manual source review + AST import-graph analysis + targeted greps + runtime checks (`import app.main`, module syntax compilation). All checks run with `PYTHONDONTWRITEBYTECODE=1`; nothing was written except this report.

## Severity definitions (as specified)

| Level | Meaning |
|---|---|
| **P0** | Production-breaking — the app cannot start or serve requests |
| **P1** | Incorrect behaviour — runs, but produces wrong results or silently lies about failures |
| **P2** | Maintainability — hidden traps, drift risk, misleading code/docs |
| **P3** | Cleanup only — dead code, stale artifacts, no runtime effect |

## Summary

| Severity | Count |
|---|---|
| P0 | **0** |
| P1 | **9** |
| P2 | **13** |
| P3 | **~25** (grouped in §4) |

**Positive checks (verified):**
- The app **starts**: `from app.main import app` imports cleanly, all routers register, no circular imports anywhere in `app/` (AST dependency-graph DFS found zero cycles).
- No secrets leaked: `.gitignore` covers `*.db`, `.env`, `backend/.env`. `backend/.env` is untracked. Only config keys (`SECRET_KEY`, `MAPBOX_TOKEN`, `DATABASE_URL`, `DEBUG`, `WEATHER_API_KEY`) were inspected; **no secret values were read or printed**.
- The 5 live Alembic migrations form a linear, internally-consistent chain (`12aa197acd99 → 6fc9b1c4c063 → 8a4f5e2c1b9d → fcc643765f4f → 520e30f0c181`) and `alembic/env.py` targets the same DB the app uses (`settings.DATABASE_URL`, made absolute under `backend/`).

**Two findings are closest to P0 and time-sensitive.** They are P1 today because the working tree runs fine, but both become P0 the moment code is deployed from a fresh checkout/clone (see **P1-6** and **P1-7**).

---

## 1. P1 — Incorrect behaviour (9 findings)

### P1-1. `/sos/simulate` returns HTTP 200 on every failure
- **Location:** `backend/app/api/v1/sos.py:53-61`
- **Impact:** Every error path in the SOS endpoint returns a **success-status response**. The handler does `return error_response(...)` where `error_response()` builds a plain dict (`{"success": False, ...}`). FastAPI serializes a returned dict as HTTP **200 OK**. A client or monitoring stack that watches status codes cannot distinguish a failed SOS from a successful one — for a safety-critical endpoint this is a silent lie to downstream systems.
- **Proof:** `error_response` (in `app/api/responses.py`) returns a dict, not a `JSONResponse`/`HTTPException`. Lines 53-61 return it directly from the route handler with no status override. Contrast with `app/api/v1/routing.py`, where errors are raised/returned as `JSONResponse` with explicit non-2xx statuses.
- **Reproduction:** POST `/api/v1/sos/simulate` with an input that triggers the `except ValueError` branch (e.g. missing required field); observe HTTP `200` in the response status line with `"success": false` in the body.
- **Smallest safe fix:** Return `JSONResponse(content=error_response(...), status_code=400)` for `ValueError` and `500` for the generic `except`, or `raise HTTPException(status_code=..., detail=error_response(...))` — matching the pattern already used in `routing.py`. No API-shape change (body stays identical).

### P1-2. Risk lookup keys on `RoadSegmentRisk.id == graph edge id` — a coincidental identity
- **Location:** `backend/app/services/routing.py:471-472` (`_get_safety_cost`)
- **Impact:** Safe routing fetches a segment's risk via `self.db.query(RoadSegmentRisk).filter(RoadSegmentRisk.id == edge_id)`. `RoadSegmentRisk.id` is an **autoincrement primary key** (`app/db/models.py`), **not** aligned to `graph_edges.id`. There is no foreign key or stable join column. In production the edge id and risk-record id agree only by coincidence, so the risk lookup returns `None` (→ cost falls back to raw edge length) or — worse — a risk record for a *different* edge. The "safest route" therefore does not reflect the actual risk data.
- **Proof:** `RoadSegmentRisk.id` is an autoincrement PK; `GraphEdge.id` is a separate sequence. The entire test suite masks this because `routing_test_helpers.create_graph_session()` deliberately sets risk record ids = edge ids (1, 2) on the 3-node in-memory graph. Two competing mechanisms exist in the same file: `_calculate_safety_score` (lines 277-313) preloads **all** risk records and picks the nearest by point distance — a correct approach — while `_get_safety_cost` (line 471) does the per-edge-id query. The per-edge path is the one used by safe-mode A\*.
- **Reproduction:** Load a real DB (or a graph where edge ids ≠ risk ids) and run safe-mode routing; log the `risk_data` value in `_get_safety_cost` — it is `None`/wrong for most edges.
- **Smallest safe fix:** In `_get_safety_cost`, use the same nearest-record-by-coordinate approach already used by `_calculate_safety_score` (lines 277-313), or join on a real key (e.g. `osm_way_id`). This also removes the N+1 per-edge query (see P2-13).

### P1-3. Safe-mode A\* is greedy per-edge, not path-optimal
- **Location:** `backend/app/services/routing.py:426`
- **Impact:** Safe mode sets `f_score[neighbor.id] = safety_cost + (heuristic * 1.0)` where `safety_cost` is the **cost of only the single incoming edge**. Fast (line 422) and balanced (line 429) modes correctly use `tentative_g_score + heuristic*K`, i.e. the **accumulated** path cost. Because safe mode never accumulates `g_score`, the first expansion by per-edge cost wins and the returned "safest" path is locally greedy rather than globally safety-optimal — it can return a route that is *not* the minimum-total-risk path.
- **Proof:** Lines 422/426/429 in `_astar_search`: only the safe branch uses the per-edge value as `f_score`.
- **Reproduction:** Build a graph where one low-risk edge feeds into a long chain of high-risk edges, while a slightly higher first edge leads to a low-risk remainder; safe mode picks the wrong overall route.
- **Smallest safe fix:** Thread the per-edge safety cost into the accumulated `tentative_g_score` for the safe branch and use `tentative_g_score + heuristic*1.0` for `f_score` (as the other two modes do), keeping the `weight_mode` selection from Phase 9A C5 unchanged.

### P1-4. Same source/destination fabricates a straight-line "route" with no road
- **Location:** `backend/app/services/routing.py:543` — `if start_node.id == end_node.id:` returns `[source, destination]` directly.
- **Impact:** Requesting a route where the nearest start and end nodes are the same node returns a **fabricated two-point straight line** that follows no road — the exact anti-pattern removed for the *unreachable* case in Phase 9A (C4) still exists for the *identical-node* case. Clients receive plausible-looking geometry and a distance that no vehicle can travel.
- **Proof:** The branch at line 543 short-circuits `find_safest_route` and returns the raw coordinates as `safest_route`.
- **Reproduction:** Call `find_safest_route` with source and destination snapping to the same graph node (e.g. identical coordinates); observe a 2-point "route".
- **Smallest safe fix:** Apply the Phase 9A C4 treatment here too: raise `ValueError("Source and destination are the same node")` (→ HTTP 400 `VALIDATION_ERROR` via the existing handler in `routing.py`), or return an explicitly-empty result — do **not** return fabricated geometry.

### P1-5. `predict_safety_score` silently returns a fabricated 0.5 on any failure
- **Location:** `backend/ml/safety_model.py:362` (broad `except Exception: return 0.5`)
- **Impact:** Any failure (missing/untrained model, bad input, feature mismatch) is swallowed and reported as a **midpoint safety score of 0.5** with no error signal. The AI safety-score endpoint (`/ai/safety-score`) then serves a made-up number as if it were real model output. A safety-critical score has no failure path.
- **Proof:** `get_safety_model()` instantiates an **untrained** `RandomForestClassifier` when `safety_model.joblib` is absent; predicting on it raises `NotFittedError`, which line 362 catches and converts to 0.5. The same catch-all also swallows genuine input errors.
- **Reproduction:** Delete/rename `ml/models/safety_model.joblib` and call `predict_safety_score(...)` — returns `0.5`, no exception, no log.
- **Smallest safe fix:** Let the exception propagate (or return `None`) so the API layer returns a 500/`ML_MODEL_UNAVAILABLE` error instead of a fabricated score; at minimum, `logger.exception(...)` before the fallback.

### P1-6. Migrations create only 6 of 14 ORM tables — fresh `alembic upgrade head` DB cannot route
- **Location:** `backend/alembic/versions/*.py` vs `backend/app/db/models.py`
- **Impact:** The 5 live migrations create only `safety_nodes`, `crime_hotspots`, `user_reports`, `highway_black_spots`, `road_segment_risks`, `accident_records`. **No migration creates** `osm_ways`, `osm_way_nodes`, `graph_nodes`, `graph_edges`, `traffic_flow`, `traffic_incidents`, `road_closures`, `construction_zones`. A database built purely from migrations has none of the graph/traffic tables; the first routing call (`routing.py` queries `graph_nodes`/`graph_edges`, `cost_engine.py` queries the traffic tables) raises `sqlite3.OperationalError: no such table`. Column-level drift on the 6 covered tables is **zero** (all ORM columns are present). The gap is hidden today because the dev DB is created via `Base.metadata.create_all` (`init_db.py`, graph-builder scripts), bypassing migrations entirely.
- **Proof:** AST comparison of all `op.create_table` targets in the 5 migration files vs all `__tablename__` declarations in `models.py` — the 8 tables above appear only in models.
- **Reproduction:** `rm saferoute.db && alembic upgrade head && python -c "import sqlite3; c=sqlite3.connect('saferoute.db'); print([r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")])"` → `graph_nodes`, `graph_edges`, `traffic_*`, `road_closures`, `construction_zones` absent.
- **Smallest safe fix:** Add a single new migration that creates the 8 missing tables (mirroring the deleted `add_osm_graph_tables` / `add_traffic_models` migrations — see P1-7), so `upgrade head` yields the full ORM schema. Verify with a fresh-DB smoke test.

### P1-7. 11 Alembic migration sources deleted — migration history cannot be reproduced
- **Location:** `backend/alembic/versions/` (5 `.py`) vs `backend/alembic/versions/__pycache__/` (11 orphaned `.pyc`).
- **Impact:** Deleted (only `.pyc` remain): `a1b2c3d4e5f6_add_osm_graph_tables`, `add_emergency_management_tables`, `add_fleet_management_tables`, `add_government_management_tables`, `add_personal_driver_tables`, `add_postgis_geometry_support`, `add_traffic_models`, `add_traffic_prediction_probability_columns`, `b7e2c4d91f6a_add_pipeline_performance_indexes`, `merge_traffic_pipeline_heads`, `rc91_add_route_monitor_and_offline_tables`. These are precisely the migrations that created the graph/traffic tables (hence P1-6). Any database whose `alembic_version` row references a deleted revision cannot `upgrade`/`downgrade` ("Can't locate revision ...").
- **Proof:** `ls alembic/versions/*.py` (5) vs `ls alembic/versions/__pycache__/*.pyc` (16) — 11 pycs have no source.
- **Reproduction:** Point alembic at a DB that was migrated under the old chain; `alembic current`/`upgrade` fails to resolve the head.
- **Smallest safe fix:** Squash history into a single baseline migration covering all 14 tables (also resolves P1-6) and reset/verify `alembic_version`; delete the orphaned pycs.

### P1-8. The entire `backend/app/graph/` package is untracked in git — a fresh checkout cannot import the routing engine
- **Location:** `backend/app/graph/` — `cost_engine.py`, `spatial_index.py`, `nearest.py`, `cost_config.py`, `cost_models.py`, `projection.py`, `__init__.py` are all `??` (untracked); only the now-deleted `risk_engine.py` was ever tracked (`D` in git status).
- **Impact:** `app/services/routing.py` (tracked, modified) imports `app.graph.cost_engine`, `app.graph.nearest`, `app.graph.spatial_index`. Since none of those files exist at `HEAD`, a **fresh clone/checkout of the committed code fails to import the routing service** and the API cannot start. The core routing engine exists only in the working tree.
- **Proof:** `git ls-files backend/app/graph/` → empty. `git status --porcelain backend/app/graph/` → `?? backend/app/graph/`.
- **Reproduction:** `git stash -u` (or fresh `git clone`) then `cd backend && python -c "import app.main"` → `ModuleNotFoundError: No module named 'app.graph.cost_engine'` (via `routing.py`).
- **Smallest safe fix:** `git add backend/app/graph/` (commit the routing engine) before any deploy. This is the **highest-priority P1**: it is time-sensitive and cheap to fix.

### P1-9. `scripts/data_ingestion/validate_graph.py` missing but imported by two pipeline scripts
- **Location:** `backend/scripts/data_ingestion/validate_graph.py` (absent; only `__pycache__/validate_graph.cpython-312.pyc` remains). Importers: `scripts/g6_phase3_remaining.py:269` (module-body import) and `scripts/g6_validate.py:630` (function-body import).
- **Impact:** Both G6 data-ingestion pipeline entry points crash with `ModuleNotFoundError: No module named 'scripts.data_ingestion.validate_graph'`. The graph-validation stage of the data pipeline — which produces the production graph data — cannot run.
- **Proof:** `ls scripts/data_ingestion/validate_graph.py` → "No such file"; grep shows exactly the two importers.
- **Reproduction:** `cd backend && python scripts/g6_validate.py` → `ModuleNotFoundError` at the graph-validation step.
- **Smallest safe fix:** Restore `validate_graph.py` (recoverable from git history, or from the stale `.pyc` metadata) implementing `GraphValidator` with `run_all_checks()`, **or** — if the validation stage was intentionally dropped — remove the import and the corresponding step from both scripts.

---

## 2. P2 — Maintainability (13 findings)

### P2-1. `asyncio.to_thread` shares a request-bound SQLAlchemy Session across threads
- **Location:** `backend/app/api/v1/routing.py` (`/calculate` handler, `asyncio.to_thread` around routing)
- **Impact:** A single `Session` created for the request is used inside a worker thread while the event loop may also touch it. `Session` is not thread-safe; under concurrent `/calculate` calls this can produce intermittent `DetachedInstanceError` / lost-update style failures.
- **Proof:** Handler passes the request-scoped `db` dependency into `asyncio.to_thread(...)`.
- **Smallest safe fix:** Create a fresh `Session` inside the thread function (or use a per-thread sessionmaker), closing it before returning.

### P2-2. `load_env_file()` unconditionally overrides real environment variables and duplicates pydantic-settings
- **Location:** `backend/app/main.py:13-29`
- **Impact:** `.env` is force-read into `os.environ` at startup, overwriting variables already set in the real environment; meanwhile `app/core/config.py` already loads the same `.env` via `model_config.env_file`. Two code paths read one file; a stray `.env` on the deploy host silently overrides a correctly-set production environment variable.
- **Proof:** `load_env_file()` uses plain `os.environ.setdefault`-free assignment; `config.py` has `model_config.env_file = BASE_DIR / ".env"`.
- **Smallest safe fix:** Delete `load_env_file()` and rely on pydantic-settings' `env_file` handling alone.

### P2-3. `DEBUG=True` shipped in `backend/.env`
- **Location:** `backend/.env` (`DEBUG=True`)
- **Impact:** `validate_production_secrets` fail-fast (which guards `SECRET_KEY`/`MAPBOX_TOKEN` presence) is **bypassed** whenever `DEBUG=True`, and the `/debug/env` endpoint (which dumps environment state) becomes reachable. A production deployment that accidentally keeps this `.env` runs in debug mode with no startup guardrail.
- **Proof:** `config.py` `model_validator` is gated on `not settings.DEBUG`; `/debug/env` is served only when `settings.DEBUG` is true.
- **Smallest safe fix:** Ship with `DEBUG=False` and no `.env` in the artifact; rely on real env vars in production.

### P2-4. Dead penalty constants masquerade as live configuration
- **Location:** `backend/app/core/config.py:71-79, 85, 95-98` — `CRIME_HOTSPOT_HIGH_PENALTY_BASE`, `SAFETY_NODE_LOW_LIGHTING_PENALTY`, `USER_REPORT_BASE_PENALTY`, `HIGH_RISK_SEGMENT_*`, `ROUTE_COST_ALPHA`, `RISK_FACTOR_*`
- **Impact:** Zero references anywhere in the codebase. They read as tunable product knobs but have no effect — anyone adjusting them will think they changed routing behaviour.
- **Proof:** `grep -rn "ROUTE_COST_ALPHA\|CRIME_HOTSPOT_HIGH_PENALTY_BASE\|SAFETY_NODE_LOW_LIGHTING_PENALTY\|USER_REPORT_BASE_PENALTY\|RISK_FACTOR_\|HIGH_RISK_SEGMENT_" --include=*.py .` → matches only in `config.py`.
- **Smallest safe fix:** Delete the constants (or add a `# deprecated` comment), and ensure the live cost logic's weights live in `cost_engine.py`/`cost_config.py` where they are actually read.

### P2-5. Stale `/calculate` docstring claims features that no longer exist
- **Location:** `backend/app/api/v1/routing.py:21-31`
- **Impact:** The endpoint docstring says it "considers crime hotspots, safety nodes, user reports" — none of these are consulted by the routing path anymore (risk comes from `RoadSegmentRisk`, traffic from `TrafficFlow`). Misleading API documentation.
- **Proof:** Routing path (`app/services/routing.py`) never queries those models; only `RoadSegmentRisk`/traffic tables are read.
- **Smallest safe fix:** Rewrite the docstring to describe the actual inputs (risk data + traffic), and similarly refresh any downstream comments referencing the old inputs.

### P2-6. Duplicated core geometry: two haversines and two spatial indexes
- **Location:** `backend/app/services/routing.py:69-90` (`_haversine_distance`, `math.asin`) vs `backend/app/utils/geospatial.py` (`haversine_distance`, `atan2`); `backend/app/services/graph_utils.py` (`GraphSpatialIndex`) vs `backend/app/graph/spatial_index.py` (`DatabaseSpatialIndex`)
- **Impact:** Two implementations of the same distance calculation and two spatial-index strategies. The `math.asin` variant is numerically unstable for near-antipodal points; drift between the copies risks subtle inconsistency between route metrics and scoring.
- **Proof:** Both functions compute the same haversine differently; `routing.py` imports its own instead of `geospatial.py`'s; `graph_utils.GraphSpatialIndex` is used only by dev scripts while the app uses `DatabaseSpatialIndex`.
- **Smallest safe fix:** Delete `_haversine_distance` from `routing.py` and import the canonical one from `geospatial.py`; keep one spatial index (the app's) and mark `GraphSpatialIndex` dev-only (see P3-3).

### P2-7. `/ai/safety-score` response envelope is inconsistent with the rest of the API
- **Location:** `backend/app/api/v1/ai.py`
- **Impact:** Returns a custom dict (`success`/`data`/`message`) without `error`/`error_code`/`timestamp` that `success_response`/`error_response` provide elsewhere, and its `except Exception` path raises `HTTPException(500, str(e))`, **leaking internal error text** to clients. Inconsistent client contract and information disclosure.
- **Proof:** Compare handler payload to `responses.success_response`; the error path embeds `str(e)`.
- **Smallest safe fix:** Return `success_response(...)` on success; on failure return the standard `error_response` envelope (without `str(e)` in the message) with HTTP 500.

### P2-8. `validation_exception_handler` imported but never registered — 422s bypass the standard envelope
- **Location:** `backend/app/main.py:40` (import) vs `:67-68` (only `Exception` and `HTTPException` handlers registered)
- **Impact:** Pydantic validation failures return FastAPI's **default** `{"detail": [...]}` body, not the project's `error_response` format the author clearly intended. Every other error is standardized; 422 is the odd one out, so clients cannot parse validation errors uniformly.
- **Proof:** `grep -n "validation_exception_handler\|add_exception_handler" app/main.py` — imported at line 40, never registered.
- **Smallest safe fix:** `app.add_exception_handler(RequestValidationError, validation_exception_handler)` (import `RequestValidationError` from `fastapi.exceptions`).

### P2-9. `ml/verify_upgrade.py` is corrupted by an un-substituted regex
- **Location:** `backend/ml/verify_upgrade.py:16` — `from \1.\2 import SafetyScoreModel, get_safety_model, predict_safety_score`
- **Impact:** The file has a `SyntaxError` ("unexpected character after line continuation character") and cannot run at all. It is a standalone model-upgrade verification tool; if the team relies on it after model swaps, it fails immediately.
- **Proof:** `python -B -c "compile(open('ml/verify_upgrade.py').read(), 'x', 'exec')"` → SyntaxError; it is the **only** syntax failure across all backend `.py` files.
- **Smallest safe fix:** Restore the intended import, e.g. `from ml.safety_model import SafetyScoreModel, get_safety_model, predict_safety_score` (names verified to exist), or delete the file if obsolete.

### P2-10. `get_edges_within_radius` silently truncates at 900 edges
- **Location:** `backend/app/services/graph_utils.py` (`filtered_ids[:900]`)
- **Impact:** A caller asking for all edges within a radius gets an arbitrary 900-edge slice with no warning — silently incomplete spatial queries. (Applies today only to dev scripts, since the app uses `DatabaseSpatialIndex`, but the helper is a live API of the module.)
- **Proof:** The slice is unconditional on the result set.
- **Smallest safe fix:** Remove the hard cap, or return a `(edges, truncated: bool)` tuple and log when truncation occurs.

### P2-11. `check_routes.py` validates against the in-memory test graph, not the real DB
- **Location:** `backend/check_routes.py` (uses `create_graph_session()` from `routing_test_helpers`)
- **Impact:** The Phase 9A report states `check_routes.py` "runs clean against the real DB"; it actually runs against the 3-node `sqlite:///:memory:` test graph. Any correctness conclusion drawn from it about production data is unverified — a verification gap, not a runtime bug.
- **Proof:** File imports `create_graph_session` (in-memory) rather than opening `settings.DATABASE_URL`.
- **Smallest safe fix:** Add a mode that opens the real DB via `app.db.session` and snapshots a few real edges/nodes; keep the in-memory mode for CI.

### P2-12. `prediction_log.csv` is written on every prediction and is git-tracked
- **Location:** `backend/ml/models/prediction_log.csv` (tracked) written by `ml/safety_model.py:_log_prediction`
- **Impact:** Each `/ai/safety-score` call appends a row to a **tracked** file, producing uncommittable churn and unbounded log growth inside the repo. (Confirmed tracked: it appears as `M` in `git status`.)
- **Proof:** `git status` shows `M backend/ml/models/prediction_log.csv`; `_log_prediction` opens it in append mode.
- **Smallest safe fix:** Move the log path outside the repo (e.g. `data/`, log dir, or `./runtime/`) and add it to `.gitignore`; remove the file from git tracking (`git rm --cached`).

### P2-13. N+1 risk query in safe-mode A\* (same code as P1-2)
- **Location:** `backend/app/services/routing.py:471`
- **Impact:** One `RoadSegmentRisk` SELECT per edge explored in safe mode — on a real 621k-edge graph this is thousands of DB round-trips per request. Performance and the P1-2 correctness bug share this line; fixing P1-2 (preload/nearest-by-coordinate) resolves both.
- **Proof:** The per-edge query is inside the A\* neighbor loop; contrast with `_calculate_safety_score`'s single bulk `query(RoadSegmentRisk).all()` (line 295).
- **Smallest safe fix:** Same as P1-2 — reuse the bulk-loaded `_risk_records` nearest lookup instead of a per-edge query.

---

## 3. P0 — none found

The app imports and starts; no startup exception, no circular import, no live broken reference inside `app/`. The two P1 items closest to P0 are **P1-8** (untracked `app/graph/` → fresh checkout cannot import routing) and **P1-6** (missing migrations → migrated DB cannot route). Either becomes P0 at the moment of a fresh-clone deployment.

---

## 4. P3 — Cleanup only (~25 items, grouped)

| # | Item | Location | Note |
|---|---|---|---|
| P3-1 | Dead duplicate exception handlers | `app/api/responses.py:73-105` | Copies of `http_exception_handler`/`general_exception_handler`; live ones live in `app/api/exceptions.py` |
| P3-2 | Dead `APIException` | `app/exceptions.py` | Never raised/imported anywhere; even if raised, the live handler drops `.error_code` |
| P3-3 | Orphaned `projection.py` | `app/graph/projection.py` | 276 lines, zero importers |
| P3-4 | `APIResponse.timestamp: str = None` | `app/api/responses.py` | Broken default in Pydantic v2; uses deprecated `datetime.utcnow()` |
| P3-5 | Orphaned cost config API | `app/graph/cost_config.py` | `traffic_congestion_multiplier`, `COST_PROFILES`, `get_cost_profile`, `load_cost_config_from_file`, `get_default_cost_config` — zero callers; `load_cost_config_from_app` checks `hasattr(settings,'COST_WEIGHT_CONFIG')` which does not exist → always defaults |
| P3-6 | Dead geodesy helpers | `app/utils/geospatial.py` | `meters_to_degrees_latitude`/`meters_to_degrees_longitude` — zero callers |
| P3-7 | 112 stale `.pyc` for deleted modules | `backend/**/__pycache__/` | `app/api/v1` (ai_copilot, emergency, fleet, government, offline, personal_driver, prediction, traffic, voice, websocket), `app/services` (16), `app/graph` (20, incl. deleted `risk_engine`, `chainage`, `edge_factory`), `ml/prediction` (whole package), alembic (11, see P1-7), root/tests |
| P3-8 | Empty test directory | `backend/tests/` | No tests; suite lives in root `test_*.py` |
| P3-9 | Bare `except` / `pass` blocks | `app/graph/cost_engine.py:267,287,482,511`; `app/api/middleware/request_size.py:69` (`pass`); `app/graph/cost_config.py:96,99` (`pass`) | Silent failure swallowing; `# noqa`-worthy or narrow to specific exception types |
| P3-10 | Latitude-zero ZeroDivisionError swallowed | `ml/data_ingestion.py:28,61,92` | `abs(latitude * 0.0174533)` → `0` at lat 0 → `ZeroDivisionError` → falls through to 0.5; only reachable at the equator |
| P3-11 | Unused imports | See table below | Harmless but noisy |
| P3-12 | `RouteResponse` schema imported but unused | `app/api/v1/routing.py:9` | Response is an untyped dict; schema bypassed |
| P3-13 | In-process rate limiting | `app/api/middleware/rate_limit.py` | Buckets live only in process memory — useless across multiple workers (only matters once the middleware is enabled; it is P3 today) |
| P3-14 | Lazy/deferred imports (no cycles) | `cost_config.py:87`, `middleware/__init__.py`, `responses.py`, `routing.py:345` | Cosmetic; hoisting them would not create a cycle (graph is acyclic) |
| P3-15 | `generate_mock_data.py` hardcodes `DATABASE_URL` | `app/utils/generate_mock_data.py` | Ignores `settings`; may seed a different DB than the app uses |
| P3-16 | Standalone/orphan data scripts | `scripts/data_ingestion/cluster_blackspots.py`, `nhai_blackspots_importer.py` | Never imported; NHAI importer not wired into the g6 pipeline (MoRTH importers only) |
| P3-17 | Fragile namespace-package imports | `ml/test_api.py:12`, `ml/test_api_endpoint.py:12` (`from backend.app.main import app`) | Works only via implicit namespace package + repo root on `sys.path`; breaks if `backend/__init__.py` is ever added |
| P3-18 | Stale comments | `test_caching_safety.py:47` ("0.8 placeholder" — score is now data-driven), `routing.py` docstring comments | Misleading leftovers |
| P3-19 | `_traffic_tables_empty` runs 4 `first()` queries per request | `app/graph/cost_engine.py` | Runs on first edge-cost computation of each request; cache the result or skip when tables are known present |
| P3-20 | Unused handler imports | `sos.py` (`status`, `db` dependency), `ai.py`, `responses.py` (`Dict`) | Cosmetic |

### Unused imports (P3-11 detail)

| File | Unused |
|---|---|
| `app/main.py:5,31,40` | `Path`, `Request`; `validation_exception_handler` (unregistered — see P2-8) |
| `app/services/routing.py:10,11,18` | `datetime`, `timedelta`, `Tuple`, `Any`, `RouteSegment` |
| `app/graph/cost_engine.py:10` | `func` (from `sqlalchemy`) |
| `app/core/config.py:4,6` | `Optional`, `os` |
| `app/api/responses.py:2` | `Dict` |
| `app/api/v1/routing.py:4,9` | `HTTPException`, `RouteResponse` |
| `app/api/v1/sos.py:3` | `status` |
| `app/services/graph_utils.py:3,5,6` | `Any`, `func`, `OSMWayNode` |
| `app/exceptions.py:3` | `Optional`, `Dict`, `Any` (file dead — P3-2) |

### Audit checklist coverage (the requested scan categories)

| Requested check | Verdict |
|---|---|
| TODO / FIXME / XXX / HACK | 1 match total (a `[SIMULATED]` marker in `sos.py:38`); **no open TODOs** in app/ml/scripts |
| `pass` | 5 in `app/` (all exception-swallowing — see P3-9) |
| Bare `except` | `cost_engine.py` (×4), `request_size.py` (×1), plus `except Exception` catch-alls in `safety_model.py` (P1-5) and `sos.py` (P1-1) |
| Duplicated logic | Haversine ×2 (P2-6); spatial index ×2 (P2-6); risk-score derivation ×2 (P1-2) |
| Unreachable code | Safe-mode f_score branch (P1-3); dead config constants (P2-4); dead helpers (P3-5, P3-6); fabricated route branch (P1-4) |
| Dead imports | Full list above (P3-11) |
| Unused files / orphan modules | `projection.py`, `exceptions.py`, `graph_utils.py` (dev-only), `generate_mock_data.py` (dev-only), `cluster_blackspots.py`, `nhai_blackspots_importer.py` (P3) |
| Unused services | None at `app/` level — all registered routers are live; dev services are `graph_utils` (P2-6) |
| Stale migrations | **P1-6** (8 tables missing) and **P1-7** (11 deleted sources) |
| Broken references | **P1-9** (`validate_graph.py`) and **P2-9** (`verify_upgrade.py`) — the only two in the repo |
| Circular imports | **None** — app graph is acyclic (verified) |
| Startup problems | None today; **P1-8** breaks a fresh checkout; **P1-6** breaks a migrated DB |
| Hidden runtime exceptions | **P1-5** (predict→0.5), **P1-1** (SOS error→200), P3-10 (lat=0) |
| Silent exception swallowing | **P1-5**, P3-9 (bare `except`/`pass`), P3-10 |

---

## 5. Reproduction order / quick verification commands

```bash
# Fresh-checkout import breakage (P1-8)
git ls-files backend/app/graph/                    # empty -> package untracked

# Migrated-DB schema gap (P1-6)
cd backend && rm -f /tmp/audit.db && alembic -x sqlalchemy.url=sqlite:////tmp/audit.db upgrade head \
  && python -c "import sqlite3; c=sqlite3.connect('/tmp/audit.db'); print([r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")])"

# SOS error status (P1-1)
# POST /api/v1/sos/simulate with a value-erroring payload -> observe HTTP 200

# predict_safety_score silent 0.5 (P1-5)
cd backend && python -B -c "from ml.safety_model import predict_safety_score; print(predict_safety_score.__module__)" \
  # then rename ml/models/safety_model.joblib and call the function -> 0.5, no raise

# verify_upgrade.py corruption (P2-9)
cd backend && python -B -c "compile(open('ml/verify_upgrade.py').read(),'x','exec')"   # SyntaxError

# validate_graph.py missing (P1-9)
cd backend && python -B scripts/g6_validate.py     # ModuleNotFoundError
```

---

## 6. Constraints honoured

Per the Phase 10 spec, this audit performed **no** code changes, no architecture redesign, no feature work, no performance optimization, no API/schema/response-format changes, and no frontend changes. The single output file is this document. **Awaiting approval before any fix is applied.**
