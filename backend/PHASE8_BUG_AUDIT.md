# Phase 8 — Production Bug Audit

**Scope:** Real production bugs only. No fixes applied. No architecture changes, no routing rewrites, no optimizations, no new features.
**Method:** Static inspection of the full production surface (`app/` + `ml/`), with every high-value finding **empirically reproduced** on an in-memory SQLite graph. Line numbers are exact as of this audit.

---

## Verification notes

All findings marked **[reproduced]** were confirmed by executing the code path against a synthetic in-memory graph. Findings marked **[static]** are reachable only through a code path not exercised in this audit (e.g. dead code), and are flagged accordingly.

---

## CRITICAL — routing produces wrong/meaningless results

### C1. `_get_safety_cost` raises NameError on every call → the "safest route" ignores all risk data **[reproduced]**
- **File/Line:** `app/services/routing.py:437-459` (reference to `RoadSegmentRisk` at lines 439-440)
- **Root cause:** `RoadSegmentRisk` is **not imported** in `routing.py` (line 14 imports only `GraphNode, GraphEdge`). The query `self.db.query(RoadSegmentRisk)` raises `NameError: name 'RoadSegmentRisk' is not defined` inside the `try`, which is then caught by the bare `except Exception` at line 452.
- **Runtime impact:** For **every edge** during a `weight_mode='safe'` A* run, the NameError fires and the fallback returns `float(edge.length)` (line 458). Risk data is never consulted. Worse, the `except` block **does not log anything**, so this is completely invisible in logs.
- **Reachability:** **[reproduced]** — `_get_safety_cost(2)` on a high-risk edge (risk_score=0.9) returned `30.0` (edge length) instead of a risk-based cost; `fast` and `safe` paths were identical `[1,2,3]` on a graph where the safe path should have differed.
- **Minimal safe fix:** Add `RoadSegmentRisk` to the `from app.db.models import ...` on line 14. That one import makes the intended risk logic execute. (Do not touch the algorithm.)

### C2. "Safe" and "fast" routing modes are effectively inverted in what they minimize **[static, derived from C1]**
- **File/Line:** `app/services/routing.py:390-399` (`_astar_search` f_score logic)
- **Root cause:** The `'fast'` branch (line 392) accumulates `tentative_g_score`, which uses `_get_edge_cost` → `cost_engine.compute_edge_cost` → **risk, traffic, road-class costs included**. The `'safe'` branch (line 396) uses `_get_safety_cost`, which is broken (C1) and returns **raw edge length only** — the least safety-aware value available.
- **Runtime impact:** The route labeled "safest" is the one minimizing plain distance (plus heuristic); the route labeled "fastest" is the one minimizing the full risk+traffic+length cost. For any dataset where risk varies between edges, the two labels are swapped in meaning. Clients comparing `safest_route` vs `fastest_route` get the opposite of the product intent.
- **Reachability:** Every request (both A* runs always execute). **[reproduced]** via C1's identical-paths result on the risk-varying graph.
- **Minimal safe fix:** Fix C1 (import). Then verify the `'safe'` branch uses risk-aware cost and the `'fast'` branch uses distance/traffic cost as intended. This is a routing-logic decision — confirm the intended semantics before changing.

### C3. `_calculate_safety_score` returns a hardcoded placeholder — all reported safety scores are fake **[static]**
- **File/Line:** `app/services/routing.py:268-283`
- **Root cause:** The function body is `return 0.8  # Placeholder - reasonably safe`. The docstring claims it queries nearby `RoadSegmentRisk`, but no query is issued.
- **Runtime impact:** `safest_safety_score`, `fastest_safety_score`, and every segment's `safety_score` in `route_segments` are always `0.8` regardless of actual risk. The API reports a safety score that has no relationship to the data.
- **Reachability:** Every request that computes metrics. **[static]** but trivially true from code.
- **Minimal safe fix:** Wire it to the edge costs already computed by `RouteCostEngine` (per-segment risk_cost), or query `RoadSegmentRisk` near the segment midpoint. Out of audit scope to implement.

