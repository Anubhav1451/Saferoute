# RC8.4 Dynamic Routing & Live ETA Engine - Implementation Plan

## Overview
Build a comprehensive Dynamic Routing & Live ETA Engine on top of RC8.0-8.3 infrastructure:
- RC8.0: PostgreSQL/PostGIS, Redis Cache, Celery Workers
- RC8.1: GIS Routing (Graph, Spatial Index, A* Routing, Cost Engine)
- RC8.2: WebSocket Real-Time Events, Redis Pub/Sub, Celery Tasks
- RC8.3: AI Copilot Service, Narrative Generation, Route Comparison, Recommendations

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RC8.4 ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌─────────────────┐     ┌────────────────────────┐   │
│  │  Route       │     │  Live ETA       │     │  Route Monitoring      │   │
│  │  Monitor     │────▶│  Engine         │────▶│  Service (Background)  │   │
│  │  Service     │     │  (Core)         │     │  (Celery Worker)       │   │
│  └──────────────┘     └────────┬────────┘     └───────────┬────────────┘   │
│                                │                             │              │
│                                ▼                             │              │
│                      ┌─────────────────┐                    │              │
│                      │  Traffic        │                    │              │
│                      │  Service        │                    │              │
│                      │ (RC8.1/RC8.1)   │                    │              │
│                      └────────┬────────┘                    │              │
│                               │                             │              │
│                               ▼                             ▼              │
│                      ┌─────────────────┐     ┌────────────────────────┐   │
│                      │  Redis Cache    │     │  WebSocket Connection  │   │
│                      │  (ETA Cache,    │     │  Manager (RC8.2)       │   │
│                      │   Route Cache)  │     │  + Redis Pub/Sub       │   │
│                      └─────────────────┘     └───────────┬────────────┘   │
│                                                        │              │
│                               ┌────────────────────────┘              │
│                               ▼                                       │
│                      ┌─────────────────┐                              │
│                      │  WebSocket      │                              │
│                      │  Events         │                              │
│                      │  - ETA_UPDATE   │                              │
│                      │  - TRAFFIC_ALERT│                              │
│                      │  - REROUTE_SUGG │                              │
│                      │  - ARRIVAL      │                              │
│                      └─────────────────┘                              │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Live ETA Engine (`app/services/eta_engine.py`)
**Core service for real-time ETA calculations**

**Inputs:**
- Route (list of GraphEdges from GIS routing)
- Current traffic flow (TrafficFlow)
- Active incidents (TrafficIncident)
- Active road closures (RoadClosure)
- Active construction zones (ConstructionZone)
- Weather hazards (WeatherHazard)
- Historical speed profiles (TrafficPrediction)
- Current time / time of day

**Algorithm:**
1. Get base travel time from route edges (GIS routing result)
2. Apply traffic flow penalties per edge (speed ratio)
3. Apply incident penalties (delay_minutes from incidents)
4. Apply closure penalties (detour estimation or infinite penalty)
5. Apply construction penalties (speed reduction)
6. Apply weather penalties (speed reduction %)
7. Apply historical profile adjustments (time-of-day patterns)
8. Apply safety buffer (configurable %)
9. Return LiveETA with breakdown and confidence

**Output:** `LiveETAResponse`
- `eta_seconds`: Total ETA in seconds
- `base_travel_time_seconds`: Base GIS route time
- `traffic_delay_seconds`: Traffic flow delays
- `incident_delay_seconds`: Incident delays
- `closure_delay_seconds`: Closure detour delays
- `construction_delay_seconds`: Construction delays
- `weather_delay_seconds`: Weather delays
- `historical_adjustment_seconds`: Historical pattern adjustment
- `safety_buffer_seconds`: Safety buffer
- `confidence`: 0.0-1.0 confidence score
- `breakdown`: Per-edge breakdown
- `expires_at`: Cache expiry timestamp

