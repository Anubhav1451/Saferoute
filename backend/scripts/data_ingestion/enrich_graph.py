import os
import sys
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

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

class GraphEnricher(BaseImporter):
    source_name = "graph_enricher"
    batch_size = 5000

    def __init__(self, source_name: Optional[str] = None):
        super().__init__(source_name)
        self._way_cache: Dict[int, OSMWay] = {}
        self._node_cache: Dict[int, GraphNode] = {}

    def _load_caches(self, session: Session):
        """Load OSMWay and GraphNode data as lightweight dicts instead of full ORM objects."""
        if not self._way_cache:
            self._way_cache = {}
            for w in session.query(OSMWay.id, OSMWay.highway, OSMWay.lanes, OSMWay.oneway).yield_per(50000):
                self._way_cache[w.id] = w
            self.logger.info(f"Loaded {len(self._way_cache):,} OSMWay records into cache")
        if not self._node_cache:
            self._node_cache = {}
            for n in session.query(GraphNode.id, GraphNode.osm_node_id, GraphNode.latitude, GraphNode.longitude).yield_per(50000):
                self._node_cache[n.id] = n
            self.logger.info(f"Loaded {len(self._node_cache):,} GraphNode records into cache")

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
            MAX_ITERATIONS = 500  # ETL-4: guard against infinite loop
            iteration = 0
            while iteration < MAX_ITERATIONS:
                iteration += 1
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

                        phi1, phi2 = math.radians(lat1), math.radians(lat2)
                        dlambda = math.radians(lon2 - lon1)
                        y = math.sin(dlambda) * math.cos(phi2)
                        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
                        heading = (math.degrees(math.atan2(y, x)) + 360) % 360

                        updates.append({
                            "id": edge.id,
                            "priority": PRIORITY_MAP.get(highway, 10),
                            "speed_priority": PRIORITY_MAP.get(highway, 10),
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

            if iteration >= MAX_ITERATIONS:
                self.logger.warning("Enrichment stopped: hit MAX_ITERATIONS=%d with %d edges remaining", MAX_ITERATIONS, total - enriched)

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
