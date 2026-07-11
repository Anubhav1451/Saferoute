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