**Caching:** Redis with TTL 30 seconds (configurable: `ETA_CACHE_TTL`)

---

### 2. Dynamic Re-routing Detector (`app/services/reroute_detector.py`)
**Detects when active routes need re-routing**

**Triggers:**
- Congestion threshold exceeded (configurable: `REROUTE_CONGESTION_THRESHOLD` = 3 = heavy)
- Active road closure on route
- Critical incident on route (severity HIGH/CRITICAL)
- Severe weather hazard on route
- ETA deviation > threshold from original (configurable: `REROUTE_ETA_DEVIATION_PCT` = 25%)

**Algorithm:**
1. Subscribe to active route monitoring (WebSocket subscription or DB poll)
2. Periodically check route against live traffic data
3. Evaluate each trigger condition
4. If triggered, request alternate routes from Alternate Route Generator
4. Emit `REROUTE_SUGGESTED` WebSocket event
5. Track reroute suggestions to avoid spam (cooldown period)

**Output:** `RerouteTrigger` event with:
- Trigger type and severity
- Recommended alternate routes
- Original vs new ETA comparison
- Reasoning

---

### 3. Alternate Route Generator (`app/services/alternate_routes.py`)
**Generates multiple route alternatives**

**Route Profiles:**
1. **FASTEST** - Minimize time (traffic-aware)
2. **SAFEST** - Maximize safety score (existing GIS routing)
3. **BALANCED** - Weighted combination (configurable: `BALANCED_WEIGHT_TIME`, `BALANCED_WEIGHT_SAFETY`)
4. **ECO** - Minimize fuel/emissions (prefer steady speeds, avoid congestion)

**Algorithm:**
1. Get base route from GIS routing (safest + fastest)
2. For each profile, compute route with modified cost weights:
   - FASTEST: `time_weight=1.0, risk_weight=0.0, traffic_weight=1.5`
   - SAFEST: `time_weight=0.3, risk_weight=1.0, traffic_weight=0.5`
   - BALANCED: `time_weight=0.5, risk_weight=0.5, traffic_weight=1.0`
   - ECO: `time_weight=0.4, risk_weight=0.3, traffic_weight=1.2, eco_weight=1.0`
3. Apply traffic-aware cost modifications per edge
4. Deduplicate similar routes (similarity > 80% edges)
5. Return top 3 alternatives with LiveETA for each

**Caching:** Redis with TTL 2 minutes (configurable: `ALT_ROUTE_CACHE_TTL`)

---

### 4. Route Monitoring Service (`app/services/route_monitor.py`)
**Background service for monitoring active routes**

**Architecture:**
- Celery worker task (`route_monitoring` queue)
- Periodic task: every 30 seconds (configurable: `ROUTE_MONITOR_INTERVAL`)
- Manages active route subscriptions (WebSocket session → route mapping)
- Polls traffic data for subscribed routes
- Computes LiveETA for each
- Detects reroute triggers
- Emits WebSocket events

**Data Structures:**
```python
class ActiveRoute:
    route_id: str
    user_id: str
    websocket_session_id: str
    route_edges: List[int]      # GraphEdge IDs
    original_eta: int           # Original ETA seconds
    original_route: RouteResponse  # Full original route
    started_at: datetime
    last_eta_update: datetime
    reroute_cooldown_until: datetime
    subscription_topics: List[str]
```

**WebSocket Integration:**
- Subscribe to route monitoring via WebSocket topic: `route:{route_id}:monitor`
- Client sends `SUBSCRIBE` with route_id and route data
- Server acknowledges and starts monitoring
- Server pushes `ETA_UPDATE` every interval
- Server pushes `REROUTE_SUGGESTED` when triggered
- Server pushes `ARRIVAL_NOTIFICATION` when ETA < threshold

---

### 5. WebSocket Event Integration (`app/schemas/realtime.py` - extend)
**New Event Types for RC8.4:**

