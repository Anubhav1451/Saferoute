from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Enum as SQLEnum, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class LightingLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CrowdDensity(enum.Enum):
    SPARSE = "SPARSE"
    NORMAL = "NORMAL"
    DENSE = "DENSE"


class SeverityLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SafetyNode(Base):
    __tablename__ = "safety_nodes"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    safety_score = Column(Float, nullable=False)  # 0.0 to 1.0, higher is safer
    lighting_level = Column(SQLEnum(LightingLevel), nullable=False, index=True)
    crowd_density = Column(SQLEnum(CrowdDensity), nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Composite index for spatial queries (latitude, longitude)
    __table_args__ = (Index('ix_safety_nodes_lat_lon', 'latitude', 'longitude'),)


class CrimeHotspot(Base):
    __tablename__ = "crime_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    radius = Column(Float, nullable=False)  # in meters
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    description = Column(String(500))
    # Composite index for spatial queries
    __table_args__ = (Index('ix_crime_hotspots_lat_lon', 'latitude', 'longitude'),)


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    report_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)
    # Composite index for spatial queries
    __table_args__ = (Index('ix_user_reports_lat_lon', 'latitude', 'longitude'),)


class BlackSpotSeverity(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AccidentSeverity(enum.Enum):
    FATAL = "FATAL"
    GRIEVOUS = "GRIEVOUS"
    SIMPLE = "SIMPLE"


class HighwayBlackSpot(Base):
    __tablename__ = "highway_black_spots"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    radius = Column(Float, nullable=False)
    severity = Column(SQLEnum(BlackSpotSeverity), nullable=False, index=True)
    accident_count = Column(Integer, default=0)
    fatalities = Column(Integer, default=0)
    last_accident_date = Column(DateTime, nullable=True)
    road_name = Column(String(200), nullable=True)
    description = Column(String(500), nullable=True)
    source = Column(String(100), default="MoRTH")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    state = Column(String(50), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    highway_number = Column(String(50), nullable=True, index=True)
    managed_by = Column(String(100), nullable=True)
    official_id = Column(String(100), nullable=True, index=True)
    chainage_start_km = Column(Float, nullable=True)
    chainage_end_km = Column(Float, nullable=True)
    location_text = Column(String(500), nullable=True)
    geometry_resolution = Column(String(50), nullable=True)
    source_name = Column(String(100), nullable=True)
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, nullable=True)

    __table_args__ = (
        Index('ix_highway_black_spots_lat_lon', 'latitude', 'longitude'),
        Index('ix_highway_black_spots_state_district', 'state', 'district'),
        Index('ix_highway_black_spots_hwy_chainage', 'highway_number', 'chainage_start_km'),
    )


class AccidentRecord(Base):
    __tablename__ = "accident_records"

    id = Column(Integer, primary_key=True, index=True)
    black_spot_id = Column(Integer, ForeignKey("highway_black_spots.id"), nullable=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    accident_date = Column(DateTime, nullable=False, index=True)
    severity = Column(SQLEnum(AccidentSeverity), nullable=False, index=True)
    fatalities = Column(Integer, default=0)
    injuries = Column(Integer, default=0)
    vehicles_involved = Column(Integer, default=1)
    road_name = Column(String(200), nullable=True)
    weather_condition = Column(String(50), nullable=True)
    time_of_day = Column(String(20), nullable=True)
    description = Column(String(500), nullable=True)
    source = Column(String(100), default="MoRTH")
    created_at = Column(DateTime, default=datetime.utcnow)

    state = Column(String(50), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    year = Column(Integer, nullable=True, index=True)
    collision_type = Column(String(100), nullable=True, index=True)
    violation_type = Column(String(100), nullable=True, index=True)
    road_user_type = Column(String(100), nullable=True)
    vehicle_type = Column(String(100), nullable=True)
    road_class = Column(String(50), nullable=True, index=True)
    source_name = Column(String(100), nullable=True)
    aggregation_level = Column(String(50), nullable=True, index=True)

    black_spot = relationship("HighwayBlackSpot", backref="accidents")

    __table_args__ = (
        Index('ix_accident_records_lat_lon', 'latitude', 'longitude'),
        Index('ix_accident_records_black_spot_id', 'black_spot_id'),
        Index('ix_accident_records_date_severity', 'accident_date', 'severity'),
        Index('ix_accident_records_state_year', 'state', 'year'),
        Index('ix_accident_records_date_aggregation', 'accident_date', 'aggregation_level'),
    )


class RoadSegmentRisk(Base):
    __tablename__ = "road_segment_risks"

    id = Column(Integer, primary_key=True, index=True)
    start_latitude = Column(Float, nullable=False, index=True)
    start_longitude = Column(Float, nullable=False, index=True)
    end_latitude = Column(Float, nullable=False)
    end_longitude = Column(Float, nullable=False)
    road_name = Column(String(200), nullable=True)
    segment_length_m = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    accident_frequency = Column(Float, default=0.0)
    severity_distribution = Column(String(500), nullable=True)
    record_count = Column(Integer, default=0)
    last_accident_date = Column(DateTime, nullable=True)
    data_source = Column(String(100), default="MoRTH+Police")
    computed_at = Column(DateTime, default=datetime.utcnow)

    segment_length_km = Column(Float, nullable=True)
    highway_number = Column(String(50), nullable=True, index=True)
    road_class = Column(String(50), nullable=True, index=True)
    exposure_factor = Column(Float, nullable=True)
    accident_density = Column(Float, nullable=True)
    fatality_weight = Column(Float, nullable=True)
    blackspot_weight = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_road_segment_risks_lat_lon', 'start_latitude', 'start_longitude'),
        Index('ix_road_segment_risks_score', 'risk_score'),
        Index('ix_road_segment_risks_hwy_class', 'highway_number', 'road_class'),
    )


class OSMWay(Base):
    __tablename__ = "osm_ways"

    id = Column(Integer, primary_key=True, index=True)
    osm_id = Column(Integer, unique=True, nullable=False, index=True)
    highway = Column(String(100), nullable=False, index=True)
    name = Column(String(500), nullable=True)
    ref = Column(String(100), nullable=True, index=True)
    oneway = Column(String(50), nullable=True)
    maxspeed = Column(String(50), nullable=True)
    lanes = Column(String(50), nullable=True)
    bridge = Column(String(50), nullable=True)
    tunnel = Column(String(50), nullable=True)
    geometry_wkt = Column(String, nullable=True)  # Well-Known Text for PostGIS compatibility
    processed_at = Column(DateTime, nullable=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_osm_ways_highway_ref', 'highway', 'ref'),
    )


class OSMWayNode(Base):
    __tablename__ = "osm_way_nodes"

    id = Column(Integer, primary_key=True, index=True)
    way_id = Column(Integer, ForeignKey("osm_ways.id"), nullable=False, index=True)
    osm_node_id = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    __table_args__ = (
        Index('ix_osm_way_nodes_way_seq', 'way_id', 'sequence'),
    )


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(Integer, primary_key=True, index=True)
    osm_node_id = Column(Integer, unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    __table_args__ = (
        Index('ix_graph_nodes_lat_lon', 'latitude', 'longitude'),
    )


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False, index=True)
    dest_node_id = Column(Integer, ForeignKey("graph_nodes.id"), nullable=False, index=True)
    osm_way_id = Column(Integer, ForeignKey("osm_ways.id"), nullable=True, index=True)
    geometry_wkt = Column(String, nullable=True)
    length = Column(Float, nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # 'BIDIRECTIONAL', 'FORWARD', 'BACKWARD'
    highway = Column(String(100), nullable=False)
    maxspeed = Column(Float, nullable=True)
    travel_time = Column(Float, nullable=False, index=True)
    road_class = Column(String(50), nullable=False, index=True)
    
    # Enrichment Metadata
    priority = Column(Integer, nullable=True, index=True)
    speed_priority = Column(Integer, nullable=True)
    access = Column(String(100), nullable=True)
    roundabout = Column(Boolean, default=False)
    surface = Column(String(100), nullable=True)
    smoothness = Column(String(100), nullable=True)
    lit = Column(String(100), nullable=True)
    lanes = Column(Integer, nullable=True)
    width = Column(Float, nullable=True)
    is_bridge = Column(Boolean, default=False)
    is_tunnel = Column(Boolean, default=False)
    
    # Spatial properties
    heading = Column(Float, nullable=True)
    mid_lat = Column(Float, nullable=True, index=True)
    mid_lon = Column(Float, nullable=True, index=True)
    bbox_min_lat = Column(Float, nullable=True)
    bbox_min_lon = Column(Float, nullable=True)
    bbox_max_lat = Column(Float, nullable=True)
    bbox_max_lon = Column(Float, nullable=True)

    __table_args__ = (
        Index('ix_graph_edges_nodes', 'source_node_id', 'dest_node_id'),
        Index('ix_graph_edges_midpoint', 'mid_lat', 'mid_lon'),
    )


class IncidentType(enum.Enum):
    """Types of traffic incidents."""
    ACCIDENT = "ACCIDENT"
    CONGESTION = "CONGESTION"
    ROADWORK = "ROADWORK"
    WEATHER = "WEATHER"
    HAZARD = "HAZARD"
    EVENT = "EVENT"
    BROKEN_DOWN_VEHICLE = "BROKEN_DOWN_VEHICLE"
    ROAD_CLOSURE = "ROAD_CLOSURE"
    LANE_CLOSURE = "LANE_CLOSURE"
    DEBRIS = "DEBRIS"
    FLOODING = "FLOODING"
    POLICE_ACTIVITY = "POLICE_ACTIVITY"


class IncidentSeverity(enum.Enum):
    """Severity levels for traffic incidents."""
    LOW = "LOW"           # Minor impact, single lane
    MEDIUM = "MEDIUM"     # Moderate impact, multiple lanes
    HIGH = "HIGH"         # Major impact, significant delay
    CRITICAL = "CRITICAL" # Severe impact, road closed


class TrafficIncident(Base):
    """Real-time traffic incidents with location, severity, and metadata."""
    __tablename__ = "traffic_incidents"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)  # From external source

    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    road_name = Column(String(200), nullable=True)
    road_class = Column(String(50), nullable=True, index=True)

    # Incident details
    incident_type = Column(SQLEnum(IncidentType), nullable=False, index=True)
    severity = Column(SQLEnum(IncidentSeverity), nullable=False, index=True)
    description = Column(String(1000), nullable=True)

    # Lane/road impact
    lanes_affected = Column(Integer, nullable=True)       # Number of lanes affected
    total_lanes = Column(Integer, nullable=True)          # Total lanes on road
    direction = Column(String(20), nullable=True)         # 'BOTH', 'INBOUND', 'OUTBOUND'
    closure_type = Column(String(30), nullable=True)      # 'FULL', 'PARTIAL', 'LANE'

    # Timestamps and TTL
    started_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    reported_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)  # TTL for auto-cleanup
    cleared_at = Column(DateTime, nullable=True)

    # Source and confidence
    source = Column(String(100), nullable=False, index=True)  # e.g., 'HERE', 'TomTom', 'Waze', 'Police', 'User'
    source_id = Column(String(100), nullable=True)            # External source's ID
    confidence = Column(Float, nullable=False, default=0.8)   # 0.0 to 1.0
    verified = Column(Boolean, default=False, index=True)

    # Metadata
    metadata_json = Column(String, nullable=True)  # JSON for additional source-specific data
    delay_minutes = Column(Integer, nullable=True)  # Estimated delay in minutes
    queue_length_m = Column(Float, nullable=True)   # Queue length in meters

    # PostGIS Geometry column added by migration (Point or Polygon for road extent)

    __table_args__ = ()

    # Property for active status
    @property
    def is_active(self) -> bool:
        """Check if incident is currently active."""
        now = datetime.utcnow()
        if self.cleared_at and self.cleared_at <= now:
            return False
        if self.expires_at and self.expires_at <= now:
            return False
        return True


class TrafficFlow(Base):
    """Real-time traffic flow data for road segments."""
    __tablename__ = "traffic_flow"

    id = Column(Integer, primary_key=True, index=True)

    # Location - linked to road segment or edge
    edge_id = Column(Integer, ForeignKey("graph_edges.id"), nullable=True, index=True)
    osm_way_id = Column(Integer, ForeignKey("osm_ways.id"), nullable=True, index=True)

    # Alternative direct location
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    road_name = Column(String(200), nullable=True)

    # Flow metrics
    speed_kmh = Column(Float, nullable=False)     # Current speed in km/h
    free_flow_speed_kmh = Column(Float, nullable=True)  # Free-flow reference speed
    congestion_level = Column(Integer, nullable=False, index=True)  # 0=free, 1=light, 2=moderate, 3=heavy, 4=severe
    jam_factor = Column(Float, nullable=True)     # 0.0 to 10.0 (HERE format)

    # Volume and occupancy
    vehicle_count = Column(Integer, nullable=True)
    occupancy_percent = Column(Float, nullable=True)  # 0.0 to 100.0

    # Travel time
    travel_time_seconds = Column(Integer, nullable=True)
    free_flow_travel_time_seconds = Column(Integer, nullable=True)
    delay_seconds = Column(Integer, nullable=True)

    # Timestamps and TTL
    measured_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, index=True)  # TTL

    # Source and confidence
    source = Column(String(100), nullable=False, index=True)  # 'HERE', 'TomTom', 'Inrix', 'OSM', 'Sensor'
    source_id = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=0.8)

    # Metadata
    metadata_json = Column(String, nullable=True)

    # Road segment reference
    segment_length_m = Column(Float, nullable=True)

    # PostGIS Geometry column added by migration (LineString for road segment)

    __table_args__ = ()

    @property
    def congestion_ratio(self) -> float:
        """Speed ratio (0.0-1.0), 1.0 = free flow."""
        if self.free_flow_speed_kmh and self.free_flow_speed_kmh > 0:
            return min(1.0, self.speed_kmh / self.free_flow_speed_kmh)
        return 1.0

    @property
    def delay_factor(self) -> float:
        """Travel time multiplier due to congestion."""
        if self.free_flow_travel_time_seconds and self.free_flow_travel_time_seconds > 0:
            return self.travel_time_seconds / self.free_flow_travel_time_seconds
        return 1.0


