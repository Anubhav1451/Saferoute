import os
import sys
import math
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Ensure backend root is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import engine as app_engine
from app.db.models import Base, OSMWay, OSMWayNode, GraphNode, GraphEdge
from .base_importer import BaseImporter
from .etl_logger import EtlLogger

# Speed mapping for highway types (km/h)
DEFAULT_SPEEDS = {
    'motorway': 110.0,
    'motorway_link': 80.0,
    'trunk': 80.0,
    'trunk_link': 60.0,
    'primary': 60.0,
    'primary_link': 50.0,
    'secondary': 40.0,
    'secondary_link': 30.0,
    'tertiary': 30.0,
    'tertiary_link': 25.0,
    'unclassified': 25.0,
    'residential': 20.0,
}

# Road class mapping
ROAD_CLASS_MAP = {
    'motorway': 'HIGHWAY',
    'motorway_link': 'HIGHWAY',
    'trunk': 'HIGHWAY',
    'trunk_link': 'HIGHWAY',
    'primary': 'ARTERIAL',
    'primary_link': 'ARTERIAL',
    'secondary': 'COLLECTOR',
    'secondary_link': 'COLLECTOR',
    'tertiary': 'LOCAL',
    'tertiary_link': 'LOCAL',
    'unclassified': 'LOCAL',
    'residential': 'LOCAL',
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

class GraphBuilder(BaseImporter):
    source_name = "osm_graph_builder"
    batch_size = 5000

    def __init__(self, source_name: Optional[str] = None):
        super().__init__(source_name)
        self._node_cache: Dict[int, int] = {}  # osm_node_id -> graph_node_id
        self._edge_buffer: List[Dict] = []

    def _load_node_cache(self, session: Session):
        if not self._node_cache:
            for nid, onid in session.query(GraphNode.id, GraphNode.osm_node_id).all():
                self._node_cache[onid] = nid

    def _flush_edge_buffer(self, session: Session):
        if not self._edge_buffer:
            return
        session.bulk_insert_mappings(GraphEdge, self._edge_buffer)
        self._edge_buffer = []
        session.flush()

    def _parse_maxspeed(self, speed_str: Optional[str]) -> Optional[float]:
        if not speed_str:
            return None
        try:
            # Simple regex/split to handle "50 mph" or "50 km/h"
            # For this system, we assume km/h as standard
            val = float(speed_str.split()[0])
            return val
        except (ValueError, IndexError):
            return None

    def process_way(self, session: Session, way: OSMWay):
        nodes = self._way_nodes_cache.get(way.id, [])
        if len(nodes) < 2:
            return

        highway = way.highway
        maxspeed = self._parse_maxspeed(way.maxspeed) or DEFAULT_SPEEDS.get(highway, 25.0)
        road_class = ROAD_CLASS_MAP.get(highway, 'LOCAL')
        is_bridge = way.bridge == 'yes'
        is_tunnel = way.tunnel == 'yes'
        oneway_tag = way.oneway
        is_oneway = (oneway_tag == 'yes') or (highway in {'motorway', 'motorway_link'})

        from sqlalchemy import inspect as sa_inspect

        # Collect OSM node IDs and identify new nodes (batch-create to avoid N+1 flush)
        # Use dict to deduplicate within a single way (closed ways have duplicate first/last node)
        osm_nids = []
        new_nodes_dict = {}
        for n in nodes:
            osm_nids.append(n.osm_node_id)
            if n.osm_node_id not in self._node_cache:
                new_nodes_dict[n.osm_node_id] = {'osm_node_id': n.osm_node_id, 'latitude': n.latitude, 'longitude': n.longitude}
        new_osm_nodes = list(new_nodes_dict.values())

        # Batch-insert new nodes if any (one flush per way instead of per-node)
        if new_osm_nodes:
            session.execute(GraphNode.__table__.insert(), new_osm_nodes)
            session.flush()
            new_osm_ids = [entry['osm_node_id'] for entry in new_osm_nodes]
            if len(new_osm_ids) <= 900:
                for gn_id, gn_osm_id in session.query(GraphNode.id, GraphNode.osm_node_id).filter(
                    GraphNode.osm_node_id.in_(new_osm_ids)
                ).all():
                    self._node_cache[gn_osm_id] = gn_id
            else:
                for entry in new_osm_nodes:
                    oid = entry['osm_node_id']
                    gn = session.query(GraphNode).filter_by(osm_node_id=oid).first()
                    self._node_cache[oid] = gn.id

        # Create edges using cached IDs
        for i in range(len(osm_nids) - 1):
            src_id = self._node_cache[osm_nids[i]]
            dst_id = self._node_cache[osm_nids[i + 1]]
            if src_id == dst_id:
                continue

            length = haversine_distance(nodes[i].latitude, nodes[i].longitude,
                                        nodes[i + 1].latitude, nodes[i + 1].longitude)
            travel_time = length / (maxspeed * 0.27778)
            geom = f"LINESTRING({nodes[i].longitude} {nodes[i].latitude}, {nodes[i + 1].longitude} {nodes[i + 1].latitude})"

            edge_base = {
                'osm_way_id': way.id, 'geometry_wkt': geom,
                'length': length, 'highway': highway, 'maxspeed': maxspeed,
                'travel_time': travel_time, 'road_class': road_class,
                'is_bridge': is_bridge, 'is_tunnel': is_tunnel,
            }

            self._edge_buffer.append(dict(source_node_id=src_id, dest_node_id=dst_id,
                                          direction='FORWARD' if is_oneway else 'BIDIRECTIONAL', **edge_base))
            if not is_oneway:
                self._edge_buffer.append(dict(source_node_id=dst_id, dest_node_id=src_id,
                                              direction='BACKWARD', **edge_base))

    def _load_way_nodes_bulk(self, session: Session):
        """Pre-load all OSMWayNode records into a dict keyed by way_id to avoid N+1 queries."""
        self._way_nodes_cache: Dict[int, List[OSMWayNode]] = {}
        all_nodes = session.query(OSMWayNode).order_by(OSMWayNode.way_id, OSMWayNode.sequence).all()
        for wn in all_nodes:
            self._way_nodes_cache.setdefault(wn.way_id, []).append(wn)

    def run(self, dry_run: bool = False, metadata: Optional[dict] = None) -> Dict[str, Any]:
        if dry_run:
            self.logger.info("DRY RUN mode: no records will be written")
            return {"dry_run": True, "source": self.source_name}

        session = self.get_session()
        try:
            self._node_cache = {}
            self._load_node_cache(session)
            self._load_way_nodes_bulk(session)

            # Find unprocessed ways
            unprocessed_ways = session.query(OSMWay).filter(OSMWay.processed_at == None).all()
            total = len(unprocessed_ways)
            
            self.start_batch(total_records=total, metadata=metadata)
            
            for i, way in enumerate(unprocessed_ways):
                try:
                    self.process_way(session, way)
                    way.processed_at = datetime.utcnow()
                    
                    if (i + 1) % self.batch_size == 0:
                        self._flush_edge_buffer(session)
                        session.commit()
                        self._counters["inserted"] += self.batch_size
                        self.logger.info(f"Processed {i+1}/{total} ways...")
                except Exception as e:
                    self.logger.exception(f"Failed to process way {way.id}: {e}")
                    self._counters["errors"] += 1
            
            self._flush_edge_buffer(session)
            session.commit()
            self._counters["inserted"] = total - self._counters.get("errors", 0)
            self.end_batch("COMPLETED")
        except Exception as e:
            session.rollback()
            self.end_batch("FAILED", error_message=str(e))
            self.logger.exception(f"Graph build failed: {e}")
            raise
        finally:
            self.close_all()

        return {
            "source": self.source_name,
            "batch_id": self._batch.id if self._batch else None,
            "status": self._batch.status if self._batch else "FAILED",
            "processed_ways": self._counters.get("inserted", 0),
            "errors": self._counters.get("errors", 0),
            "duration_seconds": self._batch.duration_seconds if self._batch else 0.0,
        }

if __name__ == "__main__":
    builder = GraphBuilder()
    result = builder.run()
    print(result)
