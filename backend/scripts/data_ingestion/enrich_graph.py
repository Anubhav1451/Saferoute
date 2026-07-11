import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Ensure backend root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from app.db.session import engine as app_engine
from app.db.models import Base, OSMWay, OSMWayNode, GraphNode, GraphEdge
from .base_importer import BaseImporter
from .etl_logger import EtlLogger

# Priority mapping for highway types
PRIORITY_MAP = {
    'motorway': 1,
    'motorway_link': 2,
    'trunk': 2,
    'trunk_link': 3,
    'primary': 3,
    'primary_link': 4,
    'secondary': 4,
    'secondary_link': 5,
    'tertiary': 5,
    'tertiary_link': 6,
    'unclassified': 6,
    'residential': 7,
}

# Speed priority mapping
SPEED_PRIORITY_MAP = {
    'motorway': 1,
    'motorway_link': 2,
    'trunk': 2,
    'trunk_link': 3,
    'primary': 3,
    'primary_link': 4,
    'secondary': 4,
    'secondary_link': 5,
    'tertiary': 5,
    'tertiary_link': 6,
    'unclassified': 6,
    'residential': 7,
}

class GraphEnricher(BaseImporter):
    source_name = "graph_enricher"
    batch_size = 5000

    def __init__(self, source_name: Optional[str] = None):
        super().__init__(source_name)
        self._way_cache: Dict[int, OSMWay] = {}
        self._node_cache: Dict[int, GraphNode] = {}

    def _load_caches(self, session: Session):
        if not self._way_cache:
            for way in session.query(OSMWay).all():
                self._way_cache[way.id] = way
        if not self._node_cache:
            for node in session.query(GraphNode).all():
                self._node_cache[node.id] = node

    def _calculate_edge_geometry(self, session: Session, edge: GraphEdge) -> Tuple[float, float, float, float, float, float]:
        node_src = self._node_cache.get(edge.source_node_id)
        node_dst = self._node_cache.get(edge.dest_node_id)
        if node_src is None or node_dst is None:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        lat1, lon1 = node_src.latitude, node_src.longitude
        lat2, lon2 = node_dst.latitude, node_dst.longitude
        
        # Midpoint
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        
        # BBox
        min_lat, max_lat = min(lat1, lat2), max(lat1, lat2)
        min_lon, max_lon = min(lon1, lon2), max(lon1, lon2)
        
        # Heading (Bearing)
        import math
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dlambda = math.radians(lon2 - lon1)
        y = math.sin(dlambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
        heading = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        return mid_lat, mid_lon, min_lat, min_lon, max_lat, max_lon, heading

    def enrich_edge(self, session: Session, edge: GraphEdge):
        way = self._way_cache.get(edge.osm_way_id)
        if not way:
            return

        # Basic attributes from OSMWay tags
        # These were already in OSMWay but we migrate them to GraphEdge for routing speed
        highway = way.highway
        
        edge.priority = PRIORITY_MAP.get(highway, 10)
        edge.speed_priority = SPEED_PRIORITY_MAP.get(highway, 10)
        edge.access = way.tags.get('access') if hasattr(way, 'tags') else None 
        # Note: OSMWay in our model doesn't have a 'tags' JSON field yet, 
        # but we have explicit columns. We should use the columns.
        
        # Fixing the attribute access based on the model
        edge.roundabout = (way.highway == 'roundabout') # Simple approximation
        edge.surface = None # Need to add surface to OSMWay model if we want it
        edge.smoothness = None
        edge.lit = None
        edge.lanes = int(way.lanes) if way.lanes and way.lanes.isdigit() else None
        
        # Spatial properties
        mid_lat, mid_lon, min_lat, min_lon, max_lat, max_lon, heading = self._calculate_edge_geometry(session, edge)
        edge.mid_lat = mid_lat
        edge.mid_lon = mid_lon
        edge.bbox_min_lat = min_lat
        edge.bbox_min_lon = min_lon
        edge.bbox_max_lat = max_lat
        edge.bbox_max_lon = max_lon
        edge.heading = heading

    def run(self, dry_run: bool = False, metadata: Optional[dict] = None) -> Dict[str, Any]:
        if dry_run:
            self.logger.info("DRY RUN mode: no records will be written")
            return {"dry_run": True, "source": self.source_name}

        session = self.get_session()
        try:
            self._way_cache = {}
            self._node_cache = {}
            self._load_caches(session)

            total = session.query(GraphEdge).filter(GraphEdge.mid_lat == None).count()
            self.start_batch(total_records=total, metadata=metadata)

            bulk_chunk = 5000
            enriched = 0
            while True:
                edges = session.query(GraphEdge).filter(GraphEdge.mid_lat == None).limit(bulk_chunk).all()
                if not edges:
                    break

                updates = []
                for edge in edges:
                    try:
                        way = self._way_cache.get(edge.osm_way_id)
                        if not way:
                            continue
                        highway = way.highway
                        node_src = self._node_cache.get(edge.source_node_id)
                        node_dst = self._node_cache.get(edge.dest_node_id)
                        if node_src is None or node_dst is None:
                            continue

                        lat1, lon1 = node_src.latitude, node_src.longitude
                        lat2, lon2 = node_dst.latitude, node_dst.longitude
                        mid_lat = (lat1 + lat2) / 2
                        mid_lon = (lon1 + lon2) / 2

                        import math
                        phi1, phi2 = math.radians(lat1), math.radians(lat2)
                        dlambda = math.radians(lon2 - lon1)
                        y = math.sin(dlambda) * math.cos(phi2)
                        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
                        heading = (math.degrees(math.atan2(y, x)) + 360) % 360

                        updates.append({
                            "id": edge.id,
                            "priority": PRIORITY_MAP.get(highway, 10),
                            "speed_priority": SPEED_PRIORITY_MAP.get(highway, 10),
                            "mid_lat": mid_lat,
                            "mid_lon": mid_lon,
                            "heading": heading,
                            "bbox_min_lat": min(lat1, lat2),
                            "bbox_min_lon": min(lon1, lon2),
                            "bbox_max_lat": max(lat1, lat2),
                            "bbox_max_lon": max(lon1, lon2),
                            "roundabout": (highway == "roundabout"),
                        })
                    except Exception as e:
                        self.logger.exception(f"Failed to enrich edge {edge.id}: {e}")
                        self._counters["errors"] += 1

                if updates:
                    session.bulk_update_mappings(GraphEdge, updates)
                    session.commit()
                enriched += len(updates)
                self.logger.info(f"Enriched {enriched}/{total} edges...")

            self._counters["inserted"] = enriched
            self.end_batch("COMPLETED")
        except Exception as e:
            session.rollback()
            self.end_batch("FAILED", error_message=str(e))
            self.logger.exception(f"Enrichment failed: {e}")
            raise
        finally:
            self.close_all()

        return {
            "source": self.source_name,
            "batch_id": self._batch.id if self._batch else None,
            "status": self._batch.status if self._batch else "FAILED",
            "enriched_edges": self._counters.get("inserted", 0),
            "errors": self._counters.get("errors", 0),
            "duration_seconds": self._batch.duration_seconds if self._batch else 0.0,
        }

if __name__ == "__main__":
    enricher = GraphEnricher()
    result = enricher.run()
    print(result)
