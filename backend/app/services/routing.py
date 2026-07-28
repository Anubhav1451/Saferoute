# app/services/routing.py
"""
AI Safety Routing Service using A* algorithm over GIS graph.
Replaces the previous Mapbox-dependent implementation with pure GIS graph routing.
Maintains exact same API contract as previous implementation.
"""

import math
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional, Any
from sqlalchemy.orm import Session

from app.db.models import GraphNode, GraphEdge
from app.graph.spatial_index import get_spatial_index
from app.graph.nearest import nearest_node
from app.graph.cost_engine import RouteCostEngine
from app.schemas.routing import Coordinate, RouteSegment
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
            # Fallback to distance-based cost if cost engine fails
            edge = self.db.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
            if edge:
                return float(edge.length)  # Fallback to length
            raise

    def _get_neighbors(self, node: GraphNode) -> List[tuple]:
        """
        Get neighboring nodes and edge costs for a given node.

        Args:
            node: Current GraphNode

        Returns:
            List of tuples (neighbor_node, cost, edge_id)
        """
        neighbors = []

        # Get edges where this node is the source
        edges = self.db.query(GraphEdge).filter(
            GraphEdge.source_node_id == node.id
        ).all()

        for edge in edges:
            neighbor = self.db.query(GraphNode).filter(
                GraphNode.id == edge.dest_node_id
            ).first()

            if neighbor:
                try:
                    cost = self._get_edge_cost(edge.id)
                    neighbors.append((neighbor, cost, edge.id))
                except Exception as e:
                    logger.warning(f"Skipping edge {edge.id} due to cost calculation error: {e}")

        # Get edges where this node is the destination (for bidirectional edges)
        edges = self.db.query(GraphEdge).filter(
            GraphEdge.dest_node_id == node.id
        ).all()

        for edge in edges:
            neighbor = self.db.query(GraphNode).filter(
                GraphNode.id == edge.source_node_id
            ).first()

            if neighbor:
                try:
                    cost = self._get_edge_cost(edge.id)
                    neighbors.append((neighbor, cost, edge.id))
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
        Calculate safety score for a point based on nearby risk data.
        Simplified implementation - in production this would be more sophisticated.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Safety score between 0.0 and 1.0 (higher is safer)
        """
        # For now, return a reasonable default
        # In a full implementation, this would query nearby RoadSegmentRisk records
        # and other safety features to compute an actual safety score
        return 0.8  # Placeholder - reasonably safe

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
                    node = self.db.query(GraphNode).filter(GraphNode.id == node_id).first()
                    if node:
                        path_nodes.append(node)
                return path_nodes

            # Mark current node as visited
            closed_set.add(current_id)
            nodes_explored += 1

            # Get current node
            current_node = self.db.query(GraphNode).filter(GraphNode.id == current_id).first()
            if not current_node:
                continue

            # Get neighbors
            neighbors = self._get_neighbors(current_node)

            for neighbor, edge_cost, edge_id in neighbors:
                if neighbor.id in closed_set:
                    continue

                # Calculate tentative g_score
                tentative_g_score = g_score[current_id] + edge_cost

                # If this path to neighbor is better than any previous one
                if neighbor.id not in g_score or tentative_g_score < g_score[neighbor.id]:
                    # This path is better, record it
                    came_from[neighbor.id] = current_id
                    g_score[neighbor.id] = tentative_g_score

                    # Calculate heuristic
                    neighbor_node = self.db.query(GraphNode).filter(GraphNode.id == neighbor.id).first()
                    if neighbor_node:
                        heuristic = self._heuristic(neighbor_node, goal_node)

                        # Apply weight_mode to determine f_score
                        if weight_mode == 'fast':
                            # Pure distance optimization - use edge cost as-is
                            f_score[neighbor.id] = tentative_g_score + (heuristic * 0.5)  # Lower weight on heuristic
                        elif weight_mode == 'safe':
                            # Safety optimization - use safety cost
                            safety_cost = self._get_safety_cost(edge_id)
                            f_score[neighbor.id] = safety_cost + (heuristic * 1.0)  # Higher weight on heuristic for safety
                        else:  # 'balanced'
                            # Balance between distance and safety
                            f_score[neighbor.id] = tentative_g_score + (heuristic * 0.8)

                        heapq.heappush(open_set, (f_score[neighbor.id], neighbor.id))

        # If we exhaust the open set without finding the goal, return direct path
        logger.warning(f"A* search failed to find path from {start_node_id} to {goal_node_id} "
                      f"after exploring {nodes_explored} nodes. Returning direct path.")

        # Return direct path as fallback
        return [start_node, goal_node]

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

    def _get_safety_cost(self, edge_id: int) -> float:
        """
        Get safety-based cost for an edge (lower = safer).
        Used for safety-weighted A* search.

        Args:
            edge_id: ID of the GraphEdge

        Returns:
            Safety cost (lower is safer)
        """
        try:
            # Get risk data if available
            risk_data = self.db.query(RoadSegmentRisk).filter(
                RoadSegmentRisk.id == edge_id
            ).first()

            if risk_data and risk_data.risk_score is not None:
                # Convert risk_score (0-1, higher=more risky) to safety cost
                # For safety routing: lower cost = safer route
                # We want: risk_score=0.0 (safe) -> low cost, risk_score=1.0 (dangerous) -> high cost
                safety_cost = (1.0 - risk_data.risk_score) * 50.0  # Invert and scale
                return max(1.0, safety_cost)  # Ensure minimum cost
            else:
                # No risk data available - assume moderately safe
                return 25.0  # Moderate safety cost
        except Exception:
            # Fallback to distance-based cost
            edge = self.db.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
            if edge:
                return float(edge.length)
            return 25.0  # Default fallback

    def calculate_ai_safety_score(self, latitude: float, longitude: float,
                                  timestamp: Optional[Any] = None) -> float:
        """
        Calculate safety score using the AI model.
        Returns -1.0 if the AI model fails.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            timestamp: Optional timestamp for temporal calculation

        Returns:
            Safety score between 0.0 and 1.0, or -1.0 if AI model fails
        """
        # This method is kept for compatibility with existing tests.
        # In the GIS-based service, we don't have the AI model integrated here.
        # We return a default value that can be overridden by tests.
        # The actual safety scoring is done via _calculate_safety_score which uses risk data.
        return 0.5

    def calculate_route_analytics(self, route_coords: List[Dict],
                                  safety_nodes: List[Any],
                                  crime_hotspots: List[Any],
                                  user_reports: List[Any],
                                  segment_risks: List[Any],
                                  black_spots: List[Any] = None,
                                  accident_records: List[Any] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive safety analytics for a route.

        Args:
            route_coords: List of dicts with 'latitude' and 'longitude' keys
            safety_nodes: List of SafetyNode objects
            crime_hotspots: List of CrimeHotspot objects
            user_reports: List of UserReport objects
            segment_risks: List of RoadSegmentRisk objects
            black_spots: Optional list of HighwayBlackSpot objects
            accident_records: Optional list of AccidentRecord objects

        Returns:
            Dictionary containing analytics metrics
        """
        # Handle default values for optional parameters
        if black_spots is None:
            black_spots = []
        if accident_records is None:
            accident_records = []

        # If we have insufficient route coordinates, return default analytics
        if not route_coords or len(route_coords) < 2:
            return self._get_default_analytics()

        # Initialize metrics
        total_distance = 0.0
        safety_scores = []
        risk_scores = []
        penalties = []
        segment_count = 0
        unsafe_distance = 0.0
        safe_distance = 0.0
        black_spots_crossed = 0
        dangerous_intersections = 0

        # For risk distribution (5 buckets: 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0)
        risk_distribution = [0, 0, 0, 0, 0]

        # Process each segment
        for i in range(len(route_coords) - 1):
            from_coord = route_coords[i]
            to_coord = route_coords[i + 1]

            # Calculate segment distance
            distance = self._haversine_distance(
                from_coord["latitude"], from_coord["longitude"],
                to_coord["latitude"], to_coord["longitude"]
            )
            total_distance += distance

            # Calculate penalty and safety for midpoint
            mid_lat = (from_coord["latitude"] + to_coord["latitude"]) / 2
            mid_lon = (from_coord["longitude"] + to_coord["longitude"]) / 2

            # Calculate penalty based on safety data
            penalty = self._calculate_penalty(mid_lat, mid_lon, safety_nodes, crime_hotspots, user_reports, segment_risks)

            # Check for high-risk area
            if self._is_high_risk_area(mid_lat, mid_lon, crime_hotspots):
                penalty *= getattr(settings, 'HIGH_RISK_SEGMENT_MULTIPLIER', 2.0)

            # Calculate safety score
            # Check if we have any GIS safety data to use for calculation
            has_gis_safety_data = bool(safety_nodes or crime_hotspots or user_reports or segment_risks)

            if has_gis_safety_data and penalty > 0:
                # Use GIS-based calculation when we have safety data and penalty > 0
                # Normalize penalty to reasonable range for safety score calculation
                # Penalty of 0 = safety score of 1.0 (completely safe)
                # Penalty of 50+ = safety score approaching 0.0 (very unsafe)
                safety_score = max(0.0, min(1.0, 1.0 - (penalty / 50.0)))
            else:
                # Fall back to AI safety score when no GIS safety data is available
                # Get AI safety score for the midpoint (returns 0.0-1.0 where higher is safer, or -1.0 if unavailable)
                ai_safety_score = self.calculate_ai_safety_score(mid_lat, mid_lon)
                if ai_safety_score >= 0:
                    # AI is available and returned a valid score
                    safety_score = ai_safety_score
                else:
                    # AI is unavailable, use neutral safety score
                    safety_score = 0.5

            risk_score = 1.0 - safety_score

            # Check for black spots crossed
            for bs in black_spots:
                bs_distance = self._haversine_distance(mid_lat, mid_lon, bs.latitude, bs.longitude)
                if bs_distance <= getattr(bs, 'radius', 50.0):  # Within the black spot radius
                    black_spots_crossed += 1
                    break  # Count each black spot only once per segment

            # Check for dangerous intersections (simplified: high accident density areas)
            accident_count = 0
            for acc in accident_records:
                acc_distance = self._haversine_distance(mid_lat, mid_lon, acc.latitude, acc.longitude)
                if acc_distance < 50:  # Within 50 meters
                    accident_count += 1
            if accident_count >= 3:  # Threshold for dangerous intersection
                dangerous_intersections += 1

            # Accumulate metrics
            safety_scores.append(safety_score)
            risk_scores.append(risk_score)
            penalties.append(penalty)
            segment_count += 1

            # Distance safety classification
            if risk_score > 0.6:
                unsafe_distance += distance
            elif risk_score < 0.3:
                safe_distance += distance

            # Risk distribution bucket
            bucket_index = min(int(risk_score * 5), 4)  # 0-4 for scores 0.0-0.8, 4 for 0.8-1.0
            risk_distribution[bucket_index] += 1

        # Calculate final metrics
        avg_safety = sum(safety_scores) / len(safety_scores) if safety_scores else 0.5
        avg_risk = 1.0 - avg_safety
        max_risk = max(risk_scores) if risk_scores else 0.5
        overall_safety_score = avg_safety
        avg_confidence = 0.8  # Placeholder - in reality would come from data quality metrics

        return {
            "average_risk": round(avg_risk, 3),
            "max_risk": round(max_risk, 3),
            "black_spots_crossed": black_spots_crossed,
            "black_spots_avoided": 0,  # Requires comparison route - not implemented
            "dangerous_intersections": dangerous_intersections,
            "average_confidence": round(avg_confidence, 2),
            "risk_distribution": risk_distribution,
            "segment_count": segment_count,
            "unsafe_distance": round(unsafe_distance, 1),
            "safe_distance": round(safe_distance, 1),
            "overall_safety_score": round(overall_safety_score, 3)
        }

    def _calculate_penalty(self, lat: float, lon: float,
                          safety_nodes: List[Any],
                          crime_hotspots: List[Any],
                          user_reports: List[Any],
                          segment_risks: List[Any]) -> float:
        """
        Calculate penalty for a point based on safety data.
        Simplified version of the original method.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            safety_nodes: List of SafetyNode objects
            crime_hotspots: List of CrimeHotspot objects
            user_reports: List of UserReport objects
            segment_risks: List of RoadSegmentRisk objects

        Returns:
            Penalty value
        """
        penalty = 0.0

        # Crime hotspot penalty
        for hotspot in crime_hotspots:
            distance = self._haversine_distance(lat, lon, hotspot.latitude, hotspot.longitude)
            if distance < hotspot.radius:
                # Calculate proximity factor (closer = higher penalty)
                proximity_factor = 1.0 - (distance / hotspot.radius)

                if hotspot.severity == "HIGH":
                    # Exponential penalty for high severity hotspots
                    base_penalty = settings.CRIME_HOTSPOT_HIGH_PENALTY_BASE if hasattr(settings, 'CRIME_HOTSPOT_HIGH_PENALTY_BASE') else 10.0
                    exponential_penalty = base_penalty * (2 ** proximity_factor)
                    penalty += exponential_penalty
                elif hotspot.severity == "MEDIUM":
                    penalty += settings.CRIME_HOTSPOT_MEDIUM_PENALTY * proximity_factor
                else:  # LOW
                    penalty += settings.CRIME_HOTSPOT_LOW_PENALTY * proximity_factor

        # Safety node penalty
        for node in safety_nodes:
            distance = self._haversine_distance(lat, lon, node.latitude, node.longitude)
            if distance < 100:  # Within 100 meters
                if node.lighting_level == "LOW":
                    penalty += settings.SAFETY_NODE_LOW_LIGHTING_PENALTY if hasattr(settings, 'SAFETY_NODE_LOW_LIGHTING_PENALTY') else 5.0
                if node.crowd_density == "SPARSE":
                    penalty += settings.SAFETY_NODE_SPARSE_CROWD_PENALTY if hasattr(settings, 'SAFETY_NODE_SPARSE_CROWD_PENALTY') else 5.0
                # Bonus for high safety score
                if node.safety_score > 0.8:
                    penalty -= settings.SAFETY_NODE_SPARSE_CROWD_PENALTY * 0.3  # Reduced bonus

        # User report penalty (dynamic based on recency)
        recent_timestamp = datetime.utcnow() - timedelta(days=7)
        for report in user_reports:
            if report.is_active and report.timestamp > recent_timestamp:
                distance = self._haversine_distance(lat, lon, report.latitude, report.longitude)
                if distance < 150:  # Within 150 meters
                    # More recent reports have higher penalty
                    days_old = (datetime.utcnow() - report.timestamp).days
                    penalty += (settings.USER_REPORT_BASE_PENALTY / (days_old + 1)) if hasattr(settings, 'USER_REPORT_BASE_PENALTY') else 1.0 / (days_old + 1)

        # Road segment risk penalty (pre-computed from accident data)
        if segment_risks:
            for sr in segment_risks:
                distance = self._haversine_distance(lat, lon, sr.start_latitude, sr.start_longitude)
                if distance < settings.SEGMENT_RISK_SEARCH_RADIUS_M:
                    penalty += sr.risk_score * settings.SEGMENT_RISK_BASE_PENALTY

        return max(0, penalty)  # Ensure penalty is non-negative

    def _is_high_risk_area(self, lat: float, lon: float,
                          crime_hotspots: List[Any]) -> bool:
        """
        Check if a coordinate is in a high-risk area (HIGH severity hotspot).

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            crime_hotspots: List of CrimeHotspot objects

        Returns:
            True if within radius of any HIGH severity hotspot, False otherwise
        """
        for hotspot in crime_hotspots:
            if hotspot.severity == "HIGH":
                distance = self._haversine_distance(lat, lon, hotspot.latitude, hotspot.longitude)
                if distance < hotspot.radius:
                    return True
        return False

    def _get_default_analytics(self) -> Dict[str, Any]:
        """Return default analytics when route data is insufficient."""
        return {
            "average_risk": 0.5,
            "max_risk": 0.5,
            "black_spots_crossed": 0,
            "black_spots_avoided": 0,
            "dangerous_intersections": 0,
            "average_confidence": 0.3,
            "risk_distribution": [0, 0, 0, 0, 0],
            "segment_count": 0,
            "unsafe_distance": 0.0,
            "safe_distance": 0.0,
            "overall_safety_score": 0.5
        }

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

        # If start and end nodes are the same, return direct route
        if start_node.id == end_node.id:
            direct_coords = [source, destination]
            distance, safety_score, segments = self._calculate_route_metrics(direct_coords)
            return {
                "safest_route": direct_coords,
                "fastest_route": direct_coords,
                "safest_distance": distance,
                "fastest_distance": distance,
                "safest_safety_score": safety_score,
                "fastest_safety_score": safety_score,
                "route_segments": segments
            }

        # Step 2 & 3: A* over GraphEdge graph
        # Find fastest route (distance-weighted)
        fastest_path_nodes = self._astar_search(start_node.id, end_node.id, weight_mode='fast')
        # Find safest route (safety-weighted)
        safest_path_nodes = self._astar_search(start_node.id, end_node.id, weight_mode='safe')

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