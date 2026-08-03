# RC8.12 Government Command Center & Smart City Platform

## Overview

RC8.12 adds a Government Command Center & Smart City platform on top of the
existing SafeRoute infrastructure. It provides city/district/state dashboards,
incident/crime/traffic analytics, emergency monitoring, heatmaps, zone
monitoring, live city metrics, resource utilization, agency/command-center/user
management, audit logging, and evidence-backed executive reports — while
**reusing** the existing Traffic, Prediction, Emergency, Fleet, AI Copilot,
Routing, WebSocket, Redis, and Celery engines. No existing engine is duplicated
or rewritten.

All analytics are **evidence-backed**: every number in a summary or report comes
from a reused engine query. No hallucinated statistics.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        RC8.12 ARCHITECTURE                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐   ┌──────────────────────┐   ┌─────────────────────┐    │
│  │  REST API    │   │  GovernmentService   │   │  WebSocket Events   │    │
│  │ /government  │──▶│  (RC8.12 orchestrator)│──▶│  government.*        │    │
│  └──────────────┘   └──────────┬───────────┘   └─────────────────────┘    │
│                                │                                          │
│                                ▼                                          │
│                      ┌──────────────────────┐                             │
│                      │ REUSED ENGINES        │                             │
│                      │  Traffic (RC8.1)      │  traffic_analytics         │
│                      │  Prediction (RC8.7)   │  city risk, future          │
│                      │                       │  congestion/crime/accident  │
│                      │  Emergency (RC8.11)   │  incident analytics,        │
│                      │                       │  monitoring, heatmap src    │
│                      │  Fleet (RC8.10)       │  resource utilization       │
│                      │  AI Copilot (RC8.3)   │  executive/district/city    │
│                      │                       │  summaries                  │
│                      │  Routing (RC8.4)      │  reference data             │
│                      └──────────┬───────────┘                             │
│                                 │                                          │
│                                 ▼                                          │
│                      ┌──────────────────────┐   ┌─────────────────────┐   │
│                      │  Celery tasks        │   │  Redis Pub/Sub       │   │
│                      │  (government queue)  │   │  saferoute:ws:events │   │
│                      └──────────────────────┘   └─────────────────────┘   │
│                                                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model (Part 1)

Ten new tables (created only because they did not exist):

| Table | Purpose |
|-------|---------|
| `government_agencies` | Agencies (police/fire/medical/municipal/transport), jurisdiction level, parent-child hierarchy. |
| `government_command_centers` | Physical/operational command centers owned by an agency. |
| `government_city_zones` | Geographic zones (ward, police zone, precinct, coverage area) within a city/district. |
| `government_live_metrics` | Time-series city metric snapshots (traffic index, incident count, risk index, safety score, …). |
| `government_incident_analytics` | Aggregated incident analytics snapshots per city/zone/period. |
| `government_emergency_heatmaps` | Persisted heatmap grids (risk/incident/crime/traffic/accident/emergency). |
| `government_traffic_analytics` | Aggregated traffic analytics snapshots. |
| `government_safety_analytics` | Aggregated safety analytics snapshots. |
| `government_agency_users` | Agency user accounts (links RC8.9 user identities). |
| `government_audit_logs` | Append-only audit trail for government actions. |

**Enums added:** `AgencyType`, `AgencyLevel`, `AgencyStatus`,
`CommandCenterStatus`, `CityZoneType`, `MetricType`, `AnalyticsPeriod`,
`HeatmapType`, `AgencyUserRole`.

**Migration:** `alembic/versions/add_government_management_tables.py`
(revision `add_government_management_tables`, down-revision
`add_emergency_management_tables`). Single Alembic head maintained.

---

## Service (Part 2)

`app/services/government_service.py` — `GovernmentService`:

- **Agency / command-center / city-zone / agency-user CRUD** with audit logging.
- **Live city metrics**: record + list + latest-per-type, published as WebSocket events.
- **City/district/state dashboards**: aggregate all reused-engine analytics.
- **Analytics**: `traffic_analytics` (Traffic engine snapshots per zone),
  `safety_analytics` (Prediction risk), `incident_analytics` (Emergency engine
  analytics), `crime_analytics` (Prediction `crime` threat).
- **Emergency monitoring** (reuses `EmergencyService.get_emergency_dashboard`)
  and **resource utilization** (reuses Fleet vehicles + Emergency responders).
- **Heatmaps**: grid sampled from the Prediction engine (risk/accident/crime)
  or the Emergency engine (incident/emergency) or Traffic engine (traffic).
- **Evidence-backed executive/city/district summaries** and recommended actions
  derived from actual analytics values (Part 7).
- **Reports**: hourly/daily/weekly/monthly structured reports.

**Engine reuse accessors** are lazy properties: `traffic`, `prediction`,
`emergency`, `fleet`, `ai_copilot`, `routing`.

---

## REST APIs (Part 3)

Router `app/api/v1/government.py`, prefix `/api/v1/government`, tag `government`.
27 paths:

