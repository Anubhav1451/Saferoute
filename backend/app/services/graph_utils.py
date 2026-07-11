import math
import logging
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import GraphNode, GraphEdge, OSMWayNode

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing between two points in degrees."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

class GraphSpatialIndex:
    """
    Provides fast spatial lookups for GraphNodes and GraphEdges.
    Uses a simple grid-based index for SQLite performance.
    """
    def __init__(self, session: Session, grid_size_deg: float = 0.01):
        self.session = session
        self.grid_size = grid_size_deg
        self._node_grid: Dict[Tuple[int, int], List[int]] = {}
        self._edge_grid: Dict[Tuple[int, int], List[int]] = {}
        self._node_coords: Dict[int, Tuple[float, float]] = {}
        self._edge_coords: Dict[int, Tuple[float, float]] = {}
        self.rebuild()

    def _get_grid_coords(self, lat: float, lon: float) -> Tuple[int, int]:
        return int(lat / self.grid_size), int(lon / self.grid_size)

    def rebuild(self):
        """Build the spatial index from DB."""
        self._node_grid.clear()
        self._edge_grid.clear()
        self._node_coords.clear()
        self._edge_coords.clear()
        
        # Index nodes
        nodes = self.session.query(GraphNode.id, GraphNode.latitude, GraphNode.longitude).all()
        for nid, lat, lon in nodes:
            cell = self._get_grid_coords(lat, lon)
            self._node_grid.setdefault(cell, []).append(nid)
            self._node_coords[nid] = (lat, lon)
            
        # Index edges using midpoint
        edges = self.session.query(GraphEdge.id, GraphEdge.mid_lat, GraphEdge.mid_lon).all()
        for eid, lat, lon in edges:
            if lat is not None and lon is not None:
                cell = self._get_grid_coords(lat, lon)
                self._edge_grid.setdefault(cell, []).append(eid)
                self._edge_coords[eid] = (lat, lon)
        
        logger.info(f"Spatial index rebuilt: {len(nodes)} nodes, {len(edges)} edges indexed.")

    def get_nodes_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[int]:
        results = self.session.query(GraphNode.id).filter(
            GraphNode.latitude >= min_lat, GraphNode.latitude <= max_lat,
            GraphNode.longitude >= min_lon, GraphNode.longitude <= max_lon
        ).all()
        return [r[0] for r in results]

    def get_edges_in_bbox(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[int]:
        results = self.session.query(GraphEdge.id).filter(
            GraphEdge.mid_lat >= min_lat, GraphEdge.mid_lat <= max_lat,
            GraphEdge.mid_lon >= min_lon, GraphEdge.mid_lon <= max_lon
        ).all()
        return [r[0] for r in results]

    def nearest_node(self, lat: float, lon: float, radius_m: float = 1000.0) -> Optional[int]:
        grid_radius = int(radius_m / (self.grid_size * 111000)) + 1
        cx, cy = self._get_grid_coords(lat, lon)

        best_node = None
        min_dist = float('inf')

        for x in range(cx - grid_radius, cx + grid_radius + 1):
            for y in range(cy - grid_radius, cy + grid_radius + 1):
                for nid in self._node_grid.get((x, y), []):
                    coords = self._node_coords.get(nid)
                    if coords is None:
                        continue
                    dist = haversine_distance(lat, lon, coords[0], coords[1])
                    if dist < min_dist:
                        min_dist = dist
                        best_node = nid

        return best_node if min_dist <= radius_m else None

    def nearest_edge(self, lat: float, lon: float, radius_m: float = 100.0) -> Optional[int]:
        grid_radius = int(radius_m / (self.grid_size * 111000)) + 1
        cx, cy = self._get_grid_coords(lat, lon)

        best_edge = None
        min_dist = float('inf')

        for x in range(cx - grid_radius, cx + grid_radius + 1):
            for y in range(cy - grid_radius, cy + grid_radius + 1):
                for eid in self._edge_grid.get((x, y), []):
                    coords = self._edge_coords.get(eid)
                    if coords is None:
                        continue
                    dist = haversine_distance(lat, lon, coords[0], coords[1])
                    if dist < min_dist:
                        min_dist = dist
                        best_edge = eid

        return best_edge if min_dist <= radius_m else None

def get_edge_by_osm_id(session: Session, osm_way_id: int) -> List[GraphEdge]:
    return session.query(GraphEdge).filter_by(osm_way_id=osm_way_id).all()

def get_edges_within_radius(session: Session, spatial_index: GraphSpatialIndex, 
                            lat: float, lon: float, radius_m: float) -> List[GraphEdge]:
    deg_radius = radius_m / 111000.0
    edge_ids = spatial_index.get_edges_in_bbox(
        lat - deg_radius, lon - deg_radius,
        lat + deg_radius, lon + deg_radius
    )
    
    if not edge_ids:
        return []

    filtered_ids = [eid for eid in edge_ids
                    if eid in spatial_index._edge_coords and
                    haversine_distance(lat, lon,
                                       spatial_index._edge_coords[eid][0],
                                       spatial_index._edge_coords[eid][1]) <= radius_m]
    if not filtered_ids:
        return []

    edges = session.query(GraphEdge).filter(GraphEdge.id.in_(filtered_ids[:900])).all()
    return edges
