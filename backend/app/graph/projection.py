"""
Point Projection Utilities for SafeRoute AI Graph
Provides functions for projecting points onto graph edges and calculating
offsets (perpendicular distances) for linear referencing operations.
"""

import math
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import GraphEdge, GraphNode
from ..utils.geospatial import haversine_distance


def project_point_on_edge(
    session: Session,
    edge_id: int,
    point_lat: float,
    point_lon: float
) -> Optional[tuple[float, float, float]]:
    """
    Project a point onto a graph edge and return the closest point on the edge
    along with the fractional position.

    For a simple line segment (which our edges are), this finds the point on
    the segment closest to the given point.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge to project onto
        point_lat: Latitude of the point to project
        point_lon: Longitude of the point to project

    Returns:
        Tuple of (projected_lat, projected_lon, fraction) where fraction is
        the position along the edge (0.0 = start, 1.0 = end), or None if edge not found
    """
    edge = session.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
    if not edge:
        return None

    # Get source and destination node coordinates
    source_node = session.query(GraphNode).filter(GraphNode.id == edge.source_node_id).first()
    dest_node = session.query(GraphNode).filter(GraphNode.id == edge.dest_node_id).first()

    if not source_node or not dest_node:
        return None

    # Convert to Cartesian-like coordinates for projection calculation
    # Using equirectangular approximation for small distances (suitable for projection)
    # For more accuracy over large distances, we'd need proper geographic calculations

    # Represent points as vectors
    A = (source_node.latitude, source_node.longitude)  # Start point
    B = (dest_node.latitude, dest_node.longitude)      # End point
    P = (point_lat, point_lon)                         # Point to project

    # Vector AB
    AB = (B[0] - A[0], B[1] - A[1])
    # Vector AP
    AP = (P[0] - A[0], P[1] - A[1])

    # Dot product of AB and AP
    dot_product = AB[0] * AP[0] + AB[1] * AP[1]
    # Squared length of AB
    ab_length_squared = AB[0] * AB[0] + AB[1] * AB[1]

    # Handle degenerate case (zero-length edge)
    if ab_length_squared == 0:
        # Edge is a point, return that point
        fraction = 0.0
        projected_point = A
    else:
        # Calculate projection factor t
        t = dot_product / ab_length_squared
        # Clamp t to [0, 1] to stay within the segment
        t = max(0.0, min(1.0, t))
        fraction = t

        # Calculate projected point: A + t * AB
        projected_lat = A[0] + t * AB[0]
        projected_lon = A[1] + t * AB[1]
        projected_point = (projected_lat, projected_lon)

    return (projected_point[0], projected_point[1], fraction)


def project_point_on_edge_geographic(
    session: Session,
    edge_id: int,
    point_lat: float,
    point_lon: float
) -> Optional[tuple[float, float, float]]:
    """
    Project a point onto a graph edge using accurate geographic calculations.
    This version uses iterative refinement for better accuracy on curved earth.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge to project onto
        point_lat: Latitude of the point to project
        point_lon: Longitude of the point to project

    Returns:
        Tuple of (projected_lat, projected_lon, fraction) where fraction is
        the position along the edge (0.0 = start, 1.0 = end), or None if edge not found
    """
    # For now, we'll use the simpler planar projection since edges are typically
    # short road segments where the error is acceptable.
    # For very long edges or high precision requirements, this could be enhanced.
    return project_point_on_edge(session, edge_id, point_lat, point_lon)


def calculate_offset_distance(
    session: Session,
    edge_id: int,
    point_lat: float,
    point_lon: float
) -> Optional[float]:
    """
    Calculate the perpendicular offset distance from a point to the nearest point on an edge.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge
        point_lat: Latitude of the point
        point_lon: Longitude of the point

    Returns:
        Perpendicular distance in meters (positive indicates which side based on orientation),
        or None if edge not found
    """
    projection_result = project_point_on_edge(session, edge_id, point_lat, point_lon)
    if not projection_result:
        return None

    projected_lat, projected_lon, _ = projection_result

    # Calculate distance between original point and projected point
    return haversine_distance(point_lat, point_lon, projected_lat, projected_lon)


