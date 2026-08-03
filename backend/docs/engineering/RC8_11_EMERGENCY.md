# RC8.11 Emergency Dispatch & Incident Command Platform

## Overview

RC8.11 adds an Emergency Dispatch & Incident Command platform on top of the
existing SafeRoute infrastructure. It provides incident reporting, responder
and vehicle dispatch, live ETA, automatic rerouting, command-center operations,
emergency zones, timelines, dashboards, and analytics — while **reusing** the
existing Routing, Prediction, AI Copilot, Traffic, Fleet, Personal Driver, ETA,
WebSocket, Redis, and Celery engines. No existing engine is duplicated or
rewritten.

The platform reuses the existing **RC8.1 CAD `emergency_vehicles` table** for
dispatch vehicles (the `EmergencyVehicle` model already existed).

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         RC8.11 ARCHITECTURE                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐   ┌──────────────────────┐   ┌─────────────────────┐    │
│  │  REST API    │   │  EmergencyService    │   │  WebSocket Events   │    │
│  │  /emergency  │──▶│  (RC8.11 orchestrator)│──▶│  incident.*          │    │
│  └──────────────┘   └──────────┬───────────┘   │  dispatch.*          │    │
│                                │               │  responder.location  │    │
│                                │               │  command.alert       │    │
│                                ▼               └──────────┬──────────┘    │
│                      ┌──────────────────────┐              │              │
│                      │ REUSED ENGINES        │              │              │
│                      │  Routing (RC8.4)      │              │              │
│                      │  Live ETA (RC8.4)     │              │              │
│                      │  Prediction (RC8.7)   │              │              │
│                      │  AI Copilot (RC8.3)   │              │              │
│                      │  Traffic (RC8.1)      │              │              │
│                      │  Fleet (RC8.10)       │              │              │
│                      │  Personal Driver(8.9) │              │              │
│                      └──────────┬───────────┘              │              │
│                                 │                          │              │
│                                 ▼                          ▼              │
│                      ┌──────────────────────┐   ┌─────────────────────┐   │
│                      │  Celery tasks        │   │  Redis Pub/Sub       │   │
│                      │  (emergency queue)   │   │  saferoute:ws:events  │   │
│                      └──────────────────────┘   └─────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model (Part 1)

Seven new tables (the eighth required table, `emergency_vehicles`, already
exists from RC8.1 and is reused):

| Table | Purpose |
|-------|---------|
| `emergency_incidents` | Incident lifecycle (type/severity/priority/status, location, casualties). `severity` reuses RC8.1 `IncidentSeverity`. |
| `emergency_responders` | Responders (badge/ref, role, agency, live location, availability score, RC8.9 user link). |
| `emergency_dispatches` | Dispatch records (ref, strategy, requested/accepted units, details JSON). |
| `emergency_assignments` | Responder↔incident assignments with route/ETA snapshots from the reused engines. |
| `emergency_commands` | Command posts (commander, type/status/phase, briefing, decisions). |
| `emergency_zones` | Cordon/triage/staging/evacuation zones (center + radius / polygon). |
| `emergency_logs` | Full incident timeline (actor, action, message, severity). |

**Enums added:** `EmergencyIncidentType`, `IncidentPriority`, `IncidentStatus`,
`ResponderRole`, `ResponderStatus`, `DispatchStatus`,
`EmergencyAssignmentStatus`, `CommandType`, `CommandStatus`, `CommandPhase`,
`ZoneType`, `ZoneStatus`, `EmergencyLogSeverity`. `IncidentSeverity` is reused.

**Migration:** `alembic/versions/add_emergency_management_tables.py`
(revision `add_emergency_management_tables`, down-revision
`add_traffic_prediction_probability_columns`). Single Alembic head maintained.

---

## Service (Part 2)

`app/services/emergency_service.py` — `EmergencyService`:

- **Incident lifecycle**: create, list, get, update, status transitions, priority
  escalation, close; timeline via `EmergencyLog`.
- **Dispatch**: `dispatch_to_incident` picks the nearest available responders
  (`find_nearest_responders`) or explicit responder IDs, creates one
  `EmergencyAssignment` per unit, plans the route with the **reused routing
  engine**, computes a **live ETA with the reused Live ETA engine**, and persists
  the route/ETA snapshot.
- **Nearest responder**: blends haversine distance, availability score, and
  **Personal Driver fatigue** (RC8.9) — plus a **Prediction hazard signal**
  (Part 6).
- **Vehicle recommendation**: `recommend_vehicles` ranks available RC8.1 CAD
  vehicles using distance + **Prediction risk at the vehicle's location**.
- **Automatic rerouting**: when the live ETA exceeds base ETA by a threshold,
  recompute the safest route (reused engine) and regenerate a route narrative
  via **AI Copilot** (Part 7).
- **Command center**: command posts, zones, dashboards, analytics.

**Engine reuse accessors** are lazy properties: `routing`, `eta`, `traffic`,
`prediction`, `personal_driver`, `ai_copilot`, `fleet`.

---

## REST APIs (Part 3)

Router `app/api/v1/emergency.py`, prefix `/api/v1/emergency`, tag `emergency`.
~38 paths:

- **Incidents**: `POST /incidents`, `GET /incidents`, `GET/PUT
  /incidents/{id}`, `POST /incidents/{id}/status`, `/escalate`, `/close`,
  `/logs`, `GET /incidents/{id}/timeline`, `GET /incidents/{id}/copilot`.
- **Dispatch**: `POST /dispatch`, `GET /dispatches`, `GET /dispatches/{id}`.
- **Assignments**: `GET /assignments`, `POST /assignments/{id}/status`,
  `GET /assignments/{id}/eta`, `POST /assignments/{id}/reroute`.
