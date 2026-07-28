"""
Feature engineering for road segments.
Extracts static, historical, dynamic, and graph-based features for each road segment.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import math
import numpy as np

from app.db.models import (
    GraphEdge,
    GraphNode,
    OSMWay,
    AccidentRecord,
    HighwayBlackSpot,
    RoadSegmentRisk,
    AccidentSeverity,
    BlackSpotSeverity,
    LightingLevel,
    CrowdDensity,
    SeverityLevel,
)


# Constants for normalization (based on domain knowledge and data inspection)
# These values are chosen to cover the expected range of values.
# For features without known bounds, we use percentile-based estimates from training data.

# Static feature normalization constants
LANES_MAX = 10.0  # Assume max 10 lanes
SPEED_LIMIT_MAX = 200.0  # km/h, reasonable max speed limit
# Road class: we'll map to ordinal and normalize by number of classes
ROAD_CLASS_ORDER = [
    'motorway', 'trunk', 'primary', 'secondary', 'tertiary',
    'unclassified', 'residential', 'service', 'footway', 'cycleway', 'path',
    'living_street', 'track', 'raceway', 'road',  # fallback
]
NUM_ROAD_CLASSES = len(ROAD_CLASS_ORDER)

# Historical feature normalization constants
# These are based on typical values; in production, these should be computed from training data
ACCIDENT_COUNT_MAX = 20.0  # accidents per segment (over history)
FATAL_COUNT_MAX = 5.0
GRIEVOUS_COUNT_MAX = 10.0
BLACKSPOT_COUNT_MAX = 5.0
ACCIDENT_DENSITY_MAX = 10.0  # accidents per km
SEVERITY_INDEX_MAX = 100.0  # weighted sum, max plausible
RECENCY_WEIGHT_MAX = 1.0  # exponential decay weight, max 1.0
CONFIDENCE_MAX = 1.0  # already 0-1

# Dynamic feature normalization constants (placeholders)
# These will be set to unknown (-1.0) until real data sources are integrated
WEATHER_UNKNOWN = -1.0
TRAFFIC_UNKNOWN = -1.0
VISIBILITY_UNKNOWN = -1.0
CONSTRUCTION_UNKNOWN = -1.0

# Graph feature normalization constants
DEGREE_MAX = 20.0  # max degree of a node in the road network
# Betweenness and centrality are normalized to [0,1] by algorithm, so we keep as is
# Connectivity: binary (connected or not) -> 0.0 or 1.0


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def _get_road_class_index(road_class: str) -> int:
    """Map road class string to index, returning -1 if unknown."""
    try:
        return ROAD_CLASS_ORDER.index(road_class.lower())
    except ValueError:
        return -1


def _get_degree_from_node(session: Session, node_id: int) -> int:
    """Get the degree (number of connected edges) for a graph node."""
    # Count edges where node is either source or destination
    count = session.query(GraphEdge).filter(
        or_(
            GraphEdge.source_node_id == node_id,
            GraphEdge.dest_node_id == node_id
        )
    ).count()
    return count


@dataclass
class RoadSegmentFeatures:
    """
    Features for a road segment, all normalized to [0, 1] where applicable.
    Unknown or missing values are represented as -1.0.
    """
    # Static features
    road_class: float  # normalized index of road class [0,1]
    lanes: float  # normalized lane count [0,1]
    speed_limit: float  # normalized speed limit [0,1]
    one_way: float  # 0.0 for two-way, 1.0 for one-way
    junction: float  # 1.0 if either endpoint is a junction (degree > 2), else 0.0
    bridge: float  # 1.0 if bridge, else 0.0
    tunnel: float  # 1.0 if tunnel, else 0.0
    curvature: float  # estimate of curvature [0,1] (0 = straight, 1 = highly curved) - placeholder
    elevation: float  # normalized elevation [-1,1] -> [0,1] via shift - placeholder
    urban_rural: float  # 0.0 rural, 1.0 urban - placeholder
    lighting: float  # normalized lighting score [0,1] (0 = dark, 1 = well lit)
    surface: float  # encoded surface type [0,1] - placeholder
    smoothness: float  # encoded smoothness [0,1] - placeholder

    # Historical features (from accident and blackspot data)
    accident_count: float  # normalized count of accidents [0,1]
    fatal_count: float  # normalized count of fatal accidents [0,1]
    grievous_count: float  # normalized count of grievous injuries [0,1]
    blackspot_count: float  # normalized count of black spots [0,1]
    accident_density: float  # normalized accidents per km [0,1]
    severity_index: float  # normalized weighted severity score [0,1]
    recency_weight: float  # normalized recency weight [0,1]
    confidence: float  # confidence in historical data [0,1]

    # Dynamic features (placeholder - to be implemented with real-time data)
    weather: float  # weather condition impact [0,1] - unknown
    traffic: float  # traffic density [0,1] - unknown
    visibility: float  # visibility conditions [0,1] - unknown
    construction: float  # construction activity [0,1] - unknown

    # Graph-based features
    degree: float  # average node degree normalized [0,1]
    betweenness: float  # betweenness centrality [0,1] - placeholder
    closeness: float  # closeness centrality [0,1] - placeholder
    connectivity: float  # 1.0 if node is connected to giant component, else 0.0 - placeholder


def extract_features_for_edge(session: Session, edge: GraphEdge) -> RoadSegmentFeatures:
    """
    Extract all features for a given graph edge.

    Args:
        session: Database session
        edge: GraphEdge object representing the road segment

    Returns:
        RoadSegmentFeatures object with all features extracted and normalized
    """
    # Initialize all features to unknown (-1.0)
    # We'll set known values as we compute them

    # --- Static Features ---
    # Road class
    road_class_idx = _get_road_class_index(edge.road_class) if edge.road_class else -1
    road_class_norm = _safe_divide(road_class_idx, float(NUM_ROAD_CLASSES - 1)) if road_class_idx != -1 else -1.0

    # Lanes
    lanes_norm = _safe_divide(float(edge.lanes) if edge.lanes is not None else -1.0, LANES_MAX) \
        if edge.lanes is not None and edge.lanes >= 0 else -1.0

    # Speed limit
    speed_limit_norm = _safe_divide(float(edge.maxspeed) if edge.maxspeed is not None else -1.0, SPEED_LIMIT_MAX) \
        if edge.maxspeed is not None and edge.maxspeed >= 0 else -1.0

    # One-way (direction field: 'BIDIRECTIONAL', 'FORWARD', 'BACKWARD')
    one_way_val = 1.0 if edge.direction and edge.direction != 'BIDIRECTIONAL' else 0.0

    # Junction: determine if either node is a junction (degree > 2)
    # Note: We consider a node a junction if it has more than 2 connections (dead end=1, straight=2, junction>=3)
    src_degree = _get_degree_from_node(edge.source_node_id) if edge.source_node_id else -1
    dst_degree = _get_degree_from_node(edge.dest_node_id) if edge.dest_node_id else -1
    junction_val = 1.0 if (src_degree > 2 or dst_degree > 2) else 0.0
    # If we couldn't compute degree, mark as unknown
    if src_degree == -1 or dst_degree == -1:
        junction_val = -1.0

    # Bridge
    bridge_val = 1.0 if edge.is_bridge else 0.0

    # Tunnel
    tunnel_val = 1.0 if edge.is_tunnel else 0.0

    # Curvature: placeholder - we don't have direct curvature, but we can estimate from heading change?
    # For now, set to unknown
    curvature_val = -1.0

    # Elevation: placeholder
    elevation_val = -1.0

    # Urban/Rural: placeholder
    urban_rural_val = -1.0

    # Lighting: from edge.lit (string: 'yes', 'no', or unknown)
    lighting_val = -1.0
    if edge.lit:
        lit_str = edge.lit.lower()
        if lit_str == 'yes':
            lighting_val = 1.0
        elif lit_str == 'no':
            lighting_val = 0.0
        # else leave as -1.0 (unknown)

    # Surface: placeholder - encode surface type
    surface_val = -1.0

    # Smoothness: placeholder - encode smoothness
    smoothness_val = -1.0

    # --- Historical Features ---
    # We'll query RoadSegmentRisk for this segment (by coordinates) or by osm_way_id?
    # The RoadSegmentRisk table is defined by start/end lat/lon, not by graph edge.
    # We'll try to find a matching RoadSegmentRisk by proximity to the edge's midpoint.
    # For simplicity, we'll use the edge's midpoint and look for nearby Risk segments.

    # Get midpoint of the edge
    mid_lat = (edge.mid_lat if edge.mid_lat is not None else
               (edge.source_node.latitude + edge.dest_node.latitude) / 2.0 if edge.source_node and edge.dest_node else None)
    mid_lon = (edge.mid_lon if edge.mid_lon is not None else
               (edge.source_node.longitude + edge.dest_node.longitude) / 2.0 if edge.source_node and edge.dest_node else None)

    # Default historical values to unknown
    accident_count_val = -1.0
    fatal_count_val = -1.0
    grievous_count_val = -1.0
    blackspot_count_val = -1.0
    accident_density_val = -1.0
    severity_index_val = -1.0
    recency_weight_val = -1.0
    confidence_val = -1.0

    if mid_lat is not None and mid_lon is not None:
        # Look for road segment risks near this point (within ~50m)
        lat_range = 0.0005  # ~50m in latitude
        lon_range = 0.0005  # ~50m in latitude at equator, adjust for latitude
        # Adjust longitude range for latitude
        if mid_lat is not None:
            lon_range = 0.0005 / max(0.0001, abs(math.cos(math.radians(mid_lat))))
        else:
            lon_range = 0.0005

        risk_records = session.query(RoadSegmentRisk).filter(
            and_(
                RoadSegmentRisk.start_latitude >= mid_lat - lat_range,
                RoadSegmentRisk.start_latitude <= mid_lat + lat_range,
                RoadSegmentRisk.start_longitude >= mid_lon - lon_range,
                RoadSegmentRisk.start_longitude <= mid_lon + lon_range
            )
        ).all()

        if risk_records:
            # Use the closest risk record (by distance to midpoint)
            def dist_sq(r):
                return (r.start_latitude - mid_lat)**2 + (r.start_longitude - mid_lon)**2
            closest_risk = min(risk_records, key=dist_sq)

            # Accident count (from record_count)
            accident_count_val = _safe_divide(float(closest_risk.record_count), ACCIDENT_COUNT_MAX) \
                if closest_risk.record_count is not None else -1.0

            # Fatal and grievous counts: we don't have these in Risk, need to query AccidentRecord
            # We'll query accidents near this segment
            # For simplicity, we'll use the same bounding box
            acc_records = session.query(AccidentRecord).filter(
                and_(
                    AccidentRecord.latitude >= mid_lat - lat_range,
                    AccidentRecord.latitude <= mid_lat + lat_range,
                    AccidentRecord.longitude >= mid_lon - lon_range,
                    AccidentRecord.longitude <= mid_lon + lon_range
                )
            ).all()

            fatal_count = 0
            grievous_count = 0
            for acc in acc_records:
                if acc.severity == AccidentSeverity.FATAL:
                    fatal_count += 1
                elif acc.severity == AccidentSeverity.GRIEVOUS:
                    grievous_count += 1
            fatal_count_val = _safe_divide(float(fatal_count), FATAL_COUNT_MAX)
            grievous_count_val = _safe_divide(float(grievous_count), GRIEVOUS_COUNT_MAX)

            # Black spot count: query HighwayBlackSpot near the segment
            bs_records = session.query(HighwayBlackSpot).filter(
                and_(
                    HighwayBlackSpot.latitude >= mid_lat - lat_range,
                    HighwayBlackSpot.latitude <= mid_lat + lat_range,
                    HighwayBlackSpot.longitude >= mid_lon - lon_range,
                    HighwayBlackSpot.longitude <= mid_lon + lon_range
                )
            ).count()
            blackspot_count_val = _safe_divide(float(bs_records), BLACKSPOT_COUNT_MAX)

            # Accident density: from risk record if available
            accident_density_val = _safe_divide(float(closest_risk.accident_density), ACCIDENT_DENSITY_MAX) \
                if closest_risk.accident_density is not None else -1.0

            # Severity index: compute from accidents in the same area
            # We'll use a simple weighting: fatal=2, grievous=1, simple=0
            severity_sum = 0
            for acc in acc_records:
                if acc.severity == AccidentSeverity.FATAL:
                    severity_sum += 2
                elif acc.severity == AccidentSeverity.GRIEVOUS:
                    severity_sum += 1
                # simple adds 0
            severity_index_val = _safe_divide(float(severity_sum), SEVERITY_INDEX_MAX)

            # Recency weight: exponential decay based on accident dates
            now = datetime.utcnow()
            total_weight = 0.0
            half_life_days = 365.0  # 1 year half-life
            for acc in acc_records:
                if acc.accident_date:
                    days_old = (now - acc.accident_date).days
                    weight = 0.5 ** (days_old / half_life_days)
                    total_weight += weight
            # Normalize by max possible weight (if all accidents were today)
            max_possible_weight = len(acc_records) * 1.0
            recency_weight_val = _safe_divide(total_weight, max_possible_weight) if max_possible_weight > 0 else 0.0

            # Confidence: from risk record confidence score
            confidence_val = _safe_divide(float(closest_risk.confidence_score), CONFIDENCE_MAX) \
                if closest_risk.confidence_score is not None else -1.0

    # --- Dynamic Features (placeholder) ---
    weather_val = WEATHER_UNKNOWN
    traffic_val = TRAFFIC_UNKNOWN
    visibility_val = VISIBILITY_UNKNOWN
    construction_val = CONSTRUCTION_UNKNOWN

    # --- Graph Features ---
    # Degree: average of the two node degrees
    degree_val = -1.0
    if src_degree != -1 and dst_degree != -1:
        avg_degree = (src_degree + dst_degree) / 2.0
        degree_val = _safe_divide(avg_degree, DEGREE_MAX)
    elif src_degree != -1:
        degree_val = _safe_divide(float(src_degree), DEGREE_MAX)
    elif dst_degree != -1:
        degree_val = _safe_divide(float(dst_degree), DEGREE_MAX)

    # Betweenness and closeness: placeholder (requires global graph computation)
    betweenness_val = -1.0
    closeness_val = -1.0

    # Connectivity: placeholder (we assume the graph is connected for now)
    connectivity_val = 1.0  # Assume connected; in reality we'd check connectivity to giant component

    return RoadSegmentFeatures(
        # Static
        road_class=road_class_norm,
        lanes=lanes_norm,
        speed_limit=speed_limit_norm,
        one_way=one_way_val,
        junction=junction_val,
        bridge=bridge_val,
        tunnel=tunnel_val,
        curvature=curvature_val,
        elevation=elevation_val,
        urban_rural=urban_rural_val,
        lighting=lighting_val,
        surface=surface_val,
        smoothness=smoothness_val,
        # Historical
        accident_count=accident_count_val,
        fatal_count=fatal_count_val,
        grievous_count=grievous_count_val,
        blackspot_count=blackspot_count_val,
        accident_density=accident_density_val,
        severity_index=severity_index_val,
        recency_weight=recency_weight_val,
        confidence=confidence_val,
        # Dynamic
        weather=weather_val,
        traffic=traffic_val,
        visibility=visibility_val,
        construction=construction_val,
        # Graph
        degree=degree_val,
        betweenness=betweenness_val,
        closeness=closeness_val,
        connectivity=connectivity_val
    )


def engineer_features(latitude: float, longitude: float, timestamp: Optional[datetime] = None, radius_meters: float = 1000.0, db: Optional[Session] = None) -> RoadSegmentFeatures:
    """
    Engineer features for a given point by finding the nearest road segment.

    This is a simplified version for the safety model fallback.
    In a full implementation, this would find the nearest road segment and extract features.
    For now, we return a default set of features.

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        timestamp: Time for which to predict safety (defaults to now)
        radius_meters: Radius to consider for features (defaults to 1000m)
        db: Database session (optional, will create one if not provided)

    Returns:
        RoadSegmentFeatures object with all features extracted and normalized
    """
    # For the fallback, we return a default set of features (all 0.5)
    # In a real implementation, we would query the database for the nearest road segment.
    # Since this is a fallback, we return a neutral feature set.
    return RoadSegmentFeatures(
        # Static
        road_class=0.5,
        lanes=0.5,
        speed_limit=0.5,
        one_way=0.0,
        junction=0.0,
        bridge=0.0,
        tunnel=0.0,
        curvature=0.5,
        elevation=0.5,
        urban_rural=0.5,
        lighting=0.5,
        surface=0.5,
        smoothness=0.5,
        # Historical
        accident_count=0.5,
        fatal_count=0.5,
        grievous_count=0.5,
        blackspot_count=0.5,
        accident_density=0.5,
        severity_index=0.5,
        recency_weight=0.5,
        confidence=0.5,
        # Dynamic
        weather=0.5,
        traffic=0.5,
        visibility=0.5,
        construction=0.5,
        # Graph
        degree=0.5,
        betweenness=0.5,
        closeness=0.5,
        connectivity=0.5
    )