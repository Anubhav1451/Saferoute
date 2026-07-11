# app/services/routing.py
import math
import logging
import os
import time
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import SafetyNode, CrimeHotspot, UserReport, RoadSegmentRisk, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate, RouteSegment
from app.core.config import settings
import json
import requests
import concurrent.futures

# Import AI safety model
try:
    from app.ml.safety_model import predict_safety_score
    AI_SAFETY_AVAILABLE = True
except ImportError:
    AI_SAFETY_AVAILABLE = False
    # Create a dummy function for when AI is not available
    def predict_safety_score(*args, **kwargs):
        return 0.5  # Default neutral score


logger = logging.getLogger(__name__)


class SafetyRoutingService:
    """
    AI Safety Routing Service using A* algorithm with dynamic cost calculation.
    Cost = Distance + Penalty
    """
    # Class-level cache for safety data keyed by corridor bounding box
    _safety_data_cache = {}
    # Class-level cache for safety graph (nodes and adjacency) keyed by corridor bounding box
    _safety_graph_cache = {}

    def __init__(self, db: Session):
        # Debug print removed
        # print("SafetyRoutingService.__init__ called", flush=True)
        self.db = db
        self.edge_threshold_m = 500000.0  # max distance (m) to create an edge between safety nodes
        self.mapbox_token = settings.MAPBOX_TOKEN  # read from environment via settings
        self.max_match_segment_m = 10000  # maximum segment length for Mapbox matching (meters)
        self.max_match_distance_m = 50000  # maximum distance (m) to attempt map matching (50km)

    # --------------------- HELPERS ---------------------
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters using Haversine formula"""
        R = 6371000  # Earth's radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def remove_consecutive_duplicates(self, coords):
        """Remove consecutive duplicate coordinates (same lat and lon) from a list of coordinate dicts.
        Preserves the first and last occurrence.
        """
        if not coords:
            return []
        result = [coords[0]]
        for i in range(1, len(coords)):
            if coords[i]["latitude"] != result[-1]["latitude"] or coords[i]["longitude"] != result[-1]["longitude"]:
                result.append(coords[i])
        return result

    def calculate_penalty(self, lat: float, lon: float,
                         safety_nodes: List[SafetyNode],
                         crime_hotspots: List[CrimeHotspot],
                         user_reports: List[UserReport],
                         segment_risks: List[RoadSegmentRisk] = None) -> float:
        """
        Calculate dynamic penalty for a coordinate based on:
        - Crime hotspots (high severity = heavy penalty)
        - Safety nodes with low lighting or sparse crowd (medium penalty)
        - Recent active user reports (dynamic penalty)
        - Pre-computed road segment risk scores (from accident data)

        Uses configurable penalty values from settings.
        """
        penalty = 0.0

        # Crime hotspot penalty
        for hotspot in crime_hotspots:
            distance = self.haversine_distance(lat, lon, hotspot.latitude, hotspot.longitude)
            if distance < hotspot.radius:
                # Calculate proximity factor (closer = higher penalty)
                # Proximity factor is 1.0 when distance is 0 (at center), 0.0 when distance equals radius
                proximity_factor = 1.0 - (distance / hotspot.radius)

                if hotspot.severity == SeverityLevel.HIGH:
                    # Exponential penalty for high severity hotspots
                    # Base penalty from settings + exponential based on proximity
                    base_penalty = settings.CRIME_HOTSPOT_HIGH_PENALTY_BASE
                    exponential_penalty = base_penalty * (2 ** proximity_factor)
                    penalty += exponential_penalty
                elif hotspot.severity == SeverityLevel.MEDIUM:
                    penalty += settings.CRIME_HOTSPOT_MEDIUM_PENALTY * proximity_factor
                else:  # LOW
                    penalty += settings.CRIME_HOTSPOT_LOW_PENALTY * proximity_factor

        # Safety node penalty
        for node in safety_nodes:
            distance = self.haversine_distance(lat, lon, node.latitude, node.longitude)
            if distance < 100:  # Within 100 meters
                if node.lighting_level == LightingLevel.LOW:
                    penalty += settings.SAFETY_NODE_LOW_LIGHTING_PENALTY
                if node.crowd_density == CrowdDensity.SPARSE:
                    penalty += settings.SAFETY_NODE_SPARSE_CROWD_PENALTY
                # Bonus for high safety score
                if node.safety_score > 0.8:
                    penalty -= settings.SAFETY_NODE_SPARSE_CROWD_PENALTY * 0.3  # Reduced bonus

        # User report penalty (dynamic based on recency)
        recent_timestamp = datetime.utcnow() - timedelta(days=7)
        for report in user_reports:
            if report.is_active and report.timestamp > recent_timestamp:
                distance = self.haversine_distance(lat, lon, report.latitude, report.longitude)
                if distance < 150:  # Within 150 meters
                    # More recent reports have higher penalty
                    days_old = (datetime.utcnow() - report.timestamp).days
                    penalty += (settings.USER_REPORT_BASE_PENALTY / (days_old + 1))

        # Road segment risk penalty (pre-computed from accident data)
        if segment_risks:
            for sr in segment_risks:
                distance = self.haversine_distance(lat, lon, sr.start_latitude, sr.start_longitude)
                if distance < settings.SEGMENT_RISK_SEARCH_RADIUS_M:
                    penalty += sr.risk_score * settings.SEGMENT_RISK_BASE_PENALTY

        return max(0, penalty)  # Ensure penalty is non-negative

    def calculate_safety_score(self, penalty: float) -> float:
        """
        Calculate safety score from penalty value.
        Safety score = max(0, 1 - (penalty / max_penalty))
        """
        max_penalty = settings.SAFETY_SCORE_MAX_PENALTY
        if max_penalty == 0:
            return 1.0
        # Avoid division by zero
        if max_penalty > 0:
            calculated_score = max(0.0, 1.0 - (penalty / max_penalty))
        else:
            calculated_score = 1.0
        # Clamp between 0 and 1
        return max(0.0, min(1.0, float(calculated_score)))

    def calculate_ai_safety_score(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> float:
        """
        Calculate safety score using the AI model.
        Falls back to rule-based if AI is not available or fails.
        """
        if not AI_SAFETY_AVAILABLE:
            # Fallback to rule-based (will be calculated elsewhere)
            return -1.0  # Signal to use fallback

        try:
            # Get AI prediction
            ai_score = predict_safety_score(latitude, longitude, timestamp)
            # AI score should be between 0 and 1
            return max(0.0, min(1.0, float(ai_score)))
        except Exception as e:
            logger.warning(f"AI safety prediction failed: {e}. Falling back to rule-based.")
            return -1.0  # Signal to use fallback

    def is_high_risk_area(self, lat: float, lon: float,
                         crime_hotspots: List[CrimeHotspot]) -> bool:
        """
        Check if a coordinate is in a high-risk area (HIGH severity hotspot).
        Returns True if within radius of any HIGH severity hotspot.
        """
        for hotspot in crime_hotspots:
            if hotspot.severity == SeverityLevel.HIGH:
                distance = self.haversine_distance(lat, lon, hotspot.latitude, hotspot.longitude)
                if distance < hotspot.radius:
                    return True
        return False

    def get_nearby_safety_data(self, lat: float, lon: float,
                              radius_meters: float = None) -> tuple:
        """Get safety data within radius of a coordinate"""
        # Use configurable radius from settings if not provided
        if radius_meters is None:
            radius_meter = settings.DEFAULT_SEARCH_RADIUS_METERS
        else:
            radius_meter = radius_meters

        # Simple bounding box query for nearby data
        lat_delta = radius_meter / 111000  # Approximate degrees per meter
        lon_delta = radius_meter / (111000 * math.cos(math.radians(lat)))

        safety_nodes = self.db.query(SafetyNode).filter(
            SafetyNode.latitude.between(lat - lat_delta, lat + lat_delta),
            SafetyNode.longitude.between(lon - lon_delta, lon + lon_delta)
        ).all()

        crime_hotspots = self.db.query(CrimeHotspot).filter(
            CrimeHotspot.latitude.between(lat - lat_delta, lat + lat_delta),
            CrimeHotspot.longitude.between(lon - lon_delta, lon + lon_delta)
        ).all()

        user_reports = self.db.query(UserReport).filter(
            UserReport.latitude.between(lat - lat_delta, lat + lat_delta),
            UserReport.longitude.between(lon - lon_delta, lon + lon_delta),
            UserReport.is_active == True
        ).all()

        segment_risks = self.db.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.start_latitude.between(lat - lat_delta, lat + lat_delta),
            RoadSegmentRisk.start_longitude.between(lon - lon_delta, lon + lon_delta)
        ).all()

        return (safety_nodes, crime_hotspots, user_reports, segment_risks)

    def get_nearby_safety_data_bounding_box(self, min_lat: float, max_lat: float,
                                           min_lon: float, max_lon: float) -> tuple:
        """Get safety data within a bounding box"""
        safety_nodes = self.db.query(SafetyNode).filter(
            SafetyNode.latitude.between(min_lat, max_lat),
            SafetyNode.longitude.between(min_lon, max_lon)
        ).all()

        crime_hotspots = self.db.query(CrimeHotspot).filter(
            CrimeHotspot.latitude.between(min_lat, max_lat),
            CrimeHotspot.longitude.between(min_lon, max_lon)
        ).all()

        user_reports = self.db.query(UserReport).filter(
            UserReport.latitude.between(min_lat, max_lat),
            UserReport.longitude.between(min_lon, max_lon),
            UserReport.is_active == True
        ).all()

        segment_risks = self.db.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.start_latitude.between(min_lat, max_lat),
            RoadSegmentRisk.start_longitude.between(min_lon, max_lon)
        ).all()

        return (safety_nodes, crime_hotspots, user_reports, segment_risks)

    def generate_intermediate_points(self, start: Coordinate, end: Coordinate,
                                   num_points: int = None) -> list:
        """Generate intermediate points between start and end for pathfinding"""
        # Use configurable number of points from settings if not provided
        if num_points is None:
            num_points = settings.DEFAULT_INTERPOLATION_POINTS

        points = []
        for i in range(num_points + 1):
            t = i / num_points
            lat = start.latitude + t * (end.latitude - start.latitude)
            lon = start.longitude + t * (end.longitude - start.longitude)
            points.append(Coordinate(latitude=lat, longitude=lon))
        return points

    # --------------------- MAP MATCHING ---------------------
    def _map_match_segment(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:
        """
        Call Mapbox Map Matching API to get a road-matched trace between two points.
        Returns list of {'latitude': float, 'longitude': float} or None on failure.
        """
        if not self.mapbox_token:
            logger.warning("MAPBOX_TOKEN not set; skipping map matching.")
            return None

        # Format: lon,lat;lon,lat
        coords = f"{start.longitude},{start.latitude};{end.longitude},{end.latitude}"
        url = f"https://api.mapbox.com/matching/v5/mapbox/driving/{coords}.json"
        params = {
            "access_token": self.mapbox_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "true"
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Mapbox matching failed: {resp.status_code} {resp.text}")
                return None
            data = resp.json()
            if data.get("code") != "Ok" or not data.get("tracepoints"):
                logger.error(f"Mapbox matching returned no trace: {data}")
                return None
            # Extract the matched coordinates from the geometry
            # The matched trace is in data['tracepoints']? Actually geometry is in each match?
            # Simpler: use the 'matchings'[0]['geometry'] if present.
            matchings = data.get("matchings")
            if not matchings:
                return None
            geometry = matchings[0].get("geometry")
            if not geometry or geometry.get("type") != "LineString":
                return None
            coords_list = geometry.get("coordinates")
            # Convert to list of dicts
            return [{"latitude": lat, "longitude": lon} for lon, lat in coords_list]
        except Exception as e:
            logger.error(f"Error calling Mapbox matching: {e}")
            return None

    def _get_directions_route(self, start: Coordinate, end: Coordinate) -> Optional[List[Dict]]:
        """
        Call Mapbox Directions API to get a route between two points.
        Returns list of {'latitude': float, 'longitude': float} or None on failure.
        """
        if not self.mapbox_token:
            logger.warning("MAPBOX_TOKEN not set; skipping directions.")
            return None

        # Format: lon,lat;lon,lat
        coordinates = f"{start.longitude},{start.latitude};{end.longitude},{end.latitude}"
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}.json"
        params = {
            "access_token": self.mapbox_token,
            "geometries": "geojson",
            "overview": "full",
            "steps": "false"
        }
        try:
            resp = requests.get(url, params=params, timeout=settings.MAPBOX_DIRECTIONS_TIMEOUT_SEC)
            if resp.status_code != 200:
                logger.error(f"Mapbox Directions API failed: {resp.status_code} {resp.text}")
                return None
            data = resp.json()
            if data.get("code") != "Ok" or not data.get("routes"):
                logger.error(f"Mapbox Directions API returned no routes: {data}")
                return None
            # Extract the route geometry from the first route
            route = data["routes"][0]
            geometry = route.get("geometry")
            if not geometry or geometry.get("type") != "LineString":
                return None
            coords_list = geometry.get("coordinates")
            # Convert to list of dicts
            return [{"latitude": lat, "longitude": lon} for lon, lat in coords_list]
        except Exception as e:
            logger.error(f"Error calling Mapbox directions: {e}")
            return None

    # --------------------- ROUTE COST ---------------------
    def calculate_route_cost(self, path: list,
                           safety_nodes: list,
                           crime_hotspots: list,
                           user_reports: list,
                           segment_risks: list = None,
                           safety_weight: float = None) -> tuple:
        """
        Calculate total cost of a route considering distance and safety penalties.
        Returns (total_cost, total_distance, segments)

        Uses configurable values for weights and penalties.
        """
        # Use default safety weight from settings if not provided
        if safety_weight is None:
            weight = settings.DEFAULT_SAFETY_WEIGHT
        else:
            weight = float(safety_weight)

        total_distance = 0.0
        total_penalty = 0.0
        segments = []
        high_risk_segments = 0

        for i in range(len(path) - 1):
            from_coord = path[i]
            to_coord = path[i + 1]

            distance = self.haversine_distance(
                from_coord.latitude, from_coord.longitude,
                to_coord.latitude, to_coord.longitude
            )

            # Calculate penalty for the midpoint of the segment
            mid_lat = (from_coord.latitude + to_coord.latitude) / 2
            mid_lon = (from_coord.longitude + to_coord.longitude) / 2
            penalty = self.calculate_penalty(mid_lat, mid_lon, safety_nodes, crime_hotspots, user_reports, segment_risks)

            # Check if segment passes through high-risk area
            if self.is_high_risk_area(mid_lat, mid_lon, crime_hotspots):
                high_risk_segments += 1
                # Exponential penalty multiplier for high-risk segments
                penalty *= settings.HIGH_RISK_SEGMENT_MULTIPLIER

            total_distance += distance
            total_penalty += penalty

            # Calculate safety score for this segment
            # Try to use AI model first, fall back to rule-based
            safety_score = self.calculate_ai_safety_score(mid_lat, mid_lon)
            if safety_score < 0:  # AI failed or not available
                # Fall back to rule-based calculation
                safety_score = self.calculate_safety_score(penalty)

            # Add segment info
            # Convert to dict for RouteSegment (which expects dicts)
            from_coord_dict = {"latitude": from_coord.latitude, "longitude": from_coord.longitude}
            to_coord_dict = {"latitude": to_coord.latitude, "longitude": to_coord.longitude}
            segments.append(RouteSegment(
                from_coord=from_coord_dict,
                to_coord=to_coord_dict,
                distance=distance,
                safety_score=safety_score,
                penalty=penalty
            ))

        # Additional penalty if route passes through multiple high-risk segments
        if high_risk_segments > 0:
            total_penalty *= (1 + (high_risk_segments * settings.HIGH_RISK_SEGMENT_ADDITIONAL_FACTOR))

        # Weighted cost: weight * penalty + (1 - weight) * distance
        weighted_cost = (weight * total_penalty) + ((1 - weight) * total_distance)

        return (float(weighted_cost), float(total_distance), [s for s in segments])

    # --------------------- MAIN ROUTING ---------------------
    def find_safest_route(self, source: Coordinate, destination: Coordinate,
                          safety_weight: float = None) -> dict:
        """
        Find the safest route using a graph of SafetyNodes and map-matching each edge.
        Returns both safest and fastest routes.
        """
        # Start timing for diagnostics
        route_start_time = time.time()

        # Use default safety weight from settings if not provided
        if safety_weight is None:
            sw = settings.DEFAULT_SAFETY_WEIGHT
        else:
            sw = float(safety_weight)

        # Get safety data for the corridor between source and destination with padding
        # Padding of 0.15km (150 meters) on each side of the direct path
        padding_meters = 150.0  # 0.15km padding
        # Convert padding to degrees (approximate)
        lat_padding = padding_meters / 111000.0  # 1 degree latitude = 111 km
        mid_lat = (source.latitude + destination.latitude) / 2.0
        lon_padding = padding_meters / (111000.0 * math.cos(math.radians(mid_lat)))

        min_lat = min(source.latitude, destination.latitude) - lat_padding
        max_lat = max(source.latitude, destination.latitude) + lat_padding
        min_lon = min(source.longitude, destination.longitude) - lon_padding
        max_lon = max(source.longitude, destination.longitude) + lon_padding

        # Create cache key by rounding bounding box to 5 decimal places
        cache_key = (
            round(min_lat, 5),
            round(max_lat, 5),
            round(min_lon, 5),
            round(max_lon, 5)
        )

        # Try to get cached safety data (safety nodes, crime hotspots, user reports)
        cached_safety_data = self._safety_data_cache.get(cache_key)
        if cached_safety_data is not None:
            all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks = cached_safety_data
            logger.debug(f"Using cached safety data for corridor: {cache_key}")
        else:
            # Retrieve safety data for the corridor
            all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks = self.get_nearby_safety_data_bounding_box(
                min_lat, max_lat, min_lon, max_lon
            )
            # Deduplicate safety nodes: for each unique (lat, lon), keep the node with the highest safety_score
            unique_nodes = {}
            for node in all_safety_nodes:
                key = (node.latitude, node.longitude)
                if key not in unique_nodes or node.safety_score > unique_nodes[key].safety_score:
                    unique_nodes[key] = node
            all_safety_nodes = list(unique_nodes.values())

            logger.debug(f"CORRIDOR_BOUNDING_BOX: ({min_lat:.4f}, {max_lat:.4f}, {min_lon:.4f}, {max_lon:.4f})")
            logger.debug(f"Number of safety nodes retrieved after deduplication: {len(all_safety_nodes)}")
            logger.debug(f"Number of crime hotspots retrieved: {len(all_crime_hotspots)}")
            logger.debug(f"Number of user reports retrieved: {len(all_user_reports)}")
            logger.debug(f"Number of road segment risks retrieved: {len(all_segment_risks)}")

            # Cache the safety data for this corridor
            self._safety_data_cache[cache_key] = (all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks)
            logger.info(f"SAFETY_DATA_CACHE_MISS: Cached safety data for corridor: {cache_key}")

        # Try to get cached penalty-based graph for safety_nodes (without source/dest)
        cached_graph = self._safety_graph_cache.get(cache_key)
        graph_start_time = time.time()
        safety_nodes = all_safety_nodes  # deduped safety nodes from safety data cache
        if cached_graph is not None:
            (_cached_adj, _cached_fmp, _cache_hav_count, _cache_penalty_count,
             _cache_t_hav, _cache_t_pen, _cache_edge_risk_cache) = cached_graph
            graph_end_time = time.time()
            logger.info(f"GRAPH_CACHE_HIT: graph_build_time_seconds={graph_end_time-graph_start_time:.3f} for corridor: {cache_key}")
            _cache_hit = True
        else:
            _cache_hit = False
            graph_end_time = time.time()

        # Build the full list of nodes (safety nodes + source + destination)
        # Use a dictionary to hold nodes by (lat, lon) for quick lookup, starting with safety nodes
        node_dict = {}
        for node in safety_nodes:
            key = (node.latitude, node.longitude)
            if key not in node_dict or node.safety_score > node_dict[key].safety_score:
                node_dict[key] = node

        # Ensure source and destination are in the node_dict
        # Handle source node
        source_key = (source.latitude, source.longitude)
        if source_key not in node_dict:
            source_node = SafetyNode(
                id=-1,  # Temporary ID
                latitude=source.latitude,
                longitude=source.longitude,
                safety_score=self.calculate_ai_safety_score(source.latitude, source.longitude),
                lighting_level=LightingLevel.MEDIUM,
                crowd_density=CrowdDensity.NORMAL,
                updated_at=datetime.utcnow()
            )
            if source_node.safety_score < 0:  # AI failed, use rule based
                # Get nearby data for source to calculate initial penalty
                src_safety_nodes, src_crime_hotspots, src_user_reports, src_segment_risks = self.get_nearby_safety_data(source.latitude, source.longitude, radius_meters=settings.DEFAULT_SEARCH_RADIUS_METERS)
                src_penalty = self.calculate_penalty(source.latitude, source.longitude, src_safety_nodes, src_crime_hotspots, src_user_reports, src_segment_risks)
                source_node.safety_score = self.calculate_safety_score(src_penalty)
            node_dict[source_key] = source_node
        else:
            source_node = node_dict[source_key]

        # Handle destination node
        dest_key = (destination.latitude, destination.longitude)
        if dest_key not in node_dict:
            dest_node = SafetyNode(
                id=-2,  # Temporary ID
                latitude=destination.latitude,
                longitude=destination.longitude,
                safety_score=self.calculate_ai_safety_score(destination.latitude, destination.longitude),
                lighting_level=LightingLevel.MEDIUM,
                crowd_density=CrowdDensity.NORMAL,
                updated_at=datetime.utcnow()
            )
            if dest_node.safety_score < 0:  # AI failed, use rule based
                # Get nearby data for destination to calculate initial penalty
                dest_safety_nodes, dest_crime_hotspots, dest_user_reports, dest_segment_risks = self.get_nearby_safety_data(destination.latitude, destination.longitude, radius_meters=settings.DEFAULT_SEARCH_RADIUS_METERS)
                dest_penalty = self.calculate_penalty(destination.latitude, destination.longitude, dest_safety_nodes, dest_crime_hotspots, dest_user_reports, dest_segment_risks)
                dest_node.safety_score = self.calculate_safety_score(dest_penalty)
            node_dict[dest_key] = dest_node
        else:
            dest_node = node_dict[dest_key]

        # Now, the nodes list is the values of the dictionary
        nodes = list(node_dict.values())
        # Map from node to index
        node_to_idx = {node: idx for idx, node in enumerate(nodes)}
        src_idx = node_to_idx[source_node]
        dst_idx = node_to_idx[dest_node]

        logger.debug(f"Total nodes in graph (including source/dest): {len(nodes)}")

        # Build adjacency list: connect each node to its K nearest neighbors within edge_threshold_m
        K = settings.GRAPH_NEIGHBOR_COUNT
        n = len(nodes)
        n_base = len(safety_nodes)
        adjacency = [[] for _ in range(n)]

        penalty_precompute_start = time.time()

        if _cache_hit:
            # Extend cached adjacency (safety_nodes only) with source/dest edges
            for i in range(n_base):
                adjacency[i] = list(_cached_adj[i])
            fast_midpoint_penalty = _cached_fmp
            _hav_count = _cache_hav_count
            _penalty_count = _cache_penalty_count
            _t_hav = _cache_t_hav
            _t_pen = _cache_t_pen
            edge_risk_cache = dict(_cache_edge_risk_cache)

            for idx in range(n_base, n):
                extra_node = nodes[idx]
                extra_dists = []
                _t0 = time.time()
                for j in range(n_base):
                    dist = self.haversine_distance(extra_node.latitude, extra_node.longitude,
                                                   safety_nodes[j].latitude, safety_nodes[j].longitude)
                    _hav_count += 1
                    if dist <= self.edge_threshold_m:
                        extra_dists.append((dist, j))
                _t_hav += time.time() - _t0
                extra_dists.sort(key=lambda x: x[0])
                for k in range(min(K, len(extra_dists))):
                    dist, j = extra_dists[k]
                    _mlat = (extra_node.latitude + safety_nodes[j].latitude) / 2.0
                    _mlon = (extra_node.longitude + safety_nodes[j].longitude) / 2.0
                    _t0 = time.time()
                    mid_penalty = fast_midpoint_penalty(_mlat, _mlon)
                    _t_pen += time.time() - _t0
                    _penalty_count += 1
                    mid_safety = self.calculate_safety_score(mid_penalty)
                    risk_mid = 1.0 - mid_safety
                    weight_fast = dist
                    weight_safe = dist * (1.0 + settings.ROUTE_COST_ALPHA * risk_mid)
                    adjacency[idx].append((j, weight_fast, weight_safe))
                    adjacency[j].append((idx, weight_fast, weight_safe))

            logger.info(f"GRAPH_CACHE_EXTEND: extended {n - n_base} extra nodes in {time.time() - penalty_precompute_start:.3f}s")

        else:
            # --- Euclidean fast surface distance (accurate within ~500km) ---
            cos_avg_lat = math.cos(math.radians(mid_lat))
            M_PER_DEG = 111320.0
            m_per_deg_lon = M_PER_DEG * cos_avg_lat

            def fast_surface_dist(lat1, lon1, lat2, lon2):
                dlat = (lat1 - lat2) * M_PER_DEG
                dlon = (lon1 - lon2) * m_per_deg_lon
                return math.hypot(dlat, dlon)

            # Build grid index for fast midpoint penalty lookup (1.1km cells, 2 decimal places)
            cell_step = 0.01
            def round_cell(v):
                return round(v, 2)
            cell_safety_lookup = {}
            for sn in all_safety_nodes:
                cell_safety_lookup.setdefault((round_cell(sn.latitude), round_cell(sn.longitude)), []).append(sn)
            cell_report_lookup = {}
            for r in all_user_reports:
                cell_report_lookup.setdefault((round_cell(r.latitude), round_cell(r.longitude)), []).append(r)
            high_sev_hotspots = [h for h in all_crime_hotspots if h.severity == SeverityLevel.HIGH]
            cell_segment_lookup = {}
            for sr in all_segment_risks:
                cell_segment_lookup.setdefault((round_cell(sr.start_latitude), round_cell(sr.start_longitude)), []).append(sr)
            report_cutoff = datetime.utcnow() - timedelta(days=7)
            cell_deltas = [(-cell_step, -cell_step), (-cell_step, 0.0), (-cell_step, cell_step),
                           (0.0, -cell_step), (0.0, 0.0), (0.0, cell_step),
                           (cell_step, -cell_step), (cell_step, 0.0), (cell_step, cell_step)]

            def fast_midpoint_penalty(mid_lat, mid_lon):
                penalty = 0.0
                clat = round_cell(mid_lat)
                clon = round_cell(mid_lon)
                high_risk = False
                for h in all_crime_hotspots:
                    d = fast_surface_dist(mid_lat, mid_lon, h.latitude, h.longitude)
                    if d < h.radius:
                        prox = 1.0 - (d / h.radius)
                        if h.severity == SeverityLevel.HIGH:
                            penalty += settings.CRIME_HOTSPOT_HIGH_PENALTY_BASE * (2.0 ** prox)
                            high_risk = True
                        elif h.severity == SeverityLevel.MEDIUM:
                            penalty += settings.CRIME_HOTSPOT_MEDIUM_PENALTY * prox
                        else:
                            penalty += settings.CRIME_HOTSPOT_LOW_PENALTY * prox
                for dl, dlon in cell_deltas:
                    for sn in cell_safety_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                        _dlat = (mid_lat - sn.latitude) * M_PER_DEG
                        _dlon = (mid_lon - sn.longitude) * m_per_deg_lon
                        if _dlat * _dlat + _dlon * _dlon < 10000:
                            if sn.lighting_level == LightingLevel.LOW:
                                penalty += settings.SAFETY_NODE_LOW_LIGHTING_PENALTY
                            if sn.crowd_density == CrowdDensity.SPARSE:
                                penalty += settings.SAFETY_NODE_SPARSE_CROWD_PENALTY
                            if sn.safety_score > 0.8:
                                penalty -= settings.SAFETY_NODE_SPARSE_CROWD_PENALTY * 0.3
                for dl, dlon in cell_deltas:
                    for r in cell_report_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                        if r.is_active and r.timestamp > report_cutoff:
                            _dlat = (mid_lat - r.latitude) * M_PER_DEG
                            _dlon = (mid_lon - r.longitude) * m_per_deg_lon
                            if _dlat * _dlat + _dlon * _dlon < 22500:
                                penalty += settings.USER_REPORT_BASE_PENALTY / ((datetime.utcnow() - r.timestamp).days + 1)
                for dl, dlon in cell_deltas:
                    for sr in cell_segment_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                        _dlat = (mid_lat - sr.start_latitude) * M_PER_DEG
                        _dlon = (mid_lon - sr.start_longitude) * m_per_deg_lon
                        if _dlat * _dlat + _dlon * _dlon < settings.SEGMENT_RISK_SEARCH_RADIUS_M ** 2:
                            penalty += sr.risk_score * settings.SEGMENT_RISK_BASE_PENALTY
                if high_risk:
                    penalty *= settings.HIGH_RISK_SEGMENT_MULTIPLIER
                return max(0, penalty)

            # --- Adjacency build with edge risk cache ---
            edge_risk_cache = {}
            _hav_dist_cache = {}
            _hav_count = 0
            _penalty_count = 0
            _t_hav = 0.0
            _t_pen = 0.0
            for i in range(n):
                dists = []
                _t0 = time.time()
                for j in range(n):
                    if i == j:
                        continue
                    _hav_ij_key = (min(i, j), max(i, j))
                    if _hav_ij_key in _hav_dist_cache:
                        dist = _hav_dist_cache[_hav_ij_key]
                    else:
                        _hav_count += 1
                        dist = self.haversine_distance(nodes[i].latitude, nodes[i].longitude,
                                                       nodes[j].latitude, nodes[j].longitude)
                        _hav_dist_cache[_hav_ij_key] = dist
                    if dist <= self.edge_threshold_m:
                        dists.append((dist, j))
                _t_hav += time.time() - _t0
                dists.sort(key=lambda x: x[0])

                for k_ in range(min(K, len(dists))):
                    dist, j = dists[k_]
                    _risk_key = (min(i, j), max(i, j))

                    if _risk_key in edge_risk_cache:
                        risk_mid = edge_risk_cache[_risk_key]
                    else:
                        _penalty_count += 1
                        mid_lat = (nodes[i].latitude + nodes[j].latitude) / 2.0
                        mid_lon = (nodes[i].longitude + nodes[j].longitude) / 2.0
                        _t0 = time.time()
                        mid_penalty = 0.0
                        clat = round_cell(mid_lat)
                        clon = round_cell(mid_lon)
                        high_risk = False
                        # Crime hotspot penalty
                        for h in all_crime_hotspots:
                            dh = fast_surface_dist(mid_lat, mid_lon, h.latitude, h.longitude)
                            if dh < h.radius:
                                prox = 1.0 - (dh / h.radius)
                                if h.severity == SeverityLevel.HIGH:
                                    mid_penalty += settings.CRIME_HOTSPOT_HIGH_PENALTY_BASE * (2.0 ** prox)
                                    high_risk = True
                                elif h.severity == SeverityLevel.MEDIUM:
                                    mid_penalty += settings.CRIME_HOTSPOT_MEDIUM_PENALTY * prox
                                else:
                                    mid_penalty += settings.CRIME_HOTSPOT_LOW_PENALTY * prox
                        # Safety node penalty (grid-indexed, squared distance)
                        for dl, dlon in cell_deltas:
                            for sn in cell_safety_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                                _dlat = (mid_lat - sn.latitude) * M_PER_DEG
                                _dlon = (mid_lon - sn.longitude) * m_per_deg_lon
                                if _dlat * _dlat + _dlon * _dlon < 10000:
                                    if sn.lighting_level == LightingLevel.LOW:
                                        mid_penalty += settings.SAFETY_NODE_LOW_LIGHTING_PENALTY
                                    if sn.crowd_density == CrowdDensity.SPARSE:
                                        mid_penalty += settings.SAFETY_NODE_SPARSE_CROWD_PENALTY
                                    if sn.safety_score > 0.8:
                                        mid_penalty -= settings.SAFETY_NODE_SPARSE_CROWD_PENALTY * 0.3
                        # User report penalty (grid-indexed, squared distance)
                        for dl, dlon in cell_deltas:
                            for r in cell_report_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                                if r.is_active and r.timestamp > report_cutoff:
                                    _dlat = (mid_lat - r.latitude) * M_PER_DEG
                                    _dlon = (mid_lon - r.longitude) * m_per_deg_lon
                                    if _dlat * _dlat + _dlon * _dlon < 22500:
                                        mid_penalty += settings.USER_REPORT_BASE_PENALTY / ((datetime.utcnow() - r.timestamp).days + 1)
                        # Road segment risk penalty (grid-indexed, squared distance)
                        for dl, dlon in cell_deltas:
                            for sr in cell_segment_lookup.get((round_cell(clat + dl), round_cell(clon + dlon)), ()):
                                _dlat = (mid_lat - sr.start_latitude) * M_PER_DEG
                                _dlon = (mid_lon - sr.start_longitude) * m_per_deg_lon
                                if _dlat * _dlat + _dlon * _dlon < settings.SEGMENT_RISK_SEARCH_RADIUS_M ** 2:
                                    mid_penalty += sr.risk_score * settings.SEGMENT_RISK_BASE_PENALTY
                        if high_risk:
                            mid_penalty *= settings.HIGH_RISK_SEGMENT_MULTIPLIER
                        mid_penalty = max(0, mid_penalty)
                        _t_pen += time.time() - _t0
                        mid_safety = self.calculate_safety_score(mid_penalty)
                        risk_mid = 1.0 - mid_safety
                        edge_risk_cache[_risk_key] = risk_mid

                    weight_fast = dist
                    alpha = settings.ROUTE_COST_ALPHA
                    weight_safe = dist * (1.0 + alpha * risk_mid)
                    adjacency[i].append((j, weight_fast, weight_safe))
                    adjacency[j].append((i, weight_fast, weight_safe))

            # Deduplicate adjacency (each undirected edge is added twice, once per endpoint)
            for i in range(n):
                seen = set()
                deduped = []
                for entry in adjacency[i]:
                    j = entry[0]
                    if j not in seen:
                        seen.add(j)
                        deduped.append(entry)
                adjacency[i] = deduped

            # Cache the penalty-based adjacency for safety_nodes (without source/dest)
            self._safety_graph_cache[cache_key] = (
                adjacency[:n_base],
                fast_midpoint_penalty,
                _hav_count, _penalty_count, _t_hav, _t_pen, edge_risk_cache
            )
            logger.info(f"GRAPH_CACHE_MISS: graph_build_time_seconds={graph_end_time - graph_start_time:.3f} for corridor: {cache_key}")
            num_edges_base = sum(len(adj) for adj in adjacency[:n_base])
            logger.info(f"GRAPH_BUILD_DETAILS: nodes={n_base}, edges={num_edges_base}")

        penalty_precompute_time = time.time() - penalty_precompute_start
        logger.info(f"DIAG: Graph has {n} nodes, {sum(len(adj) for adj in adjacency)} edges (deduplicated)")
        logger.info(f"DIAG: Penalty precompute time: {penalty_precompute_time:.3f}s for {len(edge_risk_cache)} unique edges")

        # --- A* helper ---
        import heapq
        def astar(start_idx, goal_idx, weight_mode):
            open_set = []
            heapq.heappush(open_set, (0, start_idx))
            came_from = {}
            g_score = {start_idx: 0.0}
            # Heuristic: Haversine distance to goal
            f_score = {start_idx: self.haversine_distance(
                nodes[start_idx].latitude, nodes[start_idx].longitude,
                nodes[goal_idx].latitude, nodes[goal_idx].longitude
            )}

            while open_set:
                current_f_score, current = heapq.heappop(open_set)

                if current == goal_idx:
                    path = []
                    while current in came_from:
                        path.append(nodes[current]) # Append the actual node object
                        current = came_from[current]
                    path.append(nodes[start_idx]) # Add start node
                    return list(reversed(path))

                for neighbor_idx, w_fast, w_safe in adjacency[current]:
                    # Use the appropriate weight based on mode
                    weight = w_fast if weight_mode == 'fast' else w_safe

                    tentative_g_score = g_score.get(current, float('inf')) + weight

                    if tentative_g_score < g_score.get(neighbor_idx, float('inf')):
                        came_from[neighbor_idx] = current
                        g_score[neighbor_idx] = tentative_g_score
                        # Update f_score
                        f_score[neighbor_idx] = tentative_g_score + self.haversine_distance(
                            nodes[neighbor_idx].latitude, nodes[neighbor_idx].longitude,
                            nodes[goal_idx].latitude, nodes[goal_idx].longitude
                        )
                        heapq.heappush(open_set, (f_score[neighbor_idx], neighbor_idx))

            # If no path found, return direct line (source to dest)
            logger.warning(f"A* algorithm failed to find a path from {nodes[start_idx].latitude},{nodes[start_idx].longitude} to {nodes[goal_idx].latitude},{nodes[goal_idx].longitude}")
            return [nodes[start_idx], nodes[goal_idx]]

        # Run A* to get sequence of SafetyNodes
        astar_start = time.time()
        fast_nodes_path_astar = astar(src_idx, dst_idx, 'fast')
        safe_nodes_path_astar = astar(src_idx, dst_idx, 'safe')
        astar_time = time.time() - astar_start

        logger.debug(f"Fastest A* path nodes: {len(fast_nodes_path_astar)}")
        logger.debug(f"Safest A* path nodes: {len(safe_nodes_path_astar)}")

        # === DIAG: Before Mapbox ===
        print(f"[DIAG] Before Mapbox — safest waypoints: {len(safe_nodes_path_astar)}, fastest waypoints: {len(fast_nodes_path_astar)}", flush=True)

        # Use Mapbox Directions API for final road geometry based on the A* paths
        def get_mapbox_route_geometry_with_chunking(node_path: List[SafetyNode]) -> List[Dict]:
            if len(node_path) < 2:
                return []

            # We'll break the node_path into chunks of up to 25 waypoints (Directions API limit)
            # Each chunk will be processed by the Directions API, and we'll concatenate the results.
            MAX_WAYPOINTS = 25
            all_waypoints = [{"latitude": node.latitude, "longitude": node.longitude} for node in node_path]

            # If we have too many waypoints, split into chunks
            if len(all_waypoints) <= MAX_WAYPOINTS:
                waypoint_chunks = [all_waypoints]
            else:
                waypoint_chunks = []
                i = 0
                while i < len(all_waypoints):
                    # Take up to MAX_WAYPOINTS points, but ensure we overlap by one point to avoid gaps
                    end_idx = min(i + MAX_WAYPOINTS, len(all_waypoints))
                    chunk = all_waypoints[i:end_idx]
                    waypoint_chunks.append(chunk)
                    # Move to next chunk, starting from the last point of current chunk to avoid gap
                    i = end_idx - 1 if end_idx < len(all_waypoints) else end_idx

            # Now process each chunk with Directions API, with fallback to straight line on failure
            full_route = []
            for chunk_idx, waypoints in enumerate(waypoint_chunks):
                if len(waypoints) < 2:
                    # Not enough points to form a route, skip
                    continue

                # Try Directions API for this chunk
                coords_str = ";".join([f"{wp['longitude']},{wp['latitude']}" for wp in waypoints])
                url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords_str}.json"
                params = {
                    "access_token": self.mapbox_token,
                    "geometries": "geojson",
                    "overview": "full",
                    "steps": "false"
                }
                try:
                    resp = requests.get(url, params=params, timeout=settings.MAPBOX_DIRECTIONS_TIMEOUT_SEC)
                    if resp.status_code != 200:
                        logger.error(f"Mapbox Directions API failed for chunk {chunk_idx}: {resp.status_code} {resp.text}")
                        raise Exception(f"HTTP {resp.status_code}")
                    data = resp.json()
                    if data.get("code") != "Ok" or not data.get("routes"):
                        logger.error(f"Mapbox Directions API returned no routes for chunk {chunk_idx}: {data}")
                        raise Exception("No routes in response")

                    route_geometry = data["routes"][0].get("geometry")
                    if not route_geometry or route_geometry.get("type") != "LineString":
                        logger.error(f"Mapbox Directions API returned invalid geometry for chunk {chunk_idx}")
                        raise Exception("Invalid geometry")

                    coords = [{"latitude": lat, "longitude": lon} for lon, lat in route_geometry.get("coordinates")]

                    # Append to full_route, avoiding duplication of the first point if not the first chunk
                    if chunk_idx == 0:
                        full_route.extend(coords)
                    else:
                        # Skip the first point to avoid duplication with the last point of the previous chunk
                        if len(coords) > 1:
                            if not full_route or not (abs(float(full_route[-1]["latitude"]) - float(coords[0]["latitude"])) < 1e-6 and abs(float(full_route[-1]["longitude"]) - float(coords[0]["longitude"])) < 1e-6):
                                full_route.extend(coords)
                        else:
                            # If the chunk only has one point (shouldn't happen because we checked len>=2), skip
                            pass

                except Exception as e:
                    logger.warning(f"Falling back to straight line for chunk {chunk_idx} due to: {e}")
                    # Fallback: straight line from first to last waypoint in the chunk
                    start_wp = waypoints[0]
                    end_wp = waypoints[-1]
                    # We'll just add the start point (if not already added) and the end point
                    if chunk_idx == 0:
                        full_route.append(start_wp)
                    # Always add the end point of the chunk
                    if len(waypoints) > 1:
                        # Avoid duplicating the point if it's the same as the last point in full_route
                        if not full_route or not (abs(float(full_route[-1]["latitude"]) - float(end_wp["latitude"])) < 1e-6 and abs(float(float(full_route[-1]["longitude"])) - float(end_wp["longitude"])) < 1e-6):
                            full_route.append(end_wp)
                    # Note: we are not adding intermediate points because we don't have them;
                    # but the straight line is just the endpoints. This is acceptable as a fallback.

            # If we have no points in the route (shouldn't happen if we had at least two points in node_path), fallback to straight line from start to end
            if len(full_route) < 2:
                start_wp = all_waypoints[0]
                end_wp = all_waypoints[-1]
                full_route = [start_wp, end_wp]

            return self.remove_consecutive_duplicates(full_route)

        # Corridor-preserving Directions API for safest route (adaptive waypoint sampling)
        _corridor_waypoints_before = 0
        _corridor_waypoints_after = 0
        _corridor_chunks = 0
        def get_mapbox_corridor_route(node_path: List[SafetyNode]) -> List[Dict]:
            nonlocal _corridor_waypoints_before, _corridor_waypoints_after, _corridor_chunks
            if len(node_path) < 2:
                return []
            # Adaptive: one intermediate point per ~8km segment length
            INTERP_EVERY_M = 8000
            dense_pts = []
            for i in range(len(node_path) - 1):
                n0 = node_path[i]
                n1 = node_path[i + 1]
                dense_pts.append({"latitude": n0.latitude, "longitude": n0.longitude})
                dist = self.haversine_distance(n0.latitude, n0.longitude, n1.latitude, n1.longitude)
                num_interp = min(3, max(0, int(dist / INTERP_EVERY_M)))
                for t in range(1, num_interp + 1):
                    frac = t / (num_interp + 1)
                    lat = n0.latitude + (n1.latitude - n0.latitude) * frac
                    lon = n0.longitude + (n1.longitude - n0.longitude) * frac
                    dense_pts.append({"latitude": lat, "longitude": lon})
            dense_pts.append({"latitude": node_path[-1].latitude, "longitude": node_path[-1].longitude})
            _corridor_waypoints_before = len(node_path)
            _corridor_waypoints_after = len(dense_pts)

            # Pass dense waypoints to Directions API with chunking
            MAX_WAYPOINTS = 24
            waypoint_chunks = []
            i = 0
            while i < len(dense_pts):
                end_idx = min(i + MAX_WAYPOINTS, len(dense_pts))
                chunk = dense_pts[i:end_idx]
                waypoint_chunks.append(chunk)
                i = end_idx - 1 if end_idx < len(dense_pts) else end_idx
            _corridor_chunks = len(waypoint_chunks)

            full_route = []
            for chunk_idx, waypoints in enumerate(waypoint_chunks):
                if len(waypoints) < 2:
                    continue
                coords_str = ";".join([f"{wp['longitude']},{wp['latitude']}" for wp in waypoints])
                url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords_str}.json"
                params = {
                    "access_token": self.mapbox_token,
                    "geometries": "geojson",
                    "overview": "full",
                    "steps": "false"
                }
                try:
                    resp = requests.get(url, params=params, timeout=settings.MAPBOX_DIRECTIONS_TIMEOUT_SEC)
                    if resp.status_code != 200:
                        raise Exception(f"HTTP {resp.status_code}")
                    data = resp.json()
                    if data.get("code") != "Ok" or not data.get("routes"):
                        raise Exception("No routes")
                    geometry = data["routes"][0].get("geometry")
                    if not geometry or geometry.get("type") != "LineString":
                        raise Exception("Invalid geometry")
                    coords = [{"latitude": lat, "longitude": lon} for lon, lat in geometry.get("coordinates")]
                    if chunk_idx == 0:
                        full_route.extend(coords)
                    else:
                        if len(coords) > 1 and full_route:
                            last = full_route[-1]
                            first = coords[0]
                            if abs(last["latitude"] - first["latitude"]) > 1e-6 or abs(last["longitude"] - first["longitude"]) > 1e-6:
                                full_route.extend(coords)
                            else:
                                full_route.extend(coords[1:])
                except Exception as e:
                    logger.warning(f"Corridor Directions chunk {chunk_idx} failed: {e}, falling back to original directions")
                    return get_mapbox_route_geometry_with_chunking(node_path)

            return self.remove_consecutive_duplicates(full_route)

        # Get the route geometry for fastest and safest paths (parallel Mapbox calls)
        mapbox_start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f_fast = executor.submit(get_mapbox_route_geometry_with_chunking, fast_nodes_path_astar)
            f_safe = executor.submit(get_mapbox_corridor_route, safe_nodes_path_astar)
            fastest_route_coords = f_fast.result()
            safest_route_coords = f_safe.result()
        if safest_route_coords is None:
            logger.info("Corridor-preserving route failed, falling back to standard Directions for safest")
            safest_route_coords = get_mapbox_route_geometry_with_chunking(safe_nodes_path_astar)
        mapbox_time = time.time() - mapbox_start

        # Compute metrics for the final routes (which are now road-matched)
        scoring_start = time.time()
        safest_avg_score, safest_distance, safest_segments = self.compute_route_metrics_from_coords(
            safest_route_coords, all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks,
            _fast_penalty_fn=fast_midpoint_penalty)
        fastest_avg_score, fastest_distance, fastest_segments = self.compute_route_metrics_from_coords(
            fastest_route_coords, all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks,
            _fast_penalty_fn=fast_midpoint_penalty)
        scoring_time = time.time() - scoring_start

        logger.debug(f"Fastest route final coords count: {len(fastest_route_coords)}")
        logger.debug(f"Safest route final coords count: {len(safest_route_coords)}")
        logger.debug(f"Fastest route average safety score: {fastest_avg_score}")
        logger.debug(f"Safest route average safety score: {safest_avg_score}")

        # Compute safety scores for the node paths (before Mapbox) for diagnostic purposes
        def coords_to_dicts(coord_list):
            return [{"latitude": lat, "longitude": lon} for lat, lon in coord_list]

        fastest_node_coords = [(node.latitude, node.longitude) for node in fast_nodes_path_astar]
        safest_node_coords = [(node.latitude, node.longitude) for node in safe_nodes_path_astar]

        fastest_node_score, _, _ = self.compute_route_metrics_from_coords(
            coords_to_dicts(fastest_node_coords), all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks,
            _fast_penalty_fn=fast_midpoint_penalty)
        safest_node_score, _, _ = self.compute_route_metrics_from_coords(
            coords_to_dicts(safest_node_coords), all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks,
            _fast_penalty_fn=fast_midpoint_penalty)

        # === BENCHMARK LOGGING ===
        nodes_loaded = len(all_safety_nodes)
        edges_created = sum(len(adj) for adj in adjacency)

        # Get coordinates from the A* paths (before Mapbox) for node count and route comparison
        def get_coords(node):
            return (node.latitude, node.longitude)
        fastest_coords = [get_coords(node) for node in fast_nodes_path_astar]
        safest_coords = [get_coords(node) for node in safe_nodes_path_astar]
        fastest_path_node_count = len(fastest_coords)
        safest_path_node_count = len(safest_coords)
        routes_identical = (frozenset(fastest_coords) == frozenset(safest_coords))

        # If the "safest" A* path actually scored lower than "fastest" after Mapbox + penalty eval,
        # use the fastest route as the safest (it IS the safest).
        if safest_avg_score < fastest_avg_score:
            logger.info(f"SAFEST_ROUTE_FALLBACK: safest_score ({safest_avg_score:.4f}) < fastest_score ({fastest_avg_score:.4f}). Using fastest route as safest.")
            safest_route_coords = fastest_route_coords
            safest_avg_score = fastest_avg_score
            safest_distance = fastest_distance
            safest_segments = fastest_segments
            safest_path_node_count = fastest_path_node_count
            safe_nodes_path_astar = fast_nodes_path_astar

        total_elapsed = time.time() - route_start_time

        # Compute avg penalty from segments (segments is list of dicts in compute_route_metrics_from_coords)
        def avg_penalty_from_segs(segs):
            if not segs:
                return 0.0
            return sum(s["penalty"] for s in segs) / len(segs)
        safest_avg_pen = avg_penalty_from_segs(safest_segments)
        fastest_avg_pen = avg_penalty_from_segs(fastest_segments)

        print("=" * 60, flush=True)
        print(f"[BENCH] Penalty precompute: {penalty_precompute_time:.3f}s", flush=True)
        print(f"[BENCH]   haversine (n={_hav_count}): {_t_hav:.3f}s", flush=True)
        print(f"[BENCH]   penalty (n={_penalty_count}): {_t_pen:.3f}s", flush=True)
        print(f"[BENCH] A* search:          {astar_time:.3f}s", flush=True)
        print(f"[BENCH] Mapbox API calls:   {mapbox_time:.3f}s", flush=True)
        print(f"[BENCH] Final scoring:      {scoring_time:.3f}s", flush=True)
        print(f"[BENCH] Total response:     {total_elapsed:.3f}s", flush=True)
        print(f"[BENCH] Corridor waypoints: {_corridor_waypoints_before}->{_corridor_waypoints_after} ({_corridor_chunks} chunks)", flush=True)
        print(f"[BENCH] Graph: {n} nodes, {edges_created} edges, {len(edge_risk_cache)} cached", flush=True)
        print(f"[DIAG] A* safest path nodes: {safest_path_node_count}", flush=True)
        print(f"[DIAG] A* fastest path nodes: {fastest_path_node_count}", flush=True)
        print(f"[DIAG] NODE_PATH SAFETY_SCORES: safest={safest_node_score:.6f}  fastest={fastest_node_score:.6f}", flush=True)
        print(f"[DIAG] GEOMETRY SAFETY_SCORES:   safest={safest_avg_score:.6f}  fastest={fastest_avg_score:.6f}", flush=True)
        print(f"[DIAG] GEOMETRY AVG_PENALTY:     safest={safest_avg_pen:.4f}  fastest={fastest_avg_pen:.4f}", flush=True)
        print(f"[DIAG] GEOMETRY SEGMENTS:        safest={len(safest_segments)}  fastest={len(fastest_segments)}", flush=True)
        print(f"[DIAG] Safest distance={safest_distance:.2f}m  Fastest distance={fastest_distance:.2f}m", flush=True)
        print(f"[DIAG] routes_identical={routes_identical}  nodes_loaded={nodes_loaded}  edges_created={edges_created}", flush=True)
        print(f"[DIAG] After Mapbox — safest coords: {len(safest_route_coords)}, fastest coords: {len(fastest_route_coords)}", flush=True)
        print(f"[DIAG] After Mapbox — safest dist: {safest_distance:.2f}m, safest score: {safest_avg_score:.6f}", flush=True)
        print(f"[DIAG] After Mapbox — fastest dist: {fastest_distance:.2f}m, fastest score: {fastest_avg_score:.6f}", flush=True)
        print(f"[DIAG] Routes differ after Mapbox: {fastest_route_coords != safest_route_coords}", flush=True)
        print("=" * 60, flush=True)

        return {
            "safest_route": safest_route_coords,
            "fastest_route": fastest_route_coords,
            "safest_distance": safest_distance,
            "fastest_distance": fastest_distance,
            "safest_safety_score": safest_avg_score,
            "fastest_safety_score": fastest_avg_score,
            "route_segments": safest_segments,  # Keeping safest segments as per previous spec
            "debug": "Mapbox Directions used for final geometry with chunking"
        }

    def _build_safety_graph(self, safety_nodes):
        """
        Build a graph (nodes and adjacency list) for the given safety nodes.
        Each node is connected to its K nearest neighbors (based on distance) within the edge threshold.
        Returns (nodes, adjacency) where nodes is the list of safety nodes (same as input) and
        adjacency is a list of lists, where adjacency[i] is a list of tuples (j, weight_fast, weight_safe)
        for the edge from node i to node j.
        """
        if not safety_nodes:
            return [], []

        K = settings.GRAPH_NEIGHBOR_COUNT
        n = len(safety_nodes)
        adjacency = [[] for _ in range(n)]

        for i in range(n):
            dists = []
            for j in range(n):
                if i == j:
                    continue
                dist = self.haversine_distance(safety_nodes[i].latitude, safety_nodes[i].longitude,
                                               safety_nodes[j].latitude, safety_nodes[j].longitude)
                if dist <= self.edge_threshold_m:
                    dists.append((dist, j))
            dists.sort(key=lambda x: x[0])

            for k in range(min(K, len(dists))):
                dist, j = dists[k]
                safety_i = safety_nodes[i].safety_score
                safety_j = safety_nodes[j].safety_score
                risk_i = (1.0 - safety_i) * settings.RISK_FACTOR_SAFETY + \
                         (1.0 if safety_nodes[i].lighting_level == LightingLevel.LOW else 0.0) * settings.RISK_FACTOR_LIGHTING + \
                         (1.0 if safety_nodes[i].crowd_density == CrowdDensity.SPARSE else 0.0) * settings.RISK_FACTOR_CROWD
                risk_j = (1.0 - safety_j) * settings.RISK_FACTOR_SAFETY + \
                         (1.0 if safety_nodes[j].lighting_level == LightingLevel.LOW else 0.0) * settings.RISK_FACTOR_LIGHTING + \
                         (1.0 if safety_nodes[j].crowd_density == CrowdDensity.SPARSE else 0.0) * settings.RISK_FACTOR_CROWD
                risk_avg = (risk_i + risk_j) / 2.0

                weight_fast = dist
                weight_safe = dist * (1.0 + settings.ROUTE_COST_ALPHA * risk_avg)

                adjacency[i].append((j, weight_fast, weight_safe))
                adjacency[j].append((i, weight_fast, weight_safe))

        return safety_nodes, adjacency

    def compute_route_metrics_from_coords(self, route_coords: List[Dict],
                                          all_safety_nodes: List[SafetyNode],
                                          all_crime_hotspots: List[CrimeHotspot],
                                          all_user_reports: List[UserReport],
                                          all_segment_risks: List[RoadSegmentRisk] = None,
                                          _fast_penalty_fn=None) -> tuple:
        """
        Computes total distance, average safety score, and segments for a given list of route coordinates.
        This is a helper function to avoid code duplication.
        If _fast_penalty_fn is provided, uses it instead of the slower calculate_penalty per segment.
        """
        if not route_coords or len(route_coords) < 2:
            return 0.0, 0.0, []

        total_distance = 0.0
        total_penalty = 0.0
        safety_scores = []
        segments = []

        for i in range(len(route_coords) - 1):
            p1 = route_coords[i]
            p2 = route_coords[i + 1]
            lat1, lon1 = p1["latitude"], p1["longitude"]
            lat2, lon2 = p2["latitude"], p2["longitude"]
            distance = self.haversine_distance(lat1, lon1, lat2, lon2)
            mid_lat = (lat1 + lat2) / 2.0
            mid_lon = (lon1 + lon2) / 2.0

            if _fast_penalty_fn is not None:
                penalty = _fast_penalty_fn(mid_lat, mid_lon)
            else:
                penalty = self.calculate_penalty(mid_lat, mid_lon, all_safety_nodes, all_crime_hotspots, all_user_reports, all_segment_risks)
                if self.is_high_risk_area(mid_lat, mid_lon, all_crime_hotspots):
                    penalty *= settings.HIGH_RISK_SEGMENT_MULTIPLIER

            total_distance += distance
            total_penalty += penalty

            safety_score = self.calculate_ai_safety_score(mid_lat, mid_lon)
            if safety_score < 0:  # AI failed or not available
                safety_score = self.calculate_safety_score(penalty)
            safety_scores.append(safety_score)

            segments.append({
                "from_coord": {"latitude": lat1, "longitude": lon1},
                "to_coord": {"latitude": lat2, "longitude": lon2},
                "distance": distance,
                "safety_score": safety_score,
                "penalty": penalty
            })
        # FIX: Calculate average penalty first, then convert to safety score
        # This is consistent with how safety score is defined for a single point
        avg_penalty = total_penalty / len(segments) if segments else 0.0
        avg_safety = self.calculate_safety_score(avg_penalty)
        return avg_safety, total_distance, segments