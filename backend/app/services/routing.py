import math
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import SafetyNode, CrimeHotspot, UserReport, LightingLevel, CrowdDensity, SeverityLevel
from app.schemas.routing import Coordinate, RouteSegment


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
        """
        penalty = 0.0
        
        # Crime hotspot penalty
        for hotspot in crime_hotspots:
            distance = self.haversine_distance(lat, lon, hotspot.latitude, hotspot.longitude)
            if distance < hotspot.radius:
                if hotspot.severity == SeverityLevel.HIGH:
                    penalty += 500.0  # Heavy penalty for high severity
                elif hotspot.severity == SeverityLevel.MEDIUM:
                    penalty += 250.0
                else:
                    penalty += 100.0
        
        # Safety node penalty
        for node in safety_nodes:
            distance = self.haversine_distance(lat, lon, node.latitude, node.longitude)
            if distance < 100:  # Within 100 meters
                if node.lighting_level == LightingLevel.LOW:
                    penalty += 50.0  # Medium penalty for low lighting
                if node.crowd_density == CrowdDensity.SPARSE:
                    penalty += 30.0  # Medium penalty for sparse crowd
                # Bonus for high safety score
                if node.safety_score > 0.8:
                    penalty -= 20.0  # Reduce penalty for very safe areas
        
        # User report penalty (dynamic based on recency)
        recent_threshold = datetime.utcnow() - timedelta(days=7)
        for report in user_reports:
            if report.is_active and report.timestamp > recent_threshold:
                distance = self.haversine_distance(lat, lon, report.latitude, report.longitude)
                if distance < 150:  # Within 150 meters
                    # More recent reports have higher penalty
                    days_old = (datetime.utcnow() - report.timestamp).days
                    penalty += (100.0 / (days_old + 1))  # Decay over time
        
        return max(0, penalty)  # Ensure penalty is non-negative
    
    def get_nearby_safety_data(self, lat: float, lon: float, radius_meters: float = 2000) -> Tuple:
        """Get safety data within radius of a coordinate"""
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
        
        return safety_nodes, crime_hotspots, user_reports
    
    def generate_intermediate_points(self, start: Coordinate, end: Coordinate, num_points: int = 10) -> List[Coordinate]:
        """Generate intermediate points between start and end for pathfinding"""
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            lat = start.latitude + t * (end.latitude - start.latitude)
            lon = start.longitude + t * (end.longitude - start.longitude)
            points.append(Coordinate(latitude=lat, longitude=lon))
        return points
    
    def calculate_route_cost(self, path: List[Coordinate], 
                           safety_nodes: List[SafetyNode],
                           crime_hotspots: List[CrimeHotspot],
                           user_reports: List[UserReport],
                           safety_weight: float = 0.7) -> Tuple[float, float, List[RouteSegment]]:
        """
        Calculate total cost of a route considering distance and safety penalties.
        Returns (total_cost, total_distance, segments)
        """
        total_distance = 0.0
        total_penalty = 0.0
        segments = []
        
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
            
            total_distance += distance
            total_penalty += penalty
            
            # Calculate safety score for this segment (inverse of penalty)
            safety_score = max(0, 1.0 - (penalty / 500.0))
            
            segments.append(RouteSegment(
                from_coord=from_coord,
                to_coord=to_coord,
                distance=distance,
                safety_score=safety_score,
                penalty=penalty
            ))
        
        # Weighted cost: safety_weight * penalty + (1 - safety_weight) * distance
        weighted_cost = (safety_weight * total_penalty) + ((1 - safety_weight) * total_distance)
        
        return weighted_cost, total_distance, segments
    
    def find_safest_route(self, source: Coordinate, destination: Coordinate, 
                          safety_weight: float = 0.7) -> Dict:
        """
        Find the safest route using a simplified A* approach with multiple path variations.
        Returns both safest and fastest routes.
        """
        # Get safety data for the entire area
        all_safety_nodes, all_crime_hotspots, all_user_reports = self.get_nearby_safety_data(
            (source.latitude + destination.latitude) / 2,
            (source.longitude + destination.longitude) / 2,
            radius_meters=5000
        )
        
        # Generate multiple path variations
        num_variations = 5
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
            
            offset_path = self.generate_intermediate_points(offset_source, offset_dest, num_points=20)
            paths.append(offset_path)
        
        # Calculate costs for all paths
        path_costs = []
        for path in paths:
            cost, distance, segments = self.calculate_route_cost(
                path, all_safety_nodes, all_crime_hotspots, all_user_reports, safety_weight
            )
            path_costs.append((cost, distance, path, segments))
        
        # Sort by cost (safest first when safety_weight is high)
        path_costs.sort(key=lambda x: x[0])
        
        # Safest route (lowest weighted cost)
        safest_cost, safest_distance, safest_path, safest_segments = path_costs[0]
        
        # Fastest route (lowest distance)
        path_costs_by_distance = sorted(path_costs, key=lambda x: x[1])
        fastest_distance, fastest_cost, fastest_path, fastest_segments = path_costs_by_distance[0][1], path_costs_by_distance[0][0], path_costs_by_distance[0][2], path_costs_by_distance[0][3]
        
        # Calculate average safety scores
        avg_safest_safety = sum(seg.safety_score for seg in safest_segments) / len(safest_segments) if safest_segments else 0
        avg_fastest_safety = sum(seg.safety_score for seg in fastest_segments) / len(fastest_segments) if fastest_segments else 0
        
        return {
            "safest_route": safest_path,
            "fastest_route": fastest_path,
            "safest_distance": safest_distance,
            "fastest_distance": fastest_distance,
            "safest_safety_score": avg_safest_safety,
            "fastest_safety_score": avg_fastest_safety,
            "route_segments": safest_segments
        }
