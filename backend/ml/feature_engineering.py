"""
Feature engineering layer for safety prediction.
Converts raw safety data into features for machine learning models.
"""
import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from ml.data_ingestion import get_safety_data_for_location
import logging

logger = logging.getLogger(__name__)

# Constants for feature engineering
EARTH_RADIUS_METERS = 6371000

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = EARTH_RADIUS_METERS * c

    return distance

def get_time_features(timestamp: datetime) -> Dict[str, Any]:
    """
    Extract time-based features from a timestamp.
    """
    return {
        "hour": timestamp.hour,
        "day_of_week": timestamp.weekday(),  # Monday=0, Sunday=6
        "day_of_month": timestamp.day,
        "month": timestamp.month,
        "is_weekend": 1 if timestamp.weekday() >= 5 else 0,  # Saturday=5, Sunday=6
        "is_night": 1 if timestamp.hour < 6 or timestamp.hour >= 20 else 0  # Night: 8PM-6AM
    }

def get_location_features(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get location-based features.
    In a more advanced system, we might include elevation, distance to city center, etc.
    For now, we just return the raw coordinates.
    """
    return {
        "latitude": latitude,
        "longitude": longitude
    }

def calculate_crime_density(
    crime_hotspots: List[CrimeHotspot],
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """
    Calculate crime density features based on crime hotspots.
    Weights by severity and proximity.
    """
    # Handle None or empty list
    if not crime_hotspots:
        return {
            "crime_density_weighted": 0.0,
            "crime_high_count": 0,
            "crime_medium_count": 0,
            "crime_low_count": 0,
            "crime_weighted_severity_avg": 0.0
        }

    total_weighted_count = 0.0
    high_severity_count = 0
    medium_severity_count = 0
    low_severity_count = 0
    total_weighted_severity = 0.0

    for hotspot in crime_hotspots:
        distance = haversine_distance(latitude, longitude, hotspot.latitude, hotspot.longitude)

        # Only consider hotspots within radius
        if distance < radius_meters:
            # Proximity weight (closer = higher weight)
            proximity_weight = 1.0 - (distance / radius_meters)

            # Severity weight
            if hotspot.severity == SeverityLevel.HIGH:
                severity_weight = 3.0
                high_severity_count += 1
            elif hotspot.severity == SeverityLevel.MEDIUM:
                severity_weight = 2.0
                medium_severity_count += 1
            else:  # LOW
                severity_weight = 1.0
                low_severity_count += 1

            # Combined weight
            weight = proximity_weight * severity_weight
            total_weighted_count += weight
            total_weighted_severity += weight * severity_weight

    return {
        "crime_density_weighted": total_weighted_count,
        "crime_high_count": high_severity_count,
        "crime_medium_count": medium_severity_count,
        "crime_low_count": low_severity_count,
        "crime_weighted_severity_avg": total_weighted_severity / max(total_weighted_count, 1)
    }

def calculate_lighting_features(
    safety_nodes: List[SafetyNode],
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """
    Calculate lighting features based on safety nodes.
    """
    # Handle None or empty list
    if not safety_nodes:
        return {
            "lighting_avg": 0.5,
            "low_lighting_count": 0,
            "total_safety_nodes": 0
        }

    lighting_scores = {
        LightingLevel.LOW: 0.0,
        LightingLevel.MEDIUM: 0.5,
        LightingLevel.HIGH: 1.0
    }

    total_weight = 0.0
    weighted_lighting_sum = 0.0
    low_lighting_count = 0
    total_nodes = len(safety_nodes)

    for node in safety_nodes:
        distance = haversine_distance(latitude, longitude, node.latitude, node.longitude)

        # Only consider nodes within radius
        if distance < radius_meters:
            # Proximity weight
            proximity_weight = 1.0 - (distance / radius_meters)

            # Lighting score
            lighting_score = lighting_scores[node.lighting_level]

            # Weighted sum
            weight = proximity_weight
            total_weight += weight
            weighted_lighting_sum += weight * lighting_score

            # Count low lighting nodes
            if node.lighting_level == LightingLevel.LOW:
                low_lighting_count += 1

    avg_lighting = weighted_lighting_sum / max(total_weight, 1) if total_weight > 0 else 0.5

    return {
        "lighting_avg": avg_lighting,
        "low_lighting_count": low_lighting_count,
        "total_safety_nodes": total_nodes
    }

def calculate_crowd_density_features(
    safety_nodes: List[SafetyNode],
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """
    Calculate crowd density features based on safety nodes.
    """
    # Handle None or empty list
    if not safety_nodes:
        return {
            "crowd_density_avg": 0.5,
            "sparse_crowd_count": 0,
            "total_safety_nodes": 0
        }

    crowd_scores = {
        CrowdDensity.SPARSE: 0.0,
        CrowdDensity.NORMAL: 0.5,
        CrowdDensity.DENSE: 1.0
    }

    total_weight = 0.0
    weighted_crowd_sum = 0.0
    sparse_crowd_count = 0
    total_nodes = len(safety_nodes)

    for node in safety_nodes:
        distance = haversine_distance(latitude, longitude, node.latitude, node.longitude)

        # Only consider nodes within radius
        if distance < radius_meters:
            # Proximity weight
            proximity_weight = 1.0 - (distance / radius_meters)

            # Crowd score
            crowd_score = crowd_scores[node.crowd_density]

            # Weighted sum
            weight = proximity_weight
            total_weight += weight
            weighted_crowd_sum += weight * crowd_score

            # Count sparse crowd nodes (potentially unsafe)
            if node.crowd_density == CrowdDensity.SPARSE:
                sparse_crowd_count += 1

    avg_crowd_density = weighted_crowd_sum / max(total_weight, 1) if total_weight > 0 else 0.5

    return {
        "crowd_density_avg": avg_crowd_density,
        "sparse_crowd_count": sparse_crowd_count,
        "total_safety_nodes": total_nodes
    }

def calculate_report_features(
    user_reports: List[UserReport],
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0
) -> Dict[str, Any]:
    """
    Calculate user report features.
    Weights by recency and type.
    """
    # Handle None or empty list
    if not user_reports:
        return {
            "report_count_1h": 0,
            "report_count_24h": 0,
            "report_count_7d": 0,
            "report_count_30d": 0,
            "report_weighted_recent": 0.0,
            "report_weighted_severity": 0.0
        }

    now = datetime.utcnow()

    # Time windows in seconds
    windows = {
        "last_1h": 3600,
        "last_24h": 86400,
        "last_7d": 604800,
        "last_30d": 2592000
    }

    # Initialize features
    features = {
        "report_count_1h": 0,
        "report_count_24h": 0,
        "report_count_7d": 0,
        "report_count_30d": 0,
        "report_weighted_recent": 0.0,
        "report_weighted_severity": 0.0
    }

    # Report type weights (higher = more severe)
    report_type_weights = {
        "SUSPICIOUS_ACTIVITY": 3.0,
        "NO_STREETLIGHTS": 2.0,
        "POOR_ROAD_CONDITION": 1.5,
        "OVERGROWN_VEGETATION": 1.0,
        "BROKEN_STREETLIGHT": 2.5,
        "DARK_AREA": 2.5,
        "UNSAFE_PATH": 3.0,
        "LACK_OF_SECURITY": 2.0
    }

    total_weight = 0.0
    weighted_severity_sum = 0.0

    for report in user_reports:
        distance = haversine_distance(latitude, longitude, report.latitude, report.longitude)

        # Only consider reports within radius
        if distance < radius_meters:
            # Proximity weight
            proximity_weight = 1.0 - (distance / radius_meters)

            # Time-based weights
            hours_old = (now - report.timestamp).total_seconds() / 3600
            days_old = hours_old / 24

            # Count reports in different time windows
            if hours_old < 1:
                features["report_count_1h"] += 1
            if hours_old < 24:
                features["report_count_24h"] += 1
            if days_old < 7:
                features["report_count_7d"] += 1
            if days_old < 30:
                features["report_count_30d"] += 1

            # Recency weight (exponential decay)
            recency_weight = math.exp(-hours_old / 24)  # Decay over days

            # Type weight
            type_weight = report_type_weights.get(report.report_type, 1.0)

            # Combined weight for reporting
            weight = proximity_weight * recency_weight * type_weight
            features["report_weighted_recent"] += weight

            # Weighted severity sum (for average severity)
            weighted_severity_sum += weight * type_weight
            total_weight += weight

    # Calculate average severity if we have reports
    if total_weight > 0:
        features["report_weighted_severity"] = weighted_severity_sum / total_weight
    else:
        features["report_weighted_severity"] = 0.0

    return features

def engineer_features(
    latitude: float,
    longitude: float,
    timestamp: Optional[datetime] = None,
    radius_meters: float = 1000.0,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Main feature engineering function.
    Takes location and time, returns a dictionary of features.
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    # Get a database session if not provided
    if db is None:
        # In a real application, we would use dependency injection or a context manager
        # For simplicity, we're creating a new session here
        try:
            from app.db.session import SessionLocal
            db = SessionLocal()
            close_db = True
        except Exception as e:
            logger.error(f"Failed to create database session: {e}")
            # Return default features if we can't connect to the database
            return _get_default_features(latitude, longitude, timestamp)
    else:
        close_db = False

    try:
        # Get safety data
        safety_data = get_safety_data_for_location(
            db, latitude, longitude, timestamp, radius_meters
        )

        safety_nodes = safety_data["safety_nodes"]
        crime_hotspots = safety_data["crime_hotspots"]
        user_reports = safety_data["user_reports"]

        # Initialize features dictionary
        features = {}

        # Add time features
        features.update(get_time_features(timestamp))

        # Add location features
        features.update(get_location_features(latitude, longitude))

        # Add crime density features
        features.update(calculate_crime_density(
            crime_hotspots, latitude, longitude, radius_meters
        ))

        # Add lighting features
        features.update(calculate_lighting_features(
            safety_nodes, latitude, longitude, radius_meters
        ))

        # Add crowd density features
        features.update(calculate_crowd_density_features(
            safety_nodes, latitude, longitude, radius_meters
        ))

        # Add report features
        features.update(calculate_report_features(
            user_reports, latitude, longitude, radius_meters
        ))

        return features

    except Exception as e:
        logger.error(f"Error in engineer_features: {e}")
        # Return default features on error
        return _get_default_features(latitude, longitude, timestamp)

    finally:
        if close_db:
            db.close()

def _get_default_features(latitude: float, longitude: float, timestamp: datetime) -> Dict[str, Any]:
    """
    Return a default set of features when data cannot be retrieved.
    """
    features = {}
    features.update(get_time_features(timestamp))
    features.update(get_location_features(latitude, longitude))
    # Default values for other features
    features.update({
        "crime_density_weighted": 0.0,
        "crime_high_count": 0,
        "crime_medium_count": 0,
        "crime_low_count": 0,
        "crime_weighted_severity_avg": 0.0,
        "lighting_avg": 0.5,
        "low_lighting_count": 0,
        "total_safety_nodes": 0,
        "crowd_density_avg": 0.5,
        "sparse_crowd_count": 0,
        "total_safety_nodes_2": 0,  # Note: duplicated in original, keeping for compatibility
        "report_weighted_recent": 0.0,
        "report_weighted_severity": 0.0
    })
    return features

