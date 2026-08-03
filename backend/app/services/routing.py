# app/services/routing.py
"""
AI Safety Routing Service using A* algorithm over GIS graph.
Replaces the previous Mapbox-dependent implementation with pure GIS graph routing.
Maintains exact same API contract as previous implementation.
"""

import math
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.db.models import GraphNode, GraphEdge, RoadSegmentRisk
from app.graph.spatial_index import get_spatial_index
from app.graph.nearest import nearest_node
from app.graph.cost_engine import RouteCostEngine
from app.schemas.routing import Coordinate
from app.core.config import settings

logger = logging.getLogger(__name__)

class SafetyRoutingService:
    """
    AI Safety Routing Service using A* algorithm over GIS graph.
    Replaces the previous Mapbox-dependent implementation.
    Maintains exact same API contract.
    Cost = Distance + Safety Penalty (now using actual graph edge costs from RouteCostEngine)
    """

    def __init__(self, db: Session):
        """
        Initialize the GIS-based routing service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.spatial_index = get_spatial_index(db)
        self.cost_engine = RouteCostEngine(db)
        # Lazily-loaded RoadSegmentRisk records, constant for the lifetime of
        # one request. _calculate_safety_score is called once per route
        # segment (twice per request), so loading these once avoids a DB
        # query per segment (same per-instance caching the cost engine uses).
        self._risk_records: Optional[list] = None

    def _validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate if coordinates are within India's bounding box.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            bool: True if coordinates are within India's bounds, False otherwise
        """
        # RT-6: India bounding box for coordinate validation (approximate)
        INDIA_BOUNDS = {
            "min_lat": 6.0,   # Southern tip (Kanyakumari)
            "max_lat": 37.0,  # Northern border (Jammu & Kashmir)
            "min_lon": 68.0,  # Western border (Gujarat)
            "max_lon": 97.5,  # Eastern border (Arunachal Pradesh)
        }

        return (INDIA_BOUNDS["min_lat"] <= latitude <= INDIA_BOUNDS["max_lat"] and
                INDIA_BOUNDS["min_lon"] <= longitude <= INDIA_BOUNDS["max_lon"])

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates in meters using Haversine formula.
        Used for heuristic in A* algorithm.

        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate

        Returns:
            Distance in meters
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # Earth radius in meters
        return c * r

    def _find_nearest_node(self, latitude: float, longitude: float) -> Optional[GraphNode]:
        """
        Find the nearest graph node to the given coordinates using SpatialIndex.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Nearest GraphNode or None if no nodes exist
        """
        return nearest_node(self.db, latitude, longitude)

    def _get_edge_cost(self, edge_id: int) -> float:
        """
        Get the traversal cost for a graph edge using RouteCostEngine.
        This implements the RoutingService → RouteCostEngine link in the required flow.

        Args:
            edge_id: ID of the GraphEdge

        Returns:
            Traversal cost for the edge
        """
        try:
            cost_output = self.cost_engine.compute_edge_cost(edge_id)
            return cost_output.total_cost
        except Exception as e:
            logger.warning(f"Failed to compute cost for edge {edge_id}: {e}")
            # Fallback to distance-based cost if cost engine fails.
            # Session.get() returns the identity-mapped edge (already loaded
            # by _get_neighbors) without issuing another SELECT.
            edge = self.db.get(GraphEdge, edge_id)
            if edge:
                return float(edge.length)  # Fallback to length
            raise

    def _get_neighbors(self, node: GraphNode) -> List[tuple]:
        """
        Get neighboring nodes and edge costs for a given node.

        Args:
            node: Current GraphNode

        Returns:
            List of tuples (neighbor_node, cost, edge_id, mid_lat, mid_lon)
            where mid_lat/mid_lon is the geographic midpoint of the edge,
            used for risk lookup without extra DB queries.
        """
        neighbors = []

        # Get edges where this node is the source
        edges_out = self.db.query(GraphEdge).filter(
            GraphEdge.source_node_id == node.id
        ).all()

        # Get edges where this node is the destination (for bidirectional edges)
        edges_in = self.db.query(GraphEdge).filter(
            GraphEdge.dest_node_id == node.id
        ).all()

        # Batch-load all neighbor nodes with a single IN query instead of
        # issuing one GraphNode SELECT per edge (N+1). Chunk the IN clause
        # to stay under SQLite's ~999 bound-variable limit for very
        # high-degree nodes.
        needed_ids = {
            edge.dest_node_id for edge in edges_out
        } | {
            edge.source_node_id for edge in edges_in
        }
        node_map: Dict[int, GraphNode] = {}
        if needed_ids:
            ids_list = sorted(needed_ids)
            for i in range(0, len(ids_list), 500):
                chunk = ids_list[i:i + 500]
                nodes = self.db.query(GraphNode).filter(
                    GraphNode.id.in_(chunk)
                ).all()
                node_map.update({n.id: n for n in nodes})

        # Process outgoing edges (preserve original iteration order)
        for edge in edges_out:
            neighbor = node_map.get(edge.dest_node_id)
            if neighbor:
                try:
                    cost = self._get_edge_cost(edge.id)
                    # Outgoing edge: from = current node, to = neighbor
                    mid_lat = (node.latitude + neighbor.latitude) / 2.0
                    mid_lon = (node.longitude + neighbor.longitude) / 2.0
                    neighbors.append((neighbor, cost, edge.id, mid_lat, mid_lon))
                except Exception as e:
                    logger.warning(f"Skipping edge {edge.id} due to cost calculation error: {e}")

        # Process incoming edges
        for edge in edges_in:
            neighbor = node_map.get(edge.source_node_id)
            if neighbor:
                try:
                    cost = self._get_edge_cost(edge.id)
                    # Incoming edge: from = neighbor, to = current node
                    mid_lat = (neighbor.latitude + node.latitude) / 2.0
                    mid_lon = (neighbor.longitude + node.longitude) / 2.0
                    neighbors.append((neighbor, cost, edge.id, mid_lat, mid_lon))
                except Exception as e:
                    logger.warning(f"Skipping edge {edge.id} due to cost calculation error: {e}")

        return neighbors

    def _reconstruct_path(self, came_from: dict, current: int) -> list:
        """
        Reconstruct path from came_from dictionary.

        Args:
            came_from: Dictionary mapping node_id to predecessor node_id
            current: Current node ID

        Returns:
            List of node IDs representing the path from start to current
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _path_to_coordinates(self, path: list) -> list:
        """
        Convert a path of GraphNode objects to list of Coordinate objects.

        Args:
            path: List of GraphNode objects

        Returns:
            List of Coordinate objects
        """
        coordinates = []
        for node in path:
            coordinates.append(Coordinate(latitude=node.latitude, longitude=node.longitude))
        return coordinates

    def _calculate_route_metrics(self, coords: list) -> tuple:
        """
        Calculate total distance, average safety score, and segments for a route.

        Args:
            coords: List of Coordinate objects representing the route

        Returns:
            Tuple of (total_distance_meters, average_safety_score, segments_list)
        """
        if len(coords) < 2:
            return 0.0, 0.0, []

        total_distance = 0.0
        safety_scores = []
        segments = []

        for i in range(len(coords) - 1):
            from_coord = coords[i]
            to_coord = coords[i + 1]

            # Calculate distance
            distance = self._haversine_distance(
                from_coord.latitude, from_coord.longitude,
                to_coord.latitude, to_coord.longitude
            )
            total_distance += distance

            # Calculate midpoint for safety scoring
            mid_lat = (from_coord.latitude + to_coord.latitude) / 2.0
            mid_lon = (from_coord.longitude + to_coord.longitude) / 2.0

            # Calculate safety score based on actual risk data from nearby edges/nodes
            safety_score = self._calculate_safety_score(mid_lat, mid_lon)
            safety_scores.append(safety_score)

            # Create segment info
            segments.append({
                "from_coord": {"latitude": from_coord.latitude, "longitude": from_coord.longitude},
                "to_coord": {"latitude": to_coord.latitude, "longitude": to_coord.longitude},
                "distance": distance,
                "safety_score": safety_score,
                "penalty": 0.0  # Penalty is now incorporated into edge costs via RouteCostEngine
            })

        avg_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 0.5
        return total_distance, avg_safety, segments

    def _calculate_safety_score(self, latitude: float, longitude: float) -> float:
        """
        Calculate safety score for a point based on nearby production risk data.

        Queries RoadSegmentRisk records near the point (pre-computed from
        accident/black-spot data) and converts the closest record's risk_score
        to a safety score using the same inversion the ML training pipeline
        uses (safety_score = 1.0 - risk_score). When no risk record is within
        the configured search radius, returns the neutral 0.8 default.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Safety score between 0.0 and 1.0 (higher is safer)
        """
        closest = self._nearest_risk_record(latitude, longitude)

        if closest is None or closest.risk_score is None:
            return 0.8  # No production risk data near this point
        return max(0.0, min(1.0, 1.0 - closest.risk_score))

    def _nearest_risk_record(self, latitude: float, longitude: float) -> Optional[RoadSegmentRisk]:
        """
        Find the RoadSegmentRisk record nearest to a coordinate.

        Uses the pre-loaded ``_risk_records`` list (loaded once per request)
        and a simple bounding-box prefilter followed by exact haversine
        distance, matching the lookups used for safety scoring. This avoids a
        per-edge DB query (N+1) during safe-mode A*.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            The closest RoadSegmentRisk within SEGMENT_RISK_SEARCH_RADIUS_M,
            or None when no record is within range.
        """
        radius_m = getattr(settings, 'SEGMENT_RISK_SEARCH_RADIUS_M', 200.0)
        lat_delta = radius_m / 111000.0
        lon_delta = radius_m / (111000.0 * max(0.01, math.cos(math.radians(latitude))))

        if self._risk_records is None:
            self._risk_records = self.db.query(RoadSegmentRisk).all()

        closest = None
        closest_dist = None
        for r in self._risk_records:
            if not (latitude - lat_delta <= r.start_latitude <= latitude + lat_delta):
                continue
            if not (longitude - lon_delta <= r.start_longitude <= longitude + lon_delta):
                continue
            d = self._haversine_distance(latitude, longitude, r.start_latitude, r.start_longitude)
            if d > radius_m:
                continue
            if closest is None or d < closest_dist:
                closest = r
                closest_dist = d
        return closest

    def _astar_search(self, start_node_id: int, goal_node_id: int,
                     weight_mode: str = 'balanced') -> list:
        """
        Perform A* search to find path between two nodes.
        Implements the A* over GraphEdge graph component of the required flow.

        Args:
            start_node_id: ID of start node
            goal_node_id: ID of goal node
            weight_mode: 'fast' for distance-weighted, 'safe' for safety-weighted, 'balanced' for mix

        Returns:
            List of GraphNode objects representing the path from start to goal
        """
        # Get start and goal nodes
        start_node = self.db.query(GraphNode).filter(GraphNode.id == start_node_id).first()
        goal_node = self.db.query(GraphNode).filter(GraphNode.id == goal_node_id).first()

        if not start_node or not goal_node:
            raise ValueError("Start or goal node not found")

        # Node cache: avoids re-SELECTing GraphNode rows that _get_neighbors
        # already loaded. Populated lazily; only used to skip redundant queries,
        # so the visited set and path are identical to before.
        node_cache: Dict[int, GraphNode] = {
            start_node.id: start_node,
            goal_node.id: goal_node,
        }

        # A* data structures
        import heapq
        open_set = []  # Priority queue of (f_score, node_id)
        heapq.heappush(open_set, (0, start_node_id))

        came_from = {}  # node_id -> parent_node_id
        g_score = {start_node_id: 0}  # Cost from start to node
        f_score = {start_node_id: self._heuristic(start_node, goal_node)}  # Estimated total cost

        # Set to track visited nodes
        closed_set = set()

        # Safety limits to prevent infinite loops
        nodes_explored = 0
        max_nodes_to_explore = 10000

        while open_set and nodes_explored < max_nodes_to_explore:
            # Get node with lowest f_score
            current_f, current_id = heapq.heappop(open_set)

            # If we've already processed this node with a better f_score, skip
            if current_id in closed_set:
                continue

            # Check if we reached the goal
            if current_id == goal_node_id:
                # Reconstruct and return path
                path_ids = self._reconstruct_path(came_from, current_id)
                path_nodes = []
                for node_id in path_ids:
                    node = node_cache.get(node_id)
                    if node is None:
                        node = self.db.query(GraphNode).filter(GraphNode.id == node_id).first()
                        if node:
                            node_cache[node_id] = node
                    if node:
                        path_nodes.append(node)
                return path_nodes

            # Mark current node as visited
            closed_set.add(current_id)
            nodes_explored += 1

            # Get current node (already loaded when it was discovered)
            current_node = node_cache.get(current_id)
            if current_node is None:
                current_node = self.db.query(GraphNode).filter(GraphNode.id == current_id).first()
                if current_node:
                    node_cache[current_id] = current_node
            if not current_node:
                continue

            # Get neighbors
            neighbors = self._get_neighbors(current_node)

            for neighbor, edge_cost, edge_id, mid_lat, mid_lon in neighbors:
                # Cache neighbor nodes so the goal-reconstruction and future
                # pops don't re-query them.
                node_cache.setdefault(neighbor.id, neighbor)

                if neighbor.id in closed_set:
                    continue

                # The cost accumulated along the path depends on weight_mode:
                # safe mode accumulates safety cost so the priority queue
                # orders by total path safety, not the single incoming edge.
                if weight_mode == 'safe':
                    edge_increment = self._get_safety_cost(edge_id, mid_lat, mid_lon)
                else:
                    edge_increment = edge_cost

                # Calculate tentative g_score
                tentative_g_score = g_score[current_id] + edge_increment

                # If this path to neighbor is better than any previous one
                if neighbor.id not in g_score or tentative_g_score < g_score[neighbor.id]:
                    # This path is better, record it
                    came_from[neighbor.id] = current_id
                    g_score[neighbor.id] = tentative_g_score

                    # Calculate heuristic using the already-loaded neighbor
                    heuristic = self._heuristic(neighbor, goal_node)

                    # Apply weight_mode to determine f_score
                    if weight_mode == 'fast':
                        # Pure distance optimization - use edge cost as-is
                        f_score[neighbor.id] = tentative_g_score + (heuristic * 0.5)  # Lower weight on heuristic
                    elif weight_mode == 'safe':
                        # Safety optimization - accumulated safety cost along
                        # the whole path plus the heuristic, matching how the
                        # fast/balanced modes accumulate their g_score.
                        f_score[neighbor.id] = tentative_g_score + (heuristic * 1.0)  # Higher weight on heuristic for safety
                    else:  # 'balanced'
                        # Balance between distance and safety
                        f_score[neighbor.id] = tentative_g_score + (heuristic * 0.8)

                    heapq.heappush(open_set, (f_score[neighbor.id], neighbor.id))

        # If we exhaust the open set without finding the goal, raise the same
        # error the rest of the project uses for unreachable destinations
        # (ValueError -> HTTP 400 VALIDATION_ERROR in app/api/v1/routing.py).
        # A straight-line path from start to goal would follow no road, so it
        # must not be returned as a route.
        logger.warning(f"A* search failed to find path from {start_node_id} to {goal_node_id} "
                      f"after exploring {nodes_explored} nodes.")
        raise ValueError("No path found between the source and destination")

    def _heuristic(self, node1: GraphNode, node2: GraphNode) -> float:
        """
        Calculate heuristic distance between two nodes (haversine distance).

        Args:
            node1: First node
            node2: Second node

        Returns:
            Estimated distance in meters
        """
        return self._haversine_distance(
            node1.latitude, node1.longitude,
            node2.latitude, node2.longitude
        )

    def _get_safety_cost(self, edge_id: int, mid_lat: float, mid_lon: float) -> float:
        """
        Get safety-based cost for an edge (lower = safer).
        Used for safety-weighted A* search.

        The risk lookup is keyed by the edge's physical location (midpoint)
        rather than by assuming ``RoadSegmentRisk.id`` equals the graph edge
        id — those two sequences are unrelated, so the old
        ``RoadSegmentRisk.id == edge_id`` match was coincidental. Uses the
        pre-loaded ``_risk_records`` list, so this is O(risk_records) with no
        additional DB queries (no N+1).

        Args:
            edge_id: ID of the GraphEdge (kept for the fallback path)
            mid_lat: Latitude of the edge midpoint
            mid_lon: Longitude of the edge midpoint

        Returns:
            Safety cost (lower is safer)
        """
        try:
            risk_data = self._nearest_risk_record(mid_lat, mid_lon)

            if risk_data and risk_data.risk_score is not None:
                # Convert risk_score (0-1, higher=more risky) to safety cost
                # For safety routing: lower cost = safer route
                # risk_score=0.0 (safe) -> low cost, risk_score=1.0 (dangerous) -> high cost
                safety_cost = risk_data.risk_score * 50.0  # Scale directly
                return max(1.0, safety_cost)  # Ensure minimum cost
            else:
                # No risk data available - assume moderately safe
                return 25.0  # Moderate safety cost
        except Exception:
            # Fallback to distance-based cost. The edge was already loaded
            # into the session identity map by _get_neighbors, so
            # Session.get() avoids a redundant SELECT.
            edge = self.db.get(GraphEdge, edge_id)
            if edge:
                return float(edge.length)
            return 25.0  # Default fallback

    def find_safest_route(self, source: Coordinate, destination: Coordinate,
                         safety_weight: float = None) -> dict:
        """
        Find the safest and fastest routes between source and destination.
        Implements the complete required integration flow:
        RoutingService → SpatialIndex → Nearest GraphNode lookup → A* over GraphEdge →
        RouteCostEngine → RoadSegment → Return existing RouteResponse model metadata

        Args:
            source: Starting coordinates
            destination: Ending coordinates
            safety_weight: Weight for safety vs distance (0.0 = fastest, 1.0 = safest)

        Returns:
            Dictionary containing safest_route, fastest_route, distances, safety scores, and segments

        Raises:
            ValueError: If coordinates are invalid or no path found
        """
        # Use default safety weight if not provided
        if safety_weight is None:
            safety_weight = getattr(settings, 'DEFAULT_SAFETY_WEIGHT', 0.7)

        # Validate coordinates (RT-6: India bounding box check)
        if not self._validate_coordinates(source.latitude, source.longitude):
            raise ValueError(f"Source coordinates ({source.latitude}, {source.longitude}) are outside India bounds")
        if not self._validate_coordinates(destination.latitude, destination.longitude):
            raise ValueError(f"Destination coordinates ({destination.latitude}, {destination.longitude}) are outside India bounds")

        # Check if source and destination are the same
        if (abs(source.latitude - destination.latitude) < 1e-6 and
            abs(source.longitude - destination.longitude) < 1e-6):
            raise ValueError("Source and destination must be different locations")

        logger.info(f"Finding route from ({source.latitude}, {source.longitude}) to "
                   f"({destination.latitude}, {destination.longitude}) with safety_weight={safety_weight}")

        # Step 1: RoutingService → SpatialIndex → Nearest GraphNode lookup
        start_node = self._find_nearest_node(source.latitude, source.longitude)
        end_node = self._find_nearest_node(destination.latitude, destination.longitude)

        if not start_node:
            raise ValueError("Could not find a graph node near the source location")
        if not end_node:
            raise ValueError("Could not find a graph node near the destination location")

        logger.info(f"Found start node {start_node.id} at ({start_node.latitude}, {start_node.longitude})")
        logger.info(f"Found end node {end_node.id} at ({end_node.latitude}, {end_node.longitude})")

        # If start and end nodes are the same, there is no real road path
        # between them. Returning a straight line from source to destination
        # would fabricate geometry that follows no road, so raise the same
        # ValueError the rest of the project uses for invalid routes
        # (ValueError -> HTTP 400 VALIDATION_ERROR in app/api/v1/routing.py).
        if start_node.id == end_node.id:
            raise ValueError("Source and destination are the same node")

        # Step 2 & 3: A* over GraphEdge graph
        # Find fastest route (distance-weighted)
        fastest_path_nodes = self._astar_search(start_node.id, end_node.id, weight_mode='fast')

        # The safest-route search honours the caller's safety/distance preference:
        # safety_weight > 0.5 -> safety-weighted A*, < 0.5 -> distance-weighted,
        # == 0.5 -> balanced. The default (0.7) maps to 'safe', so default
        # behaviour is unchanged.
        if safety_weight > 0.5:
            safest_weight_mode = 'safe'
        elif safety_weight < 0.5:
            safest_weight_mode = 'fast'
        else:
            safest_weight_mode = 'balanced'
        # Find safest route (weighted by safety_weight)
        safest_path_nodes = self._astar_search(start_node.id, end_node.id, weight_mode=safest_weight_mode)

        # Convert paths to coordinates
        fastest_path_coords = self._path_to_coordinates(fastest_path_nodes)
        safest_path_coords = self._path_to_coordinates(safest_path_nodes)

        # Calculate metrics for both routes
        # RouteCostEngine is used implicitly in _astar_search -> _get_edge_cost
        fastest_distance, fastest_safety_score, fastest_segments = self._calculate_route_metrics(fastest_path_coords)
        safest_distance, safest_safety_score, safest_segments = self._calculate_route_metrics(safest_path_coords)

        logger.info(f"Route calculation complete: "
                   f"fastest={len(fastest_path_coords)}pts, {fastest_distance:.1f}m, safety={fastest_safety_score:.3f}; "
                   f"safest={len(safest_path_coords)}pts, {safest_distance:.1f}m, safety={safest_safety_score:.3f}")

        # Return result in exact same format as original implementation
        return {
            "safest_route": safest_path_coords,
            "fastest_route": fastest_path_coords,
            "safest_distance": safest_distance,
            "fastest_distance": fastest_distance,
            "safest_safety_score": safest_safety_score,
            "fastest_safety_score": fastest_safety_score,
            "route_segments": safest_segments  # Return safest route segments as per original API
        }


# Factory function for dependency injection (maintains compatibility)
def get_routing_service(db: Session) -> SafetyRoutingService:
    """
    Factory function to create routing service instance.
    Maintains compatibility with existing dependency injection.

    Args:
        db: SQLAlchemy database session

    Returns:
        SafetyRoutingService instance
    """
    return SafetyRoutingService(db)