```python
class EventType(str, Enum):
    # ... existing ...
    # RC8.4 additions:
    ETA_UPDATE = "ETA_UPDATE"              # Live ETA update
    TRAFFIC_ALERT = "TRAFFIC_ALERT"        # Traffic incident on route
    REROUTE_SUGGESTED = "REROUTE_SUGGESTED" # Alternate route suggestion
    ARRIVAL_NOTIFICATION = "ARRIVAL_NOTIFICATION"  # ETA < threshold
    ROUTE_MONITORING_STARTED = "ROUTE_MONITORING_STARTED"
    ROUTE_MONITORING_STOPPED = "ROUTE_MONITORING_STOPPED"
```

**Payload Models:**
```python
class ETAUpdatePayload(BaseModel):
    route_id: str
    eta_seconds: int
    original_eta_seconds: int
    delay_seconds: int
    delay_minutes: int
    confidence: float
    breakdown: Dict[str, int]  # traffic_delay, incident_delay, etc.
    expires_at: datetime

class TrafficAlertPayload(BaseModel):
    route_id: str
    incident: TrafficIncidentSchema
    affected_edges: List[int]
    estimated_delay_minutes: int

class RerouteSuggestedPayload(BaseModel):
    route_id: str
    trigger: RerouteTrigger  # CONGESTION, CLOSURE, INCIDENT, WEATHER, ETA_DEVIATION
    trigger_severity: str
    original_eta: int
    alternatives: List[AlternateRoute]  # Each with profile, eta, safety_score, distance
    reasoning: str
    cooldown_seconds: int

class ArrivalNotificationPayload(BaseModel):
    route_id: str
    eta_seconds: int
    destination: Coordinate
```

---

### 6. Celery Tasks (`app/tasks/routing_tasks.py` - extend)
**New Periodic Tasks:**

```python
# Periodic ETA refresh for actively monitored routes
refresh_active_route_etas = 30s  # Every 30 seconds

# Traffic monitoring for active routes
monitor_route_traffic = 30s  # Every 30 seconds

# Prediction updates for route edges
update_route_predictions = 5min  # Every 5 minutes

# Route monitoring cleanup (expired routes)
cleanup_expired_routes = 5min

# Alternate route cache warming
warm_alternate_route_cache = 10min
```

**On-Demand Tasks:**
- `compute_live_eta(route_id, route_edges)` - Compute and cache ETA
- `generate_alternate_routes(route_id, profile)` - Generate and cache alternates
- `evaluate_reroute_triggers(route_id)` - Check if reroute needed
- `send_eta_update(route_id)` - Push WebSocket ETA update
- `send_reroute_suggestion(route_id, trigger)` - Push reroute WebSocket event

---

### 7. Redis Caching Strategy (`app/utils/cache.py` - extend buckets)
**Cache Keys:**
```
eta:{route_hash}:{timestamp_bucket}     → LiveETAResponse (TTL: 30s)
alt_routes:{route_hash}:{profile}       → AlternateRouteResponse (TTL: 120s)
route_traffic:{edge_id}:{timestamp}     → TrafficFlow (TTL: 60s)
route_incidents:{bbox}:{timestamp}      → List[TrafficIncident] (TTL: 60s)
```

**Cache Buckets (extend cache.py):**
- `eta_cache` - TTL 30s
- `alt_route_cache` - TTL 120s
- `route_traffic_cache` - TTL 60s

---

### 8. API Endpoints (`app/api/v1/routing.py` - extend)
**New Endpoints:**

```
POST /api/v1/routes/live-eta
    Request: LiveETARequest (route_id, route_edges, destination)
    Response: LiveETAResponse

POST /api/v1/routes/alternatives
    Request: AlternateRoutesRequest (origin, destination, profiles[])
    Response: AlternateRoutesResponse

POST /api/v1/routes/monitor/start
    Request: RouteMonitorStartRequest (route_id, route_data, destination)
    Response: RouteMonitorResponse

POST /api/v1/routes/monitor/stop
    Request: RouteMonitorStopRequest (route_id)
    Response: RouteMonitorResponse

GET /api/v1/routes/{route_id}/eta
    Response: LiveETAResponse

GET /api/v1/routes/{route_id}/alternatives
    Response: AlternateRoutesResponse
```