### C4. A* open-set exhaustion silently returns a straight-line path that follows no road **[reproduced]**
- **File/Line:** `app/services/routing.py:403-408`
- **Root cause:** When the open set is exhausted without reaching the goal (disconnected graph, or >`max_nodes_to_explore`=10000 explored), the method logs a warning and returns `[start_node, goal_node]` — a direct line.
- **Runtime impact:** A route to an unreachable point is returned with HTTP 200 containing a geometrically straight path that may cross open water, walls, or off-road terrain. `find_safest_route` never checks for this; the API reports it as a valid route.
- **Reachability:** **[reproduced]** — `_astar_search(1, 4)` on a graph where node 4 is disconnected returned `[1, 4]`. Any user whose destination is in an un-indexed area hits this.
- **Minimal safe fix:** Raise `ValueError` (→ HTTP 400) when the open set is exhausted instead of returning the fabricated path.

### C5. `safety_weight` API parameter is read but never used **[reproduced]**
- **File/Line:** `app/services/routing.py:481-482` (read); no further references
- **Root cause:** `safety_weight` is defaulted (line 482) and logged (line 496), but never passed to `_astar_search` or any cost computation. The two searches always run with hardcoded `weight_mode='fast'` and `weight_mode='safe'`.
- **Runtime impact:** Clients can set `safety_weight` anywhere in `[0,1]` and the response is bit-for-bit identical. The API contract implies a safety/distance trade-off knob that does nothing.
- **Reachability:** **[reproduced]** — grep of `find_safest_route` source shows `safety_weight` only at the signature, default, and log line.
- **Minimal safe fix:** Either remove the parameter from the contract (breaking change, out of scope) or wire it into the A* weight-mode/cost blend.

---

## HIGH — safety/risk computations that do not execute as designed

### H1. Traffic congestion cost branch is dead code — `congestion_ratio > 1.0` is never true **[reproduced]**
- **File/Line:** `app/graph/cost_engine.py:717-724` (`_calculate_traffic_cost`)
- **Root cause:** The single-edge traffic path builds `flow_data['congestion_ratio']` from `flow.congestion_ratio` (line 314), which is the model **property** `min(1.0, speed_kmh / free_flow_speed_kmh)` (`app/db/models.py:420-424`) — always `≤ 1.0`. The cost function only adds a congestion penalty when `congestion_ratio > 1.0` (line 718). The branch can never fire.
- **Runtime impact:** Congestion from the traffic-flow data contributes **zero** to edge cost in routing. Traffic cost comes only from `jam_factor` and `delay_seconds` branches. For a flow row with speed 10 km/h vs free-flow 60 km/h (severe congestion, ratio 0.167), the computed traffic cost was `0.0`.
- **Reachability:** **[reproduced]** with a congested `TrafficFlow` row. Reachable whenever traffic flow data exists.
- **Minimal safe fix:** Decide the intended unit once. If `>1.0` means congestion, compute `congestion_ratio = free_flow/current` here (as the batch path already does); if `≤1.0` means congestion (speed ratio), invert the branch. Pick one and align `_get_edge_traffic_data`, `_get_batch_traffic_data`, and the model property.

### H2. Single-edge vs batch traffic cost semantics diverge — same edge gets different traffic cost depending on code path **[reproduced in Phase 7]**
- **File/Line:** `app/graph/cost_engine.py:314` (single: `flow.congestion_ratio`, clamped `speed/free_flow`) vs `app/graph/cost_engine.py:406` (batch: `free_flow/speed`, unclamped, inverted)
- **Root cause:** The two traffic-data builders compute `congestion_ratio` with **opposite** formulas. Phase 7 measured a real edge at 3.667 traffic_cost via single-path vs 4.778 via batch path.
- **Runtime impact:** If any caller switches to `compute_batch_edge_costs`, every congested edge's cost changes and the H1 dead-branch would suddenly fire. The API currently routes via single-path, so this is latent — but it is a genuine cross-path inconsistency that will bite the moment the batch path is adopted.
- **Reachability:** Batch path not currently used by routing. **[static]** — documented, not triggered.
- **Minimal safe fix:** Unify on one formula (see H1).

