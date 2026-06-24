# app/services/routing.py
import math
import logging
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate, RouteSegment
from app.core.config import settings

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

    def __init__(self, db: Session):
        self.db = db

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

    def calculate_penalty(self, lat: float, lon: float,
                         safety_nodes: List[SafetyNode],
                         crime_hotspots: List[CrimeHotspot],
                         user_reports: List[UserReport]) -> float:
        """
        Calculate dynamic penalty for a coordinate based on:
        - Crime hotspots (high severity = heavy penalty)
        - Safety nodes with low lighting or sparse crowd (medium penalty)
        - Recent active user reports (dynamic penalty)

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
            radius_meters = settings.DEFAULT_SEARCH_RADIUS_METERS

        # Simple bounding box query for nearby data
        lat_delta = radius_meters / 111000  # Approximate degrees per meter
        lon_delta = radius_meters / (111000 * math.cos(math.radians(lat)))

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

        return (safety_nodes, crime_hotspots, user_reports)

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

    def calculate_route_cost(self, path: list,
                           safety_nodes: list,
                           crime_hotspots: list,
                           user_reports: list,
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
            penalty = self.calculate_penalty(mid_lat, mid_lon, safety_nodes, crime_hotspots, user_reports)

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
            segments.append(RouteSegment(
                from_coord=from_coord,
                to_coord=to_coord,
                distance=distance,
                safety_score=safety_score,
                penalty=penalty
            ))

        # Additional penalty if route passes through multiple high-risk segments
        if high_risk_segments > 0:
            total_penalty *= (1 + (high_risk_segments * settings.HIGH_RISK_SEGMENT_ADDITIONAL_FACTOR))

        # Weighted cost: safety_weight * penalty + (1 - safety_weight) * distance
        weighted_cost = (weight * total_penalty) + ((1 - weight) * total_distance)

        return (float(weighted_cost), float(total_distance), [s for s in segments])

    def find_safest_route(self, source: Coordinate, destination: Coordinate,
                          safety_weight: float = None) -> dict:
        """
        Find the safest route using a simplified A* approach with multiple path variations.
        Returns both safest and fastest routes.
        """
        # Use default safety weight from settings if not provided
        if safety_weight is None:
            sw = settings.DEFAULT_SAFETY_WEIGHT
        else:
            sw = float(safety_weight)

        # Get safety data for the entire area
        # Use a dynamic radius based on distance between points
        base_radius = settings.BASE_SEARCH_RADIUS_METERS
        center_lat = (source.latitude + destination.latitude) / 2
        center_lon = (source.longitude + destination.longitude) / 2

        all_safety_nodes, all_crime_hotspots, all_user_reports = self.get_nearby_safety_data(
            center_lat, center_lon, radius_meters=base_radius
        )

        # Generate multiple path variations
        num_variations = settings.PATH_VARIATION_COUNT
        paths = []

        # Direct path
        direct_path = self.generate_intermediate_points(source, destination, num_points=20)
        paths.append(direct_path)

        # Generate variations with slight offsets
        for i in range(num_variations - 1):
            offset_lat = (i - num_variations // 2) * 0.002
            offset_lon = (i - num_variations // 2) * 0.002

            # Create offset points
            offset_source = Coordinate(
                latitude=source.latitude + offset_lat,
                longitude=source.longitude + offset_lon
            )
            offset_dest = Coordinate(
                latitude=destination.latitude + offset_lat,
                longitude=destination.longitude + offset_lon
            )

            offset_path = self.generate_intermediate_points(
                offset_source,
                offset_dest,
                num_points=20
            )
            paths.append(offset_path)

        # Calculate costs for all paths
        path_costs = []
        for path in paths:
            cost, distance, segments = self.calculate_route_cost(
                path, all_safety_nodes, all_crime_hotspots, all_user_reports, sw
            )
            # Ensure proper types
            path_costs.append((float(cost), float(distance), path, [s for s in segments]))

        # Sort by cost (safest first when safety_weight is high)
        if not path_costs:
            # Fallback if no paths calculated
            direct_distance = self.haversine_distance(
                source.latitude, source.longitude, destination.latitude, destination.longitude
            )
            return {
                "safest_route": [{"latitude": float(s.latitude), "longitude": float(s.longitude)} for s in [source, destination]],
                "fastest_route": [{"latitude": float(f.latitude), "longitude": float(f.longitude)} for f in [source, destination]],
                "safest_distance": float(direct_distance),
                "fastest_distance": float(direct_distance),
                "safest_safety_score": 0.5,
                "fastest_safety_score": 0.5,
                "route_segments": []
            }

        path_costs.sort(key=lambda x: x[0])

        # Safest route (lowest weighted cost)
        sc, sd, sp, ss = path_costs[0]

        # Fastest route (lowest distance)
        pcd = sorted(path_costs, key=lambda x: x[1])
        if not pcd:
            # Fallback
            fdc, ffc, fp, fs = (
                self.haversine_distance(source.latitude, source.longitude, destination.latitude, destination.longitude),
                0.0,
                [source, destination],
                []
            )
        else:
            fdc, ffc, fp, fs = pcd[0]

        # Calculate average safety scores
        def safe_avg_score(segment_list):
            if not segment_list or len(segment_list) == 0:
                return 0.0
            try:
                return sum(float(seg.safety_score) for seg in segment_list) / len(segment_list)
            except (ValueError, TypeError, AttributeError):
                return 0.0

        ass = safe_avg_score(ss)
        afs = safe_avg_score(fs)

        return {
            "safest_route": [{"latitude": float(p.latitude), "longitude": float(p.longitude)} for p in (sp if sp else [])],
            "fastest_route": [{"latitude": float(p.latitude), "longitude": float(p.longitude)} for p in (fp if fp else [])],
            "safest_distance": float(sd),
            "fastest_distance": float(fdc),
            "safest_safety_score": float(ass),
            "fastest_safety_score": float(afs),
            "route_segments": [
                {
                    "from_coord": {"latitude": float(seg.from_coord.latitude), "longitude": float(seg.from_coord.longitude)},
                    "to_coord": {"latitude": float(seg.to_coord.latitude), "longitude": float(seg.to_coord.longitude)},
                    "distance": float(seg.distance),
                    "safety_score": float(seg.safety_score),
                    "penalty": float(seg.penalty)
                } for seg in ss if seg is not None
            ]
        }