---

### 9. Configuration (`app/core/config.py` - extend)
```python
# RC8.4 Settings
ETA_CACHE_TTL: int = 30                    # seconds
ALT_ROUTE_CACHE_TTL: int = 120             # seconds
ROUTE_MONITOR_INTERVAL: int = 30           # seconds
REROUTE_CONGESTION_THRESHOLD: int = 3      # 0-4 congestion level
REROUTE_ETA_DEVIATION_PCT: float = 25.0    # percentage
REROUTE_COOLDOWN_SECONDS: int = 300        # 5 minutes
ARRIVAL_NOTIFICATION_THRESHOLD_SECONDS: int = 300  # 5 min
BALANCED_WEIGHT_TIME: float = 0.5
BALANCED_WEIGHT_SAFETY: float = 0.5
ECO_WEIGHT_ECO: float = 1.0
ROUTE_MONITOR_MAX_ROUTES: int = 1000       # Max concurrent monitored routes
ETA_CONFIDENCE_DECAY_PER_MIN: float = 0.05 # Confidence decay per minute
```

---

### 10. Database Models (extend `app/db/models.py`)
**New Models:**

```python
class ActiveRouteMonitor(Base):
    """Track actively monitored routes for WebSocket clients."""
    __tablename__ = "active_route_monitors"
    
    id = Column(Integer, primary_key=True)
    route_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True)
    websocket_session_id = Column(String(100), index=True)
    route_edges_json = Column(String)  # JSON array of edge IDs
    origin_lat = Column(Float)
    origin_lon = Column(Float)
    dest_lat = Column(Float)
    dest_lon = Column(Float)
    original_eta_seconds = Column(Integer)
    original_distance_m = Column(Float)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_eta_update = Column(DateTime)
    last_reroute_check = Column(DateTime)
    reroute_cooldown_until = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(String)

class RerouteHistory(Base):
    """History of reroute suggestions for analytics."""
    __tablename__ = "reroute_history"
    
    id = Column(Integer, primary_key=True)
    route_id = Column(String(100), index=True)
    trigger_type = Column(String(50))
    trigger_severity = Column(String(20))
    original_eta = Column(Integer)
    suggested_eta = Column(Integer)
    selected_alternative = Column(String(50))  # FASTEST/SAFEST/BALANCED/ECO
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### 11. Schemas (`app/schemas/routing.py` - extend)
```python
class LiveETARequest(BaseModel):
    route_id: str
    route_edges: List[int]  # GraphEdge IDs
    destination: Coordinate
    departure_time: Optional[datetime] = None

class LiveETAResponse(BaseModel):
    route_id: str
    eta_seconds: int
    base_travel_time_seconds: int
    traffic_delay_seconds: int
    incident_delay_seconds: int
    closure_delay_seconds: int
    construction_delay_seconds: int
    weather_delay_seconds: int
    historical_adjustment_seconds: int
    safety_buffer_seconds: int
    confidence: float
    breakdown: Dict[str, Any]
    expires_at: datetime

class AlternateRouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate
    profiles: List[str] = ["FASTEST", "SAFEST", "BALANCED", "ECO"]
    avoid_highways: bool = False
    avoid_tolls: bool = False

class AlternateRouteResponse(BaseModel):
    routes: List[AlternateRoute]
    generated_at: datetime

class AlternateRoute(BaseModel):
    profile: str  # FASTEST, SAFEST, BALANCED, ECO
    route: RouteResponse  # From existing schema
    live_eta: LiveETAResponse
    safety_score: float
    distance_m: float
    estimated_fuel_l: Optional[float] = None
    co2_kg: Optional[float] = None

