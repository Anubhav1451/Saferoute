"""
Data ingestion layer for safety data.
Fetches data from the database for feature engineering and model training.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.db.models import SafetyNode, CrimeHotspot, UserReport
from app.db.session import get_db
import logging

logger = logging.getLogger(__name__)

def get_recent_safety_nodes(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    limit: int = 1000
) -> List[SafetyNode]:
    """
    Get safety nodes within a radius of a point.
    Uses bounding box approximation for efficiency.
    """
    # Convert radius to degrees (approximate)
    lat_delta = radius_meters / 111000  # 1 degree latitude ≈ 111 km
    lon_delta = radius_meters / (111000 * abs(latitude * 0.0174533))  # adjust for latitude

    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    nodes = db.query(SafetyNode).filter(
        and_(
            SafetyNode.latitude >= min_lat,
            SafetyNode.latitude <= max_lat,
            SafetyNode.longitude >= min_lon,
            SafetyNode.longitude <= max_lon
        )
    ).limit(limit).all()

    return nodes

def get_recent_crime_hotspots(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    days: int = 30,
    limit: int = 1000
) -> List[CrimeHotspot]:
    """
    Get crime hotspots within a radius and time window.
    Note: CrimeHotspot doesn't have a timestamp, so we assume they are persistent.
    In a real system, we would have a timestamp for when the crime was recorded.
    """
    # Convert radius to degrees (approximate)
    lat_delta = radius_meters / 111000
    lon_delta = radius_meters / (111000 * abs(latitude * 0.0174533))

    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    hotspots = db.query(CrimeHotspot).filter(
        and_(
            CrimeHotspot.latitude >= min_lat,
            CrimeHotspot.latitude <= max_lat,
            CrimeHotspot.longitude >= min_lon,
            CrimeHotspot.longitude <= max_lon
        )
    ).limit(limit).all()

    return hotspots

def get_recent_user_reports(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    days: int = 7,
    limit: int = 1000
) -> List[UserReport]:
    """
    Get user reports within a radius and time window.
    """
    # Convert radius to degrees (approximate)
    lat_delta = radius_meters / 111000
    lon_delta = radius_meters / (111000 * abs(latitude * 0.0174533))

    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta

    cutoff_time = datetime.utcnow() - timedelta(days=days)

    reports = db.query(UserReport).filter(
        and_(
            UserReport.latitude >= min_lat,
            UserReport.latitude <= max_lat,
            UserReport.longitude >= min_lon,
            UserReport.longitude <= max_lon,
            UserReport.timestamp >= cutoff_time,
            UserReport.is_active == True
        )
    ).limit(limit).all()

    return reports

def get_safety_data_for_location(
    db: Session,
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None,
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """
    Get all safety data for a location at a specific time.
    Returns a dictionary containing safety nodes, crime hotspots, and user reports.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    # For simplicity, we're not using timestamp for filtering in this version
    # since our mock data doesn't have timestamps on safety nodes and crime hotspots
    # In a real system, we would filter by timestamp

    safety_nodes = get_recent_safety_nodes(db, latitude, longitude, radius_meters)
    crime_hotspots = get_recent_crime_hotspots(db, latitude, longitude, radius_meters)
    user_reports = get_recent_user_reports(db, latitude, longitude, radius_meters)

    return {
        "safety_nodes": safety_nodes,
        "crime_hotspots": crime_hotspots,
        "user_reports": user_reports,
        "timestamp": timestamp,
        "location": {"latitude": latitude, "longitude": longitude}
    }