"""
Spatial Index for SafeRoute AI Graph
Provides spatial querying capabilities for graph nodes and edges using database indexes.
Designed for production-scale datasets with lazy loading and caching support.
"""

import heapq
import math
from typing import Any, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.models import GraphEdge, GraphNode
from app.utils.geospatial import haversine_distance


class SpatialIndex:
    """
    Abstract base class for spatial indexing.
    Provides interface for spatial queries on graph nodes and edges.
    """

    def __init__(self, session: Session):
        self.session = session

    def nearest_node(self, latitude: float, longitude: float) -> Optional[GraphNode]:
        """
        Find the nearest graph node to the given coordinates.
        Returns None if no nodes exist.
        """
        raise NotImplementedError

    def nearest_edge(self, latitude: float, longitude: float) -> Optional[GraphEdge]:
        """
        Find the nearest graph edge to the given coordinates.
        Distance is calculated to the edge's midpoint.
        Returns None if no edges exist.
        """
        raise NotImplementedError

    def nearest_nodes(self, latitude: float, longitude: float, k: int = 1) -> List[GraphNode]:
        """
        Find the k nearest graph nodes to the given coordinates.
        Returns list of nodes sorted by distance (closest first).
        """
        raise NotImplementedError

    def nearest_edges(self, latitude: float, longitude: float, k: int = 1) -> List[GraphEdge]:
        """
        Find the k nearest graph edges to the given coordinates.
        Distance is calculated to the edge's midpoint.
        Returns list of edges sorted by distance (closest first).
        """
        raise NotImplementedError

    def nodes_with_in_radius(self, latitude: float, longitude: float, radius_meters: float) -> List[GraphNode]:
        """
        Find all nodes within the given radius (in meters) of the coordinates.
        Uses Haversine distance for accurate spherical distance.
        """
        raise NotImplementedError

    def edges_within_radius(self, latitude: float, longitude: float, radius_meters: float) -> List[GraphEdge]:
        """
        Find all edges whose midpoint is within the given radius (in meters) of the coordinates.
        """
        raise NotImplementedError

    def nodes_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphNode]:
        """
        Find all nodes within the bounding box.
        """
        raise NotImplementedError

    def edges_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphEdge]:
        """
        Find all edges whose midpoint is within the bounding box.
        """
        raise NotImplementedError

    
    def _get_bounding_box_for_radius(self, latitude: float, longitude: float, radius_meters: float) -> tuple:
        """
        Calculate bounding box that contains the circle of given radius.
        Returns (min_lat, min_lon, max_lat, max_lon).
        """
        # Earth's radius in meters
        R = 6371000
        # Angular distance in radians
        angular_distance = radius_meters / R

        # Latitude bounds
        lat_rad = math.radians(latitude)
        delta_lat = angular_distance
        min_lat = math.degrees(lat_rad - delta_lat)
        max_lat = math.degrees(lat_rad + delta_lat)

        # Longitude bounds (adjust for latitude)
        if math.cos(lat_rad) != 0:
            delta_lon = math.asin(math.sin(angular_distance) / math.cos(lat_rad))
        else:
            # At poles, longitude doesn't matter
            delta_lon = math.pi / 2
        min_lon = math.degrees(math.radians(longitude) - delta_lon)
        max_lon = math.degrees(math.radians(longitude) + delta_lon)

        return min_lat, min_lon, max_lat, max_lon