class RouteMonitorStartRequest(BaseModel):
    route_id: str
    route_edges: List[int]
    origin: Coordinate
    destination: Coordinate
    original_eta_seconds: int
    original_distance_m: float

class RouteMonitorStopRequest(BaseModel):
    route_id: str
```

---

### 12. Testing Strategy
**Unit Tests:**
- `test_eta_engine.py` - Live ETA calculations with mocked traffic data
- `test_reroute_detector.py` - Trigger detection logic
- `test_alternate_routes.py` - Route generation with different profiles
- `test_route_monitor.py` - Route monitoring service logic

**Integration Tests:**
- `test_routing_integration.py` - Full routing + ETA + alternatives flow
- `test_websocket_eta.py` - WebSocket ETA updates and reroute events
- `test_celery_routing_tasks.py` - Celery task execution

**Routing Regression Tests:**
- `test_routing_regression.py` - Verify RC8.1 routing still works
- Compare route results before/after RC8.4

**WebSocket Tests:**
- `test_websocket_eta_updates.py` - Subscribe, receive ETA updates
- `test_websocket_reroute.py` - Trigger reroute, receive suggestions
- `test_websocket_arrival.py` - Simulate arrival notification

---

### 13. Documentation
**Create:** `docs/engineering/RC8_4_DYNAMIC_ROUTING.md`
- Architecture diagram
- Component descriptions
- API documentation
- Configuration reference
- WebSocket event reference
- Celery task reference
- Caching strategy
- Performance considerations
- Testing guide

**Update:** `CONTEXT.md` with RC8.4 status

---

## Implementation Order

1. **Database Models** - Add `ActiveRouteMonitor` and `RerouteHistory`
2. **Schemas** - Extend `routing.py` and `realtime.py`
3. **Configuration** - Add RC8.4 settings to `config.py`
4. **Cache** - Add cache buckets to `cache.py`
5. **Core Services** - `eta_engine.py`, `reroute_detector.py`, `alternate_routes.py`
6. **Route Monitor** - `route_monitor.py` (background service)
7. **Celery Tasks** - Extend `routing_tasks.py`
8. **API Endpoints** - Extend `routing.py`
9. **WebSocket Integration** - Event publishing in services
10. **Tests** - Unit, integration, regression, WebSocket
11. **Documentation** - RC8_4_DYNAMIC_ROUTING.md + CONTEXT.md

---

## Dependencies (No New External Deps)
All built on existing RC8.0-8.3:
- `app.services.gis_routing_service` - GIS routing
- `app.services.traffic_service` - Traffic data
- `app.services.graph_utils` - Graph utilities
- `app.websockets.connection_manager` - WebSocket
- `app.websockets.redis_pubsub` - Redis Pub/Sub
- `app.tasks.celery_app` - Celery configuration
- `app.utils.cache` - Redis cache
- `app.db.models` - Database models
- `app.schemas.routing`, `app.schemas.realtime` - Schemas

---

## Performance Targets
| Operation | Target (P99) |
|-----------|--------------|
| Live ETA computation | < 50ms (cached), < 200ms (uncached) |
| Alternate route generation | < 500ms (cached), < 2s (uncached) |
| Reroute detection | < 100ms |
| WebSocket ETA push | < 10ms |
| Route monitor tick (100 routes) | < 5s |

---

## Verification Checklist
- [ ] All RC8.0-8.3 tests still pass
- [ ] New unit tests pass
- [ ] Integration tests pass
- [ ] WebSocket events fire correctly
- [ ] Celery tasks execute on schedule
- [ ] Redis caching works with TTL
- [ ] No N+1 queries in route monitoring
- [ ] API endpoints return correct schemas
- [ ] Documentation complete
- [ ] CONTEXT.md updated