### H3. `/ai/safety-score` returns a location-independent constant — the AI score ignores the coordinates **[reproduced]**
- **File/Line:** `ml/feature_engineering.py:385-440` (`engineer_features`) → used by `ml/safety_model.py:337-359` (`predict_safety_score`)
- **Root cause:** `engineer_features` is a stub: it **never queries the database** and returns a fixed neutral feature vector (all `0.5`, line 406-440). The real implementation `extract_features_for_edge` (line 137) exists but is **never called** anywhere.
- **Runtime impact:** `predict_safety_score(28.6, 77.2)` and `predict_safety_score(0, 0)` return the same value (~0.817) because the model predicts on an all-0.5 input. The `latitude`/`longitude`/`radius` query params and the `db` dependency are effectively decorative. A user-facing "AI-predicted safety score for this location" is a constant.
- **Reachability:** **[reproduced]** — `predict_safety_score` returned `0.817140...` regardless of coordinates; `engineer_features` shown not to touch `db`.
- **Minimal safe fix:** Call `extract_features_for_edge` (after fixing its bugs, see M3) on the nearest `GraphEdge`, or at minimum remove the claim that it is location-aware.

### H4. `predict_safety_score` returns a neutral 0.5 on *any* exception — errors hide behind a plausible number **[static]**
- **File/Line:** `ml/safety_model.py:362-365`
- **Root cause:** The whole body is wrapped in `try/except Exception: return 0.5`. Any model-load failure, DB error, or feature bug silently yields "moderately safe".
- **Runtime impact:** The API endpoint (`app/api/v1/ai.py:45-51`) forwards this as a success (200, `"success": True`). An operator cannot distinguish "model down" from "model says safe". Combined with H3, the endpoint is a constant anyway.
- **Reachability:** **[static]** — reachable on any exception in the feature/predict path.
- **Minimal safe fix:** At least log at error level (already does) and surface a non-200 on model availability failures instead of a neutral score.

### H5. Cost configuration silently falls back to defaults — cost tuning is impossible and `COST_PROFILES` is dead code **[reproduced]**
- **File/Line:** `app/graph/cost_config.py:81-102` (`load_cost_config_from_app`); `app/graph/cost_config.py:140-190` (`COST_PROFILES`, `get_cost_profile`)
- **Root cause:** `settings` has **no** `COST_WEIGHT_CONFIG` attribute (verified: `hasattr(settings, 'COST_WEIGHT_CONFIG') == False`), so the `hasattr` check at line 90 is always false and the function returns `CostWeightConfig()` defaults. The `except Exception: pass` at 97-99 would also swallow any parsing error silently. `COST_PROFILES` / `get_cost_profile` are never imported or called anywhere.
- **Runtime impact:** The cost weights documented as tunable (risk_weight, traffic_weight, etc.) are always their class defaults. Operators cannot steer routing via config. Not a crash, but the configuration surface is inert.
- **Reachability:** **[reproduced]** — `load_cost_config_from_app()` returned defaults.
- **Minimal safe fix:** Either expose `COST_WEIGHT_CONFIG` on `Settings` (pydantic extra="ignore" currently discards it) or load the config file path explicitly; log which config was used.

---

## MEDIUM — silent exception swallows

### M1. Bare `except:` swallows malformed JSON on closures/construction — a bad row silently disables closure routing for those edges **[reproduced]**
- **File/Line:** `app/graph/cost_engine.py:263-268` (closures), `287-298` (construction); same pattern in batch path at `476-477`, `505-506`
- **Root cause:** `json.loads(clo.affected_edges)` is wrapped in a bare `except: pass`. If any `RoadClosure.affected_edges` (or `ConstructionZone.affected_edges`) contains non-JSON (e.g. written by another tool, an OSM import glitch, a NULL/empty variant), the closure is silently dropped.
- **Runtime impact:** A road closure that should block/cost-penalize an edge is ignored → routes are sent through a closed road. Verified: closure with `affected_edges="[BAD JSON{"` produced an empty closures list with no error.
- **Reachability:** **[reproduced]**. Requires one malformed row in `road_closures` / `construction_zones`.
- **Minimal safe fix:** Log the offending `id` and `affected_edges` at warning level inside the `except` (and catch only `(ValueError, TypeError)`), or fall back to the proximity path that already exists for construction.