- **Responders**: `POST/GET /responders`, `GET /responders/nearest`,
  `GET/PUT /responders/{id}`, `POST /responders/{id}/location`, `/status`.
- **Vehicles**: `GET /vehicles/recommend`.
- **Commands**: `POST/GET /commands`, `GET/PUT /commands/{id}`,
  `POST /commands/{id}/close`.
- **Zones**: `POST/GET /zones`, `GET/PUT /zones/{id}`, `POST /zones/{id}/clear`.
- **Dashboard / Analytics**: `GET /dashboard`, `GET /analytics`.

All responses follow the shared `success_response` / `error_response` helpers.

**Route-order note:** `GET /responders/nearest` is declared before
`GET /responders/{responder_id}` so FastAPI matches the static path first.

---

## WebSocket Events (Part 4)

New `EventType` members in `app/schemas/realtime.py` (published through the
existing `RedisPubSub` broadcast path, channel
`saferoute:ws:events:broadcast`):

| Event | Value |
|-------|-------|
| `EMERGENCY_INCIDENT_CREATED` | `incident.created` |
| `EMERGENCY_INCIDENT_UPDATED` | `incident.updated` |
| `EMERGENCY_INCIDENT_CLOSED` | `incident.closed` |
| `EMERGENCY_DISPATCH_STARTED` | `dispatch.started` |
| `EMERGENCY_DISPATCH_COMPLETED` | `dispatch.completed` |
| `EMERGENCY_RESPONDER_LOCATION` | `responder.location` |
| `EMERGENCY_COMMAND_ALERT` | `command.alert` |

New `SubscriptionTopic` members enable wildcard subscriptions: `emergency.*`,
`emergency.incidents`, `emergency.dispatches`, `emergency.responders`,
`emergency.commands`.

---

## Celery Tasks (Part 5)

`app/tasks/emergency_tasks.py` — registered with the existing Celery app
(`app/tasks/celery_app.py`), routed to the **`emergency`** queue. Tasks:

| Task | Schedule | Purpose |
|------|----------|---------|
| `monitor_emergency_incidents` | 60s | Refresh assignment ETAs, run automatic-reroute checks for open incidents. |
| `optimize_dispatch` | 60s | Dispatch hazard-scaled units to REPORTED/DISPATCHING incidents with no assignments. |
| `refresh_emergency_etas` | 60s | Recompute live ETA for all in-flight assignments. |
| `track_responder_heartbeats` | 30s | Mark responders UNAVAILABLE when their location heartbeat is stale. |
| `aggregate_emergency_analytics` | 30m | Compute and cache emergency analytics. |
| `cleanup_emergency_data` | 6h | Close stale command posts, purge old closed-incident logs. |

All tasks delegate to `EmergencyService` — no business logic is duplicated in
the workers.

---

## Prediction Integration (Part 6)

The existing **Prediction engine** (`ml.prediction.PredictionService`)
influences:

- **Dispatch order** — `find_nearest_responders` scores responders with a
  hazard signal at the responder's current location (breaks ties between
  equidistant units).
- **ETA** — `_prediction_adjusted_eta` blends the engine ETA with hazard
  probability at the incident location (up to +50% at max hazard). The
  prediction-aware ETA is persisted as `live_eta_seconds`; the raw engine value
  stays in the refresh result (`eta_seconds` / `adjusted_eta_seconds`).
- **Reroute threshold** — `automatic_reroute` compares against the
  hazard-adjusted ETA, so high-hazard incidents reroute sooner.
- **Resource allocation** — `_recommended_units` returns 1 base unit, +1 for
  CRITICAL severity or URGENT priority, +1 in high-hazard zones. Used whenever
  a dispatch does not specify a unit count (Celery `optimize_dispatch`, and the
  API when `requested_units` is omitted).

---

## AI Copilot Integration (Part 7)

The existing **AI Copilot** (`app.services.ai_copilot.AICopilotService`)
explains:

- **Why a responder was selected** — from the assignment's route/ETA/availability
  snapshot (in each dispatch's `copilot_narrative`).
- **Incident summary** — type, severity, priority, status, casualties, injuries.
- **Risk summary** — safety score/grade, hazards avoided, key factors from the
  route explanation.
- **Recommended actions** — Copilot recommendations serialized per assignment.
- **Why rerouted** — `automatic_reroute` already attached a Copilot narrative;
  retained and returned with the reroute result.

Accessible via `GET /api/v1/emergency/incidents/{id}/copilot`.

### Latent bug fixed
`AICopilotService.explain_route` returned `CopilotResponse(**cached)` on cache
hits, leaving nested dataclasses (`explanation`, `comparison`, `recommendations`,
`confidence`) as plain dicts. Any consumer doing attribute access
(`copilot.explanation.explanation`) failed on a warm cache (this also affected
the existing `/api/v1/copilot/explain` endpoint). Added a recursive
`_rebuild_dataclass` helper that reconstructs nested dataclasses from the cached
plain dicts. Cold and warm-cache paths now behave identically.

---

## Verification (Part 9)

Executed in `docs/engineering/RC8_11_EMERGENCY.md` companion verification runs:

- Repository boots; FastAPI imports cleanly; OpenAPI generated.
- Alembic upgrades to a single head; `add_emergency_management_tables` applied.
- Celery app imports; all 6 emergency tasks registered on the `emergency` queue;
  6 beat-schedule entries present.
- WebSocket events + subscription topics registered.
- Routing, Prediction, AI Copilot, Traffic, Fleet, Personal Driver, Offline
  engines still import and their API paths remain registered.
- Emergency + dispatch API live smoke tests passed (create → dispatch →
  ETA refresh → reroute → timeline → analytics).
- All emergency test rows cleaned up after verification.

**Result:** PASS (see the RC8.11 final report in `CONTEXT.md`).
