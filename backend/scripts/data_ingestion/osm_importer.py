import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Ensure backend/ and package dir are on path for direct execution
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_DIR, '..', '..'))

from sqlalchemy.orm import Session
import osmium

from app.db.session import engine as app_engine
from app.db.models import Base, OSMWay, OSMWayNode
from app.core.config import settings
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PACKAGE_DIR)
from base_importer import BaseImporter
from etl_logger import EtlLogger

# Use configurable values from settings
DRIVABLE_HIGHWAYS = settings.OSM_DRIVABLE_HIGHWAYS


class OSMHandler(osmium.SimpleHandler):
    def __init__(self, importer: 'OSMImporter'):
        super().__init__()
        self.importer = importer
        self.current_batch_ways = []
        self._invalid_coords = 0

    def way(self, w):
        highway = w.tags.get('highway')
        if not highway or highway not in DRIVABLE_HIGHWAYS:
            return

        way_data = {
            'osm_id': w.id,
            'highway': highway,
            'name': w.tags.get('name'),
            'ref': w.tags.get('ref'),
            'oneway': w.tags.get('oneway'),
            'maxspeed': w.tags.get('maxspeed'),
            'lanes': w.tags.get('lanes'),
            'bridge': w.tags.get('bridge'),
            'tunnel': w.tags.get('tunnel'),
        }

        nodes = []
        for node_ref in w.nodes:
            try:
                loc = node_ref.location
                if loc is None or not loc.valid():
                    self._invalid_coords += 1
                    continue
                lat = float(loc.lat)
                lon = float(loc.lon)
                if -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0.0 and lon == 0.0):
                    nodes.append({
                        'osm_node_id': node_ref.ref,
                        'latitude': lat,
                        'longitude': lon
                    })
                else:
                    self._invalid_coords += 1
            except (RuntimeError, TypeError, ValueError, AttributeError):
                self._invalid_coords += 1

        if not nodes:
            return

        wkt = "LINESTRING (" + ", ".join([f"{n['longitude']} {n['latitude']}" for n in nodes]) + ")"
        way_data['geometry_wkt'] = wkt

        self.current_batch_ways.append(way_data)
        self.importer.add_to_processing_queue(w.id, nodes)

        if len(self.current_batch_ways) >= self.importer.batch_size:
            self.importer.flush_batch(self.current_batch_ways)
            self.current_batch_ways = []


class OSMImporter(BaseImporter):
    source_name = "osm_roads"
    batch_size = 10

    def __init__(self, source_name: Optional[str] = None):
        super().__init__(source_name)
        self.processing_queue = {}
        self._invalid_coords = 0

    def add_to_processing_queue(self, osm_id: int, nodes: List[Dict[str, Any]]):
        self.processing_queue[osm_id] = nodes

    def flush_batch(self, ways_data: List[Dict[str, Any]]):
        session = self.get_session()
        try:
            osm_ids = [d['osm_id'] for d in ways_data]
            existing_ids = {r[0] for r in session.query(OSMWay.osm_id).filter(OSMWay.osm_id.in_(osm_ids)).all()}

            new_ways = []
            for data in ways_data:
                if data['osm_id'] not in existing_ids:
                    new_ways.append(data)

            if new_ways:
                session.bulk_insert_mappings(OSMWay, new_ways)
                session.flush()

            id_map = {r[0]: r[1] for r in session.query(OSMWay.osm_id, OSMWay.id).filter(OSMWay.osm_id.in_(osm_ids)).all()}

            all_nodes = []
            for osm_id in osm_ids:
                nodes = self.processing_queue.get(osm_id, [])
                way_id = id_map.get(osm_id)
                if way_id is not None:
                    for i, n_data in enumerate(nodes):
                        all_nodes.append({
                            'way_id': way_id,
                            'osm_node_id': n_data['osm_node_id'],
                            'sequence': i,
                            'latitude': n_data['latitude'],
                            'longitude': n_data['longitude']
                        })

            if all_nodes:
                session.bulk_insert_mappings(OSMWayNode, all_nodes)

            session.commit()
            self._counters["inserted"] += len(ways_data)

            for osm_id in osm_ids:
                self.processing_queue.pop(osm_id, None)

        except Exception as e:
            session.rollback()
            self.logger.exception(f"Error flushing batch: {e}")
            self._counters["errors"] += len(ways_data)
            raise
        finally:
            session.close()

    def run(self, filepath: Optional[str] = None, dry_run: bool = False,
            rows: Optional[List[Dict[str, Any]]] = None,
            metadata: Optional[dict] = None) -> Dict[str, Any]:

        if not filepath:
            raise ValueError("filepath is required for OSMImporter")

        if dry_run:
            self.logger.info("DRY RUN mode: no records will be written")
            return {"dry_run": True, "source": self.source_name}

        self.start_batch(source_file=filepath, metadata=metadata)

        try:
            handler = OSMHandler(self)
            handler.apply_file(filepath, locations=True)

            if handler.current_batch_ways:
                self.flush_batch(handler.current_batch_ways)

            self._invalid_coords = handler._invalid_coords
            self.end_batch("COMPLETED")
        except Exception as e:
            self.end_batch("FAILED", error_message=str(e))
            self.logger.exception(f"OSM Import failed: {e}")
            raise
        finally:
            self.close_all()

        return {
            "source": self.source_name,
            "batch_id": self._batch.id if self._batch else None,
            "status": self._batch.status if self._batch else "FAILED",
            "inserted": self._counters.get("inserted", 0),
            "errors": self._counters.get("errors", 0),
            "invalid_coords": self._invalid_coords,
            "duration_seconds": self._batch.duration_seconds if self._batch else 0.0,
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to .osm.pbf file")
    args = parser.parse_args()

    importer = OSMImporter()
    result = importer.run(filepath=args.file)
    print(result)