class RoadClosure(Base):
    """Road closures with geometry, schedule, and alternatives."""
    __tablename__ = "road_closures"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)

    # Location
    name = Column(String(200), nullable=True)
    road_name = Column(String(200), nullable=True, index=True)
    road_class = Column(String(50), nullable=True, index=True)

    # Closure geometry (line or polygon)
    start_latitude = Column(Float, nullable=True, index=True)
    start_longitude = Column(Float, nullable=True, index=True)
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)

    # Closure details
    closure_type = Column(String(30), nullable=False, index=True)  # 'FULL', 'PARTIAL', 'LANE', 'RAMP'
    direction = Column(String(20), nullable=True)  # 'BOTH', 'INBOUND', 'OUTBOUND'
    lanes_closed = Column(Integer, nullable=True)
    total_lanes = Column(Integer, nullable=True)

    # Reason and description
    reason = Column(String(200), nullable=False, index=True)  # 'CONSTRUCTION', 'EVENT', 'WEATHER', 'ACCIDENT', 'MAINTENANCE'
    description = Column(String(2000), nullable=True)

    # Schedule
    starts_at = Column(DateTime, nullable=False, index=True)
    ends_at = Column(DateTime, nullable=True, index=True)  # NULL = indefinite
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(500), nullable=True)  # iCal RRULE format

    # Affected roads
    affected_edges = Column(String, nullable=True)  # JSON array of edge IDs
    alternative_routes = Column(String, nullable=True)  # JSON array of alternative route descriptions

    # Source
    source = Column(String(100), nullable=False, index=True)
    source_id = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)
    verified = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # PostGIS Geometry column added by migration (LineString or Polygon)

    __table_args__ = ()

    @property
    def is_active(self) -> bool:
        """Check if closure is currently active."""
        now = datetime.utcnow()
        if self.starts_at > now:
            return False
        if self.ends_at and self.ends_at <= now:
            return False
        return True

    @property
    def is_future(self) -> bool:
        """Check if closure is scheduled for the future."""
        return self.starts_at > datetime.utcnow()

    @property
    def is_indefinite(self) -> bool:
        """Check if closure has no end date."""
        return self.ends_at is None