### M2. `_log_prediction` and `_check_drift` swallow exceptions silently, and the drift check fires on *every* request (log spam) **[reproduced]**
- **File/Line:** `ml/safety_model.py:142-143` (`_log_prediction`), `174-175` (`_check_drift`)
- **Root cause:** Both catch `Exception` and only `logger.warning`. Additionally, the model's `train_stats` were computed on a feature scale that makes live latitude/longitude produce extreme z-scores (observed `latitude z = -983`, `longitude z = -2720`), so `_check_drift` logs a "Potential data drift detected" warning on **every** prediction.
- **Runtime impact:** Every `/ai/safety-score` call emits a spurious drift warning → log noise drowns real signals. CSV prediction logging failures are invisible.
- **Reachability:** **[reproduced]** — the drift warning printed on a single prediction. Logging failures reachable whenever the log dir is unwritable.
- **Minimal safe fix:** Cap z-score warning to a sane threshold, or exclude coordinate features from drift monitoring (coordinates legitimately vary). Narrow the `except` clauses and log at error level for the CSV write.

### M3. `extract_features_for_edge` is dead code with a guaranteed TypeError — the one real feature extractor cannot run **[reproduced]**
- **File/Line:** `ml/feature_engineering.py:169-170`
- **Root cause:** `_get_degree_from_node` is defined as `_get_degree_from_node(session, node_id)` (line 81) but called as `_get_degree_from_node(edge.source_node_id)` (line 169) — the `session` arg is missing. Also `edge.source_node`/`edge.dest_node` (lines 216-218) reference relationships that don't exist on `GraphEdge`. Any call raises.
- **Runtime impact:** Currently **none** — the function is never called (H3 uses `engineer_features`). But it is the only implementation that would actually read risk data, and it is broken. Latent.
- **Reachability:** **[reproduced]** — calling it raised `TypeError`. Not reachable via the API today.
- **Minimal safe fix:** Pass `session` explicitly, add the missing relationships or query the nodes, and then wire it into H3's `engineer_features`.

### M4. `_get_edge_cost` / `_get_neighbors` swallow cost-engine errors and silently skip or distance-fallback edges **[static]**
- **File/Line:** `app/services/routing.py:111-122` (`_get_edge_cost` `except Exception`), `168-183` (two `except Exception` per-edge skip blocks in `_get_neighbors`)
- **Root cause:** Any exception from `RouteCostEngine.compute_edge_cost` is caught; `_get_edge_cost` falls back to `float(edge.length)`, `_get_neighbors` drops the edge from the graph entirely.
- **Runtime impact:** A transient error on one edge makes routing either ignore it (potential detour / disconnected graph) or treat it as distance-only (ignoring risk/traffic). Errors are logged at `warning`, so not fully silent, but the **behavior change** (skip edge) is not surfaced to the caller.
- **Reachability:** **[static]** — reachable on any cost-engine exception (e.g. a `GraphEdge` whose row was deleted between queries).
- **Minimal safe fix:** Continue, but log at error level with `exc_info`, and (for `_get_edge_cost`) only fall back for known-safe error types rather than all `Exception`.

### M5. `general_exception_handler` exists twice; the registered one leaks the exception string but the duplicate is dead code **[static]**
- **File/Line:** `app/api/exceptions.py:34-40` (registered) vs `app/api/responses.py:89-105` (unused); registration at `app/main.py:67`
- **Root cause:** Two identical handlers exist; only `app.api.exceptions` is imported/registered. The `responses.py` copy is dead. The registered handler returns a generic 500 (fine) but the endpoint handlers in `routing.py`/`ai.py` already catch broad exceptions and return their own JSON, so the global handler rarely runs.
- **Runtime impact:** Cosmetic duplication; not a runtime failure. Noted for hygiene, not severity.
- **Reachability:** **[static]**
- **Minimal safe fix:** Delete the dead duplicate.

---

## LOW / informational