class DatabaseSpatialIndex(SpatialIndex):
    """
    Spatial index implementation that uses database indexes for filtering
    and in-memory processing for distance calculations.
    Designed to work efficiently with large datasets by leveraging
    database indexes for initial filtering.
    """

    def __init__(self, session: Session):
        super().__init__(session)
        # Cache for recent queries to avoid repeated DB hits for same area
        self._bbox_cache: dict = {}
        self._max_cache_size = 100

    def _get_nodes_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphNode]:
        """
        Get nodes within bounding box using database index.
        Uses cached results if available.
        """
        # Create cache key
        key = ('nodes', round(min_lat, 5), round(min_lon, 5), round(max_lat, 5), round(max_lon, 5))
        if key in self._bbox_cache:
            return self._bbox_cache[key]

        # Query database using indexed columns
        query = self.session.query(GraphNode).filter(
            and_(
                GraphNode.latitude >= min_lat,
                GraphNode.latitude <= max_lat,
                GraphNode.longitude >= min_lon,
                GraphNode.longitude <= max_lon
            )
        )
        nodes = query.all()

        # Cache result
        self._cache_put(key, nodes)
        return nodes

    def _get_edges_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphEdge]:
        """
        Get edges within bounding box using database index on midpoint.
        Uses cached results if available.
        """
        # Create cache key
        key = ('edges', round(min_lat, 5), round(min_lon, 5), round(max_lat, 5), round(max_lon, 5))
        if key in self._bbox_cache:
            return self._bbox_cache[key]

        # Query database using indexed midpoint columns
        query = self.session.query(GraphEdge).filter(
            and_(
                GraphEdge.mid_lat >= min_lat,
                GraphEdge.mid_lat <= max_lat,
                GraphEdge.mid_lon >= min_lon,
                GraphEdge.mid_lon <= max_lon
            )
        )
        edges = query.all()

        # Cache result
        self._cache_put(key, edges)
        return edges

    def _cache_put(self, key: tuple, value: Any) -> None:
        """Add item to cache, removing oldest if cache too large."""
        if len(self._bbox_cache) >= self._max_cache_size:
            # Remove first item (FIFO)
            first_key = next(iter(self._bbox_cache))
            del self._bbox_cache[first_key]
        self._bbox_cache[key] = value

    def clear_cache(self) -> None:
        """Clear the bounding box cache."""
        self._bbox_cache.clear()

    def nearest_node(self, latitude: float, longitude: float) -> Optional[GraphNode]:
        """Find the nearest node using expanding square search."""
        nodes = self.nearest_nodes(latitude, longitude, k=1)
        return nodes[0] if nodes else None

    def nearest_edge(self, latitude: float, longitude: float) -> Optional[GraphEdge]:
        """Find the nearest edge using expanding square search."""
        edges = self.nearest_edges(latitude, longitude, k=1)
        return edges[0] if edges else None

    def nearest_nodes(self, latitude: float, longitude: float, k: int = 1) -> List[GraphNode]:
        """
        Find k nearest nodes using expanding square search.
        Algorithm:
        1. Start with small bounding box around point
        2. Get nodes in box from database
        3. Calculate exact distances and maintain heap of k nearest
        4. If fewer than k nodes found, expand box and repeat
        5. Stop when we have k nodes and the nearest is closer than the box edge
        """
        if k <= 0:
            return []

        # Check if any nodes exist (LIMIT 1 is far cheaper than COUNT(*),
        # which scans the whole table; the result is identical - either
        # there are nodes to search or there are not).
        if self.session.query(GraphNode.id).limit(1).first() is None:
            return []

        # Initial search radius (in meters)
        radius = 100.0  # Start with 100m
        max_radius = 50000.0  # Maximum 50km to prevent infinite loop

        # Convert to degrees for initial bbox
        lat_delta = radius / 111000.0  # Approximate meters per degree latitude
        lon_delta = radius / (111000.0 * math.cos(math.radians(latitude)))

        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta
        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta

        # Max heap for k nearest (store negative distance for max heap)
        # Each entry: (-distance, node)
        max_heap: List[tuple] = []

        # Keep track of nodes we've already seen to avoid duplicates
        seen_node_ids = set()

        while radius <= max_radius:
            # Get nodes in current bounding box
            nodes = self._get_nodes_in_bbox(min_lat, min_lon, max_lat, max_lon)

            # Process each node
            for node in nodes:
                # Skip if we've already seen this node
                if node.id in seen_node_ids:
                    continue
                seen_node_ids.add(node.id)

                distance = haversine_distance(latitude, longitude, node.latitude, node.longitude)
                # If we have less than k items, add to heap
                if len(max_heap) < k:
                    heapq.heappush(max_heap, (-distance, node))
                else:
                    # If this node is closer than the farthest in heap, replace
                    if distance < -max_heap[0][0]:
                        heapq.heapreplace(max_heap, (-distance, node))

            # If we have k nodes, check if we can stop
            if len(max_heap) == k:
                # The farthest in our heap
                farthest_distance = -max_heap[0][0]
                # Calculate how far the current box extends from center
                # Corners are farthest points
                corner_distance = haversine_distance(
                    latitude, longitude, max_lat, max_lon
                )
                # If the farthest we've found is closer than the corner,
                # then we couldn't find anything closer outside the box
                if farthest_distance < corner_distance:
                    break

            # Expand search radius
            radius *= 2.0
            lat_delta = radius / 111000.0
            lon_delta = radius / (111000.0 * math.cos(math.radians(latitude)))
            min_lat = latitude - lat_delta
            max_lat = latitude + lat_delta
            min_lon = longitude - lon_delta
            max_lon = longitude + lon_delta

        # Extract nodes from heap and sort by distance (closest first)
        nodes = [node for (neg_dist, node) in max_heap]
        nodes.sort(key=lambda n: haversine_distance(latitude, longitude, n.latitude, n.longitude))
        return nodes[:k]

    def nearest_edges(self, latitude: float, longitude: float, k: int = 1) -> List[GraphEdge]:
        """
        Find k nearest edges using expanding square search.
        Distance calculated to edge midpoint.
        """
        if k <= 0:
            return []

        # Check if any edges exist (LIMIT 1 existence check instead of
        # COUNT(*) - see nearest_nodes).
        if self.session.query(GraphEdge.id).limit(1).first() is None:
            return []

        # Initial search radius (in meters)
        radius = 100.0
        max_radius = 50000.0

        # Convert to degrees for initial bbox
        lat_delta = radius / 111000.0
        lon_delta = radius / (111000.0 * math.cos(math.radians(latitude)))

        min_lat = latitude - lat_delta
        max_lat = latitude + lat_delta
        min_lon = longitude - lon_delta
        max_lon = longitude + lon_delta

        # Max heap for k nearest (store negative distance for max heap)
        # Each entry: (-distance, edge)
        max_heap: List[tuple] = []

        while radius <= max_radius:
            # Get edges in current bounding box
            edges = self._get_edges_in_bbox(min_lat, min_lon, max_lat, max_lon)

            # Process each edge
            for edge in edges:
                distance = haversine_distance(
                    latitude, longitude, edge.mid_lat, edge.mid_lon
                )
                # If we have less than k items, add to heap
                if len(max_heap) < k:
                    heapq.heappush(max_heap, (-distance, edge))
                else:
                    # If this edge is closer than the farthest in heap, replace
                    if distance < -max_heap[0][0]:
                        heapq.heapreplace(max_heap, (-distance, edge))

            # If we have k edges, check if we can stop
            if len(max_heap) == k:
                # The farthest in our heap
                farthest_distance = -max_heap[0][0]
                # Calculate how far the current box extends from center
                # Corners are farthest points
                corner_distance = haversine_distance(
                    latitude, longitude, max_lat, max_lon
                )
                # If the farthest we've found is closer than the corner,
                # then we couldn't find anything closer outside the box
                if farthest_distance < corner_distance:
                    break

            # Expand search radius
            radius *= 2.0
            lat_delta = radius / 111000.0
            lon_delta = radius / (111000.0 * math.cos(math.radians(latitude)))
            min_lat = latitude - lat_delta
            max_lat = latitude + lat_delta
            min_lon = longitude - lon_delta
            max_lon = longitude + lon_delta

        # Extract edges from heap and sort by distance (closest first)
        edges = [edge for (neg_dist, edge) in max_heap]
        edges.sort(key=lambda e: haversine_distance(latitude, longitude, e.mid_lat, e.mid_lon))
        return edges[:k]

    def nodes_within_radius(self, latitude: float, longitude: float, radius_meters: float) -> List[GraphNode]:
        """
        Find all nodes within the given radius (in meters) of the coordinates.
        Uses Haversine distance for accurate spherical distance.
        """
        if radius_meters < 0:
            return []

        # Get bounding box that contains the circle
        min_lat, min_lon, max_lat, max_lon = self._get_bounding_box_for_radius(
            latitude, longitude, radius_meters
        )

        # Get candidate nodes from database
        candidates = self._get_nodes_in_bbox(min_lat, min_lon, max_lat, max_lon)

        # Filter by exact distance
        result = []
        for node in candidates:
            distance = haversine_distance(
                latitude, longitude, node.latitude, node.longitude
            )
            if distance <= radius_meters:
                result.append(node)

        return result

    def edges_within_radius(self, latitude: float, longitude: float, radius_meters: float) -> List[GraphEdge]:
        """
        Find all edges whose midpoint is within the given radius (in meters) of the coordinates.
        """
        if radius_meters < 0:
            return []

        # Get bounding box that contains the circle
        min_lat, min_lon, max_lat, max_lon = self._get_bounding_box_for_radius(
            latitude, longitude, radius_meters
        )

        # Get candidate edges from database
        candidates = self._get_edges_in_bbox(min_lat, min_lon, max_lat, max_lon)

        # Filter by exact distance
        result = []
        for edge in candidates:
            distance = haversine_distance(
                latitude, longitude, edge.mid_lat, edge.mid_lon
            )
            if distance <= radius_meters:
                result.append(edge)

        return result

    def nodes_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphNode]:
        """
        Find all nodes within the bounding box.
        """
        return self._get_nodes_in_bbox(min_lat, min_lon, max_lat, max_lon)

    def edges_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[GraphEdge]:
        """
        Find all edges whose midpoint is within the bounding box.
        """
        return self._get_edges_in_bbox(min_lat, min_lon, max_lat, max_lon)


def get_spatial_index(session: Session) -> SpatialIndex:
    """
    Factory function to get a spatial index instance.
    Currently returns DatabaseSpatialIndex as the default implementation.

    Args:
        session: SQLAlchemy database session

    Returns:
        SpatialIndex instance
    """
    return DatabaseSpatialIndex(session)