class ConstructionZone(Base):
    """Construction zones with extended schedules and phasing."""
    __tablename__ = "construction_zones"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)
    project_id = Column(String(100), nullable=True, index=True)  # Groups related zones

    # Location
    name = Column(String(200), nullable=False)
    road_name = Column(String(200), nullable=True, index=True)
    road_class = Column(String(50), nullable=True, index=True)
    start_latitude = Column(Float, nullable=True, index=True)
    start_longitude = Column(Float, nullable=True, index=True)
    end_latitude = Column(Float, nullable=True)
    end_longitude = Column(Float, nullable=True)
    length_m = Column(Float, nullable=True)

    # Zone details
    zone_type = Column(String(50), nullable=False, index=True)  # 'ROADWORK', 'BRIDGE_WORK', 'UTILITY', 'RESURFACING', 'EXPANSION'
    description = Column(String(2000), nullable=True)
    impact_level = Column(String(20), nullable=False, default='MODERATE', index=True)  # 'LOW', 'MODERATE', 'HIGH', 'SEVERE'

    # Lanes
    lanes_affected = Column(Integer, nullable=True)
    lanes_remaining = Column(Integer, nullable=True)
    contraflow = Column(Boolean, default=False)  # Contraflow traffic pattern
    speed_limit_kmh = Column(Integer, nullable=True)  # Temporary speed limit

    # Schedule
    planned_start = Column(DateTime, nullable=False, index=True)
    planned_end = Column(DateTime, nullable=True, index=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    is_active_now = Column(Boolean, default=False, index=True)

    # Phasing
    phase = Column(String(100), nullable=True)  # Current phase name
    total_phases = Column(Integer, nullable=True)

    # Contractor/authority
    authority = Column(String(200), nullable=True)  # Government agency
    contractor = Column(String(200), nullable=True)
    contact_info = Column(String(500), nullable=True)

    # Source
    source = Column(String(100), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=False, default=0.9)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # PostGIS Geometry column added by migration (LineString or Polygon)

    __table_args__ = ()

    @property
    def is_currently_active(self) -> bool:
        """Check if construction is currently active."""
        now = datetime.utcnow()
        if self.actual_start and self.actual_start <= now:
            if self.actual_end is None or self.actual_end > now:
                return True
            if self.planned_end and self.planned_end > now:
                return True
        if self.planned_start <= now:
            if self.planned_end is None or self.planned_end > now:
                return True
        return False