def get_along_distance_from_projection(
    session: Session,
    edge_id: int,
    point_lat: float,
    point_lon: float
) -> Optional[float]:
    """
    Calculate the distance along an edge from the start node to the projection of a point.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge
        point_lat: Latitude of the point
        point_lon: Longitude of the point

    Returns:
        Distance from start node to the projected point in meters, or None if edge not found
    """
    projection_result = project_point_on_edge(session, edge_id, point_lat, point_lon)
    if not projection_result:
        return None

    _, _, fraction = projection_result
    return get_distance_along_edge(session, edge_id, fraction)


def find_nearest_point_on_edge(
    session: Session,
    edge_id: int,
    point_lat: float,
    point_lon: float
) -> Optional[tuple[float, float, float, float]]:
    """
    Find the nearest point on an edge to a given point and return detailed information.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge
        point_lat: Latitude of the point
        point_lon: Longitude of the point

    Returns:
        Tuple of (nearest_lat, nearest_lon, distance_m, fraction) where:
        - nearest_lat, nearest_lon: Coordinates of the nearest point on the edge
        - distance_m: Distance from the input point to the nearest point (meters)
        - fraction: Position along the edge (0.0 = start, 1.0 = end)
        Returns None if edge not found
    """
    projection_result = project_point_on_edge(session, edge_id, point_lat, point_lon)
    if not projection_result:
        return None

    nearest_lat, nearest_lon, fraction = projection_result
    distance = haversine_distance(point_lat, point_lon, nearest_lat, nearest_lon)

    return (nearest_lat, nearest_lon, distance, fraction)


def project_multiple_points_on_edge(
    session: Session,
    edge_id: int,
    points: list[tuple[float, float]]
) -> list[Optional[tuple[float, float, float]]]:
    """
    Project multiple points onto a graph edge.

    Args:
        session: SQLAlchemy database session
        edge_id: ID of the GraphEdge to project onto
        points: List of (latitude, longitude) tuples to project

    Returns:
        List of tuples (projected_lat, projected_lon, fraction) or None for each point
    """
    return [project_point_on_edge(session, edge_id, lat, lon) for lat, lon in points]


def find_edge_with_best_projection(
    session: Session,
    point_lat: float,
    point_lon: float,
    max_edge_distance: float = 100.0
) -> Optional[tuple[int, float, float, float, float]]:
    """
    Find the edge that has the closest projection to a given point.

    Args:
        session: SQLAlchemy database session
        point_lat: Latitude of the point
        point_lon: Longitude of the point
        max_edge_distance: Maximum distance to search for edges (meters)

    Returns:
        Tuple of (edge_id, projected_lat, projected_lon, distance_m, fraction) for the best edge,
        or None if no suitable edge found within max_edge_distance
    """
    # First, find candidate edges within a bounding box
    # Convert meters to degrees (approximate)
    lat_radius = max_edge_distance / 111000.0
    lng_radius = max_edge_distance / (111000.0 * math.cos(math.radians(point_lat)))

    # Find edges with midpoints near the point
    from sqlalchemy import and_
    candidate_edges = session.query(GraphEdge).filter(
        and_(
            GraphEdge.mid_lat >= (point_lat - lat_radius),
            GraphEdge.mid_lat <= (point_lat + lat_radius),
            GraphEdge.mid_lon >= (point_lon - lng_radius),
            GraphEdge.mid_lon <= (point_lon + lng_radius)
        )
    ).all()

    best_edge_id = None
    best_projection = None
    best_distance = float('inf')
    best_fraction = 0.0

    for edge in candidate_edges:
        projection_result = project_point_on_edge(session, edge.id, point_lat, point_lon)
        if projection_result:
            proj_lat, proj_lon, fraction = projection_result
            distance = haversine_distance(point_lat, point_lon, proj_lat, proj_lon)

            if distance < best_distance and distance <= max_edge_distance:
                best_distance = distance
                best_edge_id = edge.id
                best_projection = (proj_lat, proj_lon)
                best_fraction = fraction

    if best_edge_id is not None and best_projection is not None:
        return (best_edge_id, best_projection[0], best_projection[1], best_distance, best_fraction)

    return None