- **Agencies**: `POST/GET /agencies`, `GET/PUT /agencies/{id}`.
- **Command centers**: `POST/GET /command-centers`.
- **Zones**: `POST/GET /zones`, `GET /zones/{id}`.
- **Agency users**: `POST/GET /agency-users`.
- **Dashboards**: `GET /dashboard/city`, `/dashboard/district`, `/dashboard/state`.
- **Analytics**: `GET /analytics/traffic`, `/analytics/safety`,
  `/analytics/incidents`, `/analytics/crime`.
- **Live metrics**: `POST /metrics`, `GET /metrics`, `GET /metrics/latest`.
- **Heatmaps**: `POST /heatmaps/generate`, `GET /heatmaps`.
- **Monitoring/resources**: `GET /emergency-monitoring`, `GET /resources`.
- **Prediction**: `GET /prediction/city`, `/prediction/congestion`.
- **Copilot**: `GET /copilot/executive-summary`, `/copilot/city-summary`,
  `/copilot/district-summary`, `/copilot/incident-summary`.
- **Reports**: `GET /reports/generate`.
- **Audit**: `GET /audit-logs`.

All responses follow the shared `success_response` / `error_response` helpers.

---

## WebSocket Events (Part 4)

New `EventType` members in `app/schemas/realtime.py` (published through the
existing `RedisPubSub` broadcast path):

| Event | Value |
|-------|-------|
| `GOVERNMENT_METRIC_UPDATED` | `government.metric.updated` |
| `GOVERNMENT_ALERT` | `government.alert` |
| `GOVERNMENT_DASHBOARD_REFRESH` | `government.dashboard.refresh` |
| `GOVERNMENT_HEATMAP_UPDATED` | `government.heatmap.updated` |
| `GOVERNMENT_RESOURCE_CHANGED` | `government.resource.changed` |
| `GOVERNMENT_INCIDENT_SUMMARY` | `government.incident.summary` |

New `SubscriptionTopic` members enable wildcard subscriptions:
`government.*`, `government.dashboards`, `government.metrics`,
`government.heatmaps`, `government.alerts`, `government.incidents`.

---

## Celery Tasks (Part 5)

`app/tasks/government_tasks.py` — registered with the existing Celery app,
routed to the **`government`** queue. Tasks:

| Task | Schedule | Purpose |
|------|----------|---------|
| `refresh_government_dashboards` | 5 min | Recompute city dashboards; record derived live metrics. |
| `aggregate_government_analytics` | 30 min | Persist traffic/safety/incident analytics snapshots. |
| `generate_government_heatmaps` | 1 h | Regenerate risk + incident heatmaps per city. |
| `generate_government_report` | hourly / daily / weekly / monthly | Generate structured reports (`report_type` arg). |
| `cleanup_government_data` | 12 h | Purge stale metrics/analytics beyond retention. |

All tasks delegate to `GovernmentService` — no business logic is duplicated in
the workers. Beat schedule: 8 entries (the report task has 4 cadence entries
with `args`).

---

## Prediction Integration (Part 6)

The existing **Prediction engine** (`ml.prediction.PredictionService`) drives:

- **District/city risk** — `city_prediction_summary` averages hazard
  probabilities across the city's zones (per-threat: accident, congestion,
  crime, weather hazard, flooding, construction, road closure).
- **Future congestion** — `future_congestion` forecasts congestion probability
  per zone over the requested horizon.
- **Crime risk** — `crime_analytics` reads the `crime` threat per zone.
- **Safety analytics** — `safety_analytics` converts average risk to a 0-100
  safety score.
- **Heatmaps** — risk/accident/crime heatmap cells sample the Prediction engine.

Untrained models return default probabilities gracefully (documented path).

---

## AI Copilot Integration (Part 7)

The existing **AI Copilot** (`AICopilotService`) plus evidence-backed narratives:

- **Executive / city summary** — narrative composed from actual analytics values
  (traffic index, safety score, incident completion rate, active incidents,
  resource ratios) with **recommended actions derived from evidence** (e.g.,
  "deploy traffic units" only when congestion is HIGH). No invented statistics.
- **District summary** — aggregates per-city dashboards.
- **Incident summary** — reuses the RC8.11 `EmergencyService.get_incident_copilot`
  narrative (`why_responder_selected`, `risk_summary`, `recommended_actions`,
  `confidence`); falls back to a region-level factual summary when no incident
  context is available.

---

## Verification (Part 9)

Executed alongside this document:

- Repository boots; FastAPI imports cleanly; OpenAPI generated.
- Alembic upgrades to a single head; `add_government_management_tables` applied.
- All 10 government tables created with indexes.
- Celery app imports; all 5 government tasks registered on the `government`
  queue; 8 beat entries present (incl. hourly/daily/weekly/monthly reports).
- WebSocket events + subscription topics registered (6 events, 6 topics).
- Service unit smoke tests (agency/zone/metric/analytics/heatmap/report/audit).
- Live API smoke tests: all 27 government paths returned 200.
- Prediction integration returns real per-threat probabilities.
- AI Copilot executive/city/district/incident summaries verified.

**Result:** PASS (see the RC8.12 final report in `CONTEXT.md`).
