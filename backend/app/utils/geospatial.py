"""
Geospatial utility functions for SafeRoute AI.
Centralizes common geospatial calculations to avoid duplication.
"""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of point 1 in decimal degrees
        lat2, lon2: Latitude and longitude of point 2 in decimal degrees

    Returns:
        Distance in meters
    """
    # Earth's radius in meters
    R = 6371000

    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def meters_to_degrees_latitude(meters: float) -> float:
    """
    Convert meters to degrees latitude.

    Args:
        meters: Distance in meters

    Returns:
        Equivalent degrees latitude
    """
    # 1 degree latitude ≈ 111,000 meters
    return meters / 111000.0


def meters_to_degrees_longitude(meters: float, latitude: float) -> float:
    """
    Convert meters to degrees longitude at a given latitude.

    Args:
        meters: Distance in meters
        latitude: Latitude in degrees (for cosine correction)

    Returns:
        Equivalent degrees longitude
    """
    # 1 degree longitude ≈ 111,000 * cos(latitude) meters
    return meters / (111000.0 * math.cos(math.radians(latitude)))


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing from point 1 to point 2.

    Args:
        lat1, lon1: Latitude and longitude of point 1 in decimal degrees
        lat2, lon2: Latitude and longitude of point 2 in decimal degrees

    Returns:
        Bearing in degrees (0-360, where 0 is North)
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)

    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)

    return (math.degrees(math.atan2(y, x)) + 360) % 360