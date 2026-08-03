"""
Nearest Neighbor Queries for SafeRoute AI Graph
Provides high-level functions for finding nearest nodes and edges,
radius searches, and bounding box queries using the spatial index.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from .spatial_index import get_spatial_index


def nearest_node(session: Session, latitude: float, longitude: float) -> Optional:
    """
    Find the nearest graph node to the given coordinates.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees

    Returns:
        Nearest GraphNode object or None if no nodes exist
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nearest_node(latitude, longitude)


def nearest_edge(session: Session, latitude: float, longitude: float) -> Optional:
    """
    Find the nearest graph edge to the given coordinates.
    Distance is calculated to the edge's midpoint.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees

    Returns:
        Nearest GraphEdge object or None if no edges exist
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nearest_edge(latitude, longitude)


def nearest_nodes(session: Session, latitude: float, longitude: float, k: int = 1) -> List:
    """
    Find the k nearest graph nodes to the given coordinates.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        k: Number of nearest neighbors to return (default: 1)

    Returns:
        List of GraphNode objects sorted by distance (closest first)
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nearest_nodes(latitude, longitude, k)


def nearest_edges(session: Session, latitude: float, longitude: float, k: int = 1) -> List:
    """
    Find the k nearest graph edges to the given coordinates.
    Distance is calculated to the edge's midpoint.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        k: Number of nearest neighbors to return (default: 1)

    Returns:
        List of GraphEdge objects sorted by distance (closest first)
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nearest_edges(latitude, longitude, k)


def nodes_within_radius(session: Session, latitude: float, longitude: float, radius_meters: float) -> List:
    """
    Find all nodes within the given radius (in meters) of the coordinates.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        radius_meters: Search radius in meters

    Returns:
        List of GraphNode objects within the radius
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nodes_within_radius(latitude, longitude, radius_meters)


def edges_within_radius(session: Session, latitude: float, longitude: float, radius_meters: float) -> List:
    """
    Find all edges whose midpoint is within the given radius (in meters) of the coordinates.

    Args:
        session: SQLAlchemy database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        radius_meters: Search radius in meters

    Returns:
        List of GraphEdge objects within the radius
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.edges_within_radius(latitude, longitude, radius_meters)


def nodes_in_bbox(session: Session, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List:
    """
    Find all nodes within the bounding box.

    Args:
        session: SQLAlchemy database session
        min_lat: Minimum latitude
        min_lon: Minimum longitude
        max_lat: Maximum latitude
        max_lon: Maximum longitude

    Returns:
        List of GraphNode objects within the bounding box
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.nodes_in_bbox(min_lat, min_lon, max_lat, max_lon)


def edges_in_bbox(session: Session, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List:
    """
    Find all edges whose midpoint is within the bounding box.

    Args:
        session: SQLAlchemy database session
        min_lat: Minimum latitude
        min_lon: Minimum longitude
        max_lat: Maximum latitude
        max_lon: Maximum longitude

    Returns:
        List of GraphEdge objects within the bounding box
    """
    spatial_index = get_spatial_index(session)
    return spatial_index.edges_in_bbox(min_lat, min_lon, max_lat, max_lon)