### L1. `APIException` is never raised or handled — `error_code` is dropped when it would be used **[static]**
- **File/Line:** `app/exceptions.py:6-16`
- **Root cause:** `APIException` subclasses `HTTPException` but no code raises it, and the registered `http_exception_handler` (`app/api/exceptions.py:10-19`) reads `exc.detail`/`exc.status_code` and ignores `exc.error_code`.
- **Runtime impact:** If any future code raises `APIException`, the `error_code` won't surface. Inert today.
- **Minimal safe fix:** Extend the handler to read `getattr(exc, 'error_code', None)`.

### L2. `RouteResponse` schema is never used — the route endpoint returns an untyped dict **[static]**
- **File/Line:** `app/schemas/routing.py:24-31`; `app/api/v1/routing.py:58-70`
- **Root cause:** The endpoint builds a plain dict from `result[...]`, never constructing `RouteResponse`. FastAPI's response model is not set, so no response validation/serialization is applied and OpenAPI won't document the shape.
- **Runtime impact:** No runtime failure; API docs are inaccurate.
- **Minimal safe fix:** Add `response_model=RouteResponse` (requires the returned dict to conform exactly — it already does).

### L3. `validation_exception_handler` is imported but never registered — the custom 422 handler is dead **[static]**
- **File/Line:** `app/main.py:39` (import), `app/main.py:66-68` (only `Exception` and `HTTPException` registered)
- **Root cause:** `validation_exception_handler` (422) is never added via `app.add_exception_handler`.
- **Runtime impact:** Request validation errors use FastAPI's default 422 shape instead of the standardized envelope. Inconsistent API contract.
- **Minimal safe fix:** Register it: `app.add_exception_handler(RequestValidationError, validation_exception_handler)`.

### L4. `/metrics` swallows errors and returns `{"error": ...}` with 200 **[static]**
- **File/Line:** `app/main.py:147-151`
- **Root cause:** `except Exception` returns a 200 dict with an `error` field.
- **Runtime impact:** Monitoring probes treat a 200 as healthy even when psutil fails. Minor.
- **Minimal safe fix:** Return 500 or a structured error envelope.

---

## Summary table

| ID | File:Line | Class | Reachable? | Verified |
|----|-----------|-------|-----------|----------|
| C1 | routing.py:437-459 | NameError → safe route ignores risk | Always (safe A*) | reproduced |
| C2 | routing.py:390-399 | safe/fast modes inverted in effect | Always | derived from C1 |
| C3 | routing.py:268-283 | safety score always 0.8 | Always | static |
| C4 | routing.py:403-408 | bogus straight-line fallback route | Unreachable dest | reproduced |
| C5 | routing.py:481-482 | `safety_weight` param inert | Always | reproduced |
| H1 | cost_engine.py:717-724 | congestion branch dead code | Traffic data present | reproduced |
| H2 | cost_engine.py:314 vs 406 | batch/single traffic semantics diverge | Batch path unused | Phase-7 measured |
| H3 | feature_engineering.py:385-440 | AI score is a constant | Always | reproduced |
| H4 | safety_model.py:362-365 | errors → neutral 0.5 | Exception path | static |
| H5 | cost_config.py:81-102 | cost config inert; profiles dead | Always | reproduced |
| M1 | cost_engine.py:263-298 | malformed JSON silently drops closure | Bad row present | reproduced |
| M2 | safety_model.py:142-175 | drift log spam; log writes invisible | Always | reproduced |
| M3 | feature_engineering.py:169-218 | real feature extractor TypeErrors | Never called | reproduced |
| M4 | routing.py:111-183 | edges skipped / distance-fallback on error | Cost-engine exception | static |
| M5 | responses.py:89-105 | dead duplicate handler | Never | static |
| L1-L4 | — | hygiene / inert code | Never | static |

**Top 5 to fix first (all minimal, none require algorithm changes):**
1. **C1** — one-line import (`RoadSegmentRisk`) restores risk-aware safe routing.
2. **C4** — raise instead of fabricating a straight-line route.
3. **H1** — unify congestion-ratio units so the congestion branch can fire.
4. **M3 + H3** — fix `extract_features_for_edge` and call it so the AI score is real.
5. **M1** — log the malformed closure/construction rows instead of `pass`.

No code was modified during this audit.
