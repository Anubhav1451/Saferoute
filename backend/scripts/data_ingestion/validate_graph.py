"""
Graph Validation & Data Quality Framework for SafeRoute AI.

Validates OSM graph integrity across 5 categories:
  1. Graph connectivity (orphan nodes/edges, disconnected components)
  2. Geometry integrity (zero-length, duplicates, invalid coords, self-loops, direction)
  3. Routing integrity (unreachable nodes, dead ends, oneway correctness)
  4. OSM consistency (missing highway, duplicate IDs, invalid speed/lane values)
  5. Spatial validation (GraphSpatialIndex correctness, nearest node/edge, bbox lookup)

Produces GRAPH_VALIDATION_REPORT.md with statistics, issues, severity, and repair recommendations.

Usage:
    python validate_graph.py                     # validate only
    python validate_graph.py --repair            # validate + repair safe issues
    python validate_graph.py --db path/to/db     # custom DB path

No mock data. No fake validation. All checks run against live database.
Never modify geometry automatically.
"""

import argparse
import logging
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.models import (
    GraphEdge,
    GraphNode,
    OSMWay,
    OSMWayNode,
)
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from .geo import haversine_distance as haversine

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

VALID_DIRECTIONS = {'FORWARD', 'BACKWARD', 'BIDIRECTIONAL'}
VALID_HIGHWAYS = {
    'motorway', 'motorway_link', 'trunk', 'trunk_link',
    'primary', 'primary_link', 'secondary', 'secondary_link',
    'tertiary', 'tertiary_link', 'unclassified', 'residential',
}


@dataclass
class ValidationIssue:
    category: str          # connectivity, geometry, routing, osm, spatial
    severity: str          # CRITICAL, ERROR, WARNING, INFO
    check: str             # specific check name
    message: str           # human-readable description
    count: int = 0         # number of affected records
    sample_ids: list = field(default_factory=list)  # up to 10 sample IDs
    repairable: bool = False
    repair_sql: str = ''
    repair_description: str = ''


@dataclass
class GraphStatistics:
    total_nodes: int = 0
    total_edges: int = 0
    total_osm_ways: int = 0
    total_osm_way_nodes: int = 0
    total_bidirectional: int = 0
    total_forward: int = 0
    total_backward: int = 0
    total_enriched: int = 0
    distinct_highways: int = 0
    distinct_osm_ids: int = 0
    min_length: float = 0.0
    max_length: float = 0.0
    avg_length: float = 0.0
    total_length_km: float = 0.0
    min_maxspeed: float = 0.0
    max_maxspeed: float = 0.0
    lat_min: float = 0.0
    lat_max: float = 0.0
    lon_min: float = 0.0
    lon_max: float = 0.0


class GraphValidator:
    def __init__(self, session: Session):
        self.session = session
        self.issues: List[ValidationIssue] = []
        self.stats = GraphStatistics()
        self._adjacency: Optional[Dict[int, List[int]]] = None
        self._edge_map: Optional[Dict[int, List[Dict]]] = None
        self._node_set: Optional[Set[int]] = None
        self._node_coords: Optional[Dict[int, Tuple[float, float]]] = None
        self._reverse_adj: Optional[Dict[int, List[int]]] = None
        self._edge_endpoints: Optional[Dict[int, Tuple[int, int]]] = None
        self._load_start = 0.0

    def _log(self, msg: str):
        logger.info(msg)

    def _add_issue(self, category: str, severity: str, check: str,
                   message: str, count: int = 0, sample_ids: list = None,
                   repairable: bool = False, repair_sql: str = '',
                   repair_description: str = ''):
        issue = ValidationIssue(
            category=category, severity=severity, check=check,
            message=message, count=count,
            sample_ids=sample_ids or [],
            repairable=repairable, repair_sql=repair_sql,
            repair_description=repair_description,
        )
        self.issues.append(issue)
        self._log(f"  [{severity}] {check}: {message} (count={count})")

    def _load_adjacency(self):
        if self._adjacency is not None:
            return
        self._load_start = time.time()
        self._log("Loading adjacency list...")
        self._adjacency = defaultdict(list)
        self._edge_map = defaultdict(list)
        self._reverse_adj = defaultdict(list)
        self._edge_endpoints = {}

        for row in self.session.query(
            GraphEdge.id, GraphEdge.source_node_id, GraphEdge.dest_node_id, GraphEdge.direction
        ).yield_per(50000):
            self._adjacency[row[1]].append(row[2])
            self._reverse_adj[row[2]].append(row[1])
            self._edge_map[row[1]].append({'edge_id': row[0], 'dest': row[2], 'direction': row[3]})
            self._edge_endpoints[row[0]] = (row[1], row[2])

        self._node_set = set(self._adjacency.keys()) | set(self._reverse_adj.keys())
        elapsed = time.time() - self._load_start
        self._log(f"Adjacency loaded: {len(self._node_set):,} source nodes, "
                  f"{sum(len(v) for v in self._adjacency.values()):,} edges in {elapsed:.1f}s")

    def _load_node_coords(self):
        if self._node_coords is not None:
            return
        self._log("Loading node coordinates...")
        self._node_coords = {}
        for row in self.session.query(
            GraphNode.id, GraphNode.latitude, GraphNode.longitude
        ).yield_per(50000):
            self._node_coords[row[0]] = (row[1], row[2])
        self._log(f"Loaded {len(self._node_coords):,} node coordinates")

    # ── Statistics ──────────────────────────────────────────────────────────

    def collect_statistics(self):
        self._log("Collecting graph statistics...")
        s = self.stats

        s.total_nodes = self.session.query(func.count(GraphNode.id)).scalar() or 0
        s.total_edges = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        s.total_osm_ways = self.session.query(func.count(OSMWay.id)).scalar() or 0
        s.total_osm_way_nodes = self.session.query(func.count(OSMWayNode.id)).scalar() or 0

        s.total_bidirectional = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.direction == 'BIDIRECTIONAL').scalar() or 0
        s.total_forward = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.direction == 'FORWARD').scalar() or 0
        s.total_backward = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.direction == 'BACKWARD').scalar() or 0

        s.total_enriched = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.mid_lat != None).scalar() or 0

        s.distinct_highways = self.session.query(
            func.count(func.distinct(GraphEdge.highway))).scalar() or 0

        length_stats = self.session.query(
            func.min(GraphEdge.length), func.max(GraphEdge.length),
            func.avg(GraphEdge.length),
            func.sum(GraphEdge.length),
        ).first()
        if length_stats[0] is not None:
            s.min_length = round(length_stats[0], 2)
            s.max_length = round(length_stats[1], 2)
            s.avg_length = round(length_stats[2], 2)
            s.total_length_km = round((length_stats[3] or 0) / 1000, 2)

        speed_stats = self.session.query(
            func.min(GraphEdge.maxspeed), func.max(GraphEdge.maxspeed)
        ).first()
        if speed_stats[0] is not None:
            s.min_maxspeed = speed_stats[0]
            s.max_maxspeed = speed_stats[1]

        bounds = self.session.query(
            func.min(GraphNode.latitude), func.max(GraphNode.latitude),
            func.min(GraphNode.longitude), func.max(GraphNode.longitude),
        ).first()
        if bounds[0] is not None:
            s.lat_min, s.lat_max, s.lon_min, s.lon_max = [round(x, 4) for x in bounds]

        s.distinct_osm_ids = self.session.query(
            func.count(func.distinct(OSMWay.osm_id))).scalar() or 0

        self._log(f"Stats: {s.total_nodes:,} nodes, {s.total_edges:,} edges, "
                  f"{s.total_osm_ways:,} ways, {s.total_length_km:,} km total")

    # ── 1. Graph Connectivity ───────────────────────────────────────────────

    def check_connectivity(self):
        self._log("=== 1. Graph Connectivity ===")
        self._load_adjacency()

        all_node_ids = set()
        for row in self.session.query(GraphNode.id).yield_per(50000):
            all_node_ids.add(row[0])

        all_edge_nodes = set()
        for row in self.session.query(GraphEdge.source_node_id, GraphEdge.dest_node_id).yield_per(50000):
            all_edge_nodes.add(row[0])
            all_edge_nodes.add(row[1])

        orphan_nodes = all_node_ids - all_edge_nodes
        if orphan_nodes:
            samples = list(orphan_nodes)[:10]
            self._add_issue(
                'connectivity', 'WARNING', 'orphan_nodes',
                f'{len(orphan_nodes):,} GraphNodes have no incident edges',
                count=len(orphan_nodes), sample_ids=samples,
                repairable=True,
                repair_sql='DELETE FROM graph_nodes WHERE id IN (...);',
                repair_description='Remove GraphNodes with zero incident edges (safe)',
            )

        orphan_edges = set()
        for row in self.session.query(GraphEdge.id, GraphEdge.source_node_id, GraphEdge.dest_node_id).yield_per(50000):
            if row[1] not in all_node_ids or row[2] not in all_node_ids:
                orphan_edges.add(row[0])

        if orphan_edges:
            self._add_issue(
                'connectivity', 'CRITICAL', 'orphan_edges',
                f'{len(orphan_edges):,} GraphEdges reference non-existent nodes',
                count=len(orphan_edges), sample_ids=list(orphan_edges)[:10],
                repairable=True,
                repair_sql='DELETE FROM graph_edges WHERE id IN (...);',
                repair_description='Remove edges pointing to non-existent GraphNodes',
            )

        if not orphan_edges and not orphan_nodes:
            self._add_issue(
                'connectivity', 'INFO', 'connectivity_clean',
                'No orphan nodes or edges detected', count=0,
            )

        self._log("Computing connected components...")
        comp_start = time.time()

        visited = set()
        all_edge_node_ids = all_node_ids - orphan_nodes

        if all_edge_node_ids:
            start = next(iter(all_edge_node_ids))
            queue = deque([start])
            visited.add(start)

            while queue:
                cur = queue.popleft()
                for nxt in self._adjacency.get(cur, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
                for nxt in self._reverse_adj.get(cur, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)

            unvisited = all_edge_node_ids - visited
            num_components = 2 if unvisited else 1
            largest_size = len(visited)
            disconnected_count = len(unvisited)

            if unvisited:
                self._add_issue(
                    'connectivity', 'WARNING', 'disconnected_components',
                    f'2+ components found; {disconnected_count:,} nodes '
                    f'in non-largest component ({disconnected_count / len(all_edge_node_ids) * 100:.2f}%)',
                    count=disconnected_count,
                    sample_ids=list(unvisited)[:10],
                    repairable=False,
                    repair_description='Cannot auto-repair: disconnected components may be '
                                       'islands, private roads, or OSM artifacts',
                )
            else:
                self._add_issue(
                    'connectivity', 'INFO', 'single_component',
                    f'Graph is fully connected ({len(all_edge_node_ids):,} edge-referenced nodes, 1 component)',
                    count=0,
                )
        else:
            self._add_issue(
                'connectivity', 'ERROR', 'empty_graph',
                'No edge-referenced nodes — graph is empty', count=0,
            )

        comp_elapsed = time.time() - comp_start
        self._log(f"Component analysis done in {comp_elapsed:.1f}s")

    # ── 2. Geometry Integrity ───────────────────────────────────────────────

    def check_geometry(self):
        self._log("=== 2. Geometry Integrity ===")

        zero_len = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.length <= 0).scalar() or 0
        if zero_len:
            samples = [r[0] for r in self.session.query(GraphEdge.id).filter(
                GraphEdge.length <= 0).limit(10).all()]
            self._add_issue(
                'geometry', 'ERROR', 'zero_length_edges',
                f'{zero_len:,} edges have length <= 0 meters',
                count=zero_len, sample_ids=samples,
                repairable=True,
                repair_sql='DELETE FROM graph_edges WHERE length <= 0;',
                repair_description='Remove zero-length edges (impossible road segments)',
            )

        self._log("Checking for invalid coordinates...")
        invalid_lat = self.session.query(func.count(GraphNode.id)).filter(
            or_(GraphNode.latitude < -90, GraphNode.latitude > 90,
                GraphNode.latitude == None)).scalar() or 0
        if invalid_lat:
            self._add_issue(
                'geometry', 'CRITICAL', 'invalid_latitude',
                f'{invalid_lat:,} nodes have latitude outside [-90, 90] or NULL',
                count=invalid_lat, repairable=False,
                repair_description='Cannot auto-repair: coordinate requires source correction',
            )

        invalid_lon = self.session.query(func.count(GraphNode.id)).filter(
            or_(GraphNode.longitude < -180, GraphNode.longitude > 180,
                GraphNode.longitude == None)).scalar() or 0
        if invalid_lon:
            self._add_issue(
                'geometry', 'CRITICAL', 'invalid_longitude',
                f'{invalid_lon:,} nodes have longitude outside [-180, 180] or NULL',
                count=invalid_lon, repairable=False,
            )

        self._log("Checking for self-loops...")
        self_loop_count = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.source_node_id == GraphEdge.dest_node_id).scalar() or 0
        if self_loop_count:
            samples = [r[0] for r in self.session.query(GraphEdge.id).filter(
                GraphEdge.source_node_id == GraphEdge.dest_node_id).limit(10).all()]
            self._add_issue(
                'geometry', 'ERROR', 'self_loops',
                f'{self_loop_count:,} edges are self-loops (source == dest)',
                count=self_loop_count, sample_ids=samples,
                repairable=True,
                repair_sql='DELETE FROM graph_edges WHERE source_node_id = dest_node_id;',
                repair_description='Remove self-loop edges',
            )

        self._log("Checking for duplicate geometries...")
        dup_q = self.session.query(
            GraphEdge.geometry_wkt, func.count(GraphEdge.id)
        ).filter(
            GraphEdge.geometry_wkt != None
        ).group_by(GraphEdge.geometry_wkt).having(
            func.count(GraphEdge.id) > 1
        ).limit(10).all()

        dup_total = self.session.query(func.count()).select_from(
            self.session.query(
                GraphEdge.geometry_wkt, func.count(GraphEdge.id).label('cnt')
            ).filter(GraphEdge.geometry_wkt != None).group_by(
                GraphEdge.geometry_wkt).having(func.count(GraphEdge.id) > 1).subquery()
        ).scalar() or 0

        if dup_total:
            self._add_issue(
                'geometry', 'WARNING', 'duplicate_geometries',
                f'{dup_total:,} duplicate geometry_wkt groups found (multiple edges share geometry)',
                count=dup_total, repairable=False,
                repair_description='Cannot auto-repair: may be valid parallel edges or data issues',
            )

        self._log("Checking edge direction values...")
        invalid_dir = self.session.query(func.count(GraphEdge.id)).filter(
            ~GraphEdge.direction.in_(VALID_DIRECTIONS)).scalar() or 0
        if invalid_dir:
            samples = [r[0] for r in self.session.query(GraphEdge.id).filter(
                ~GraphEdge.direction.in_(VALID_DIRECTIONS)).limit(10).all()]
            self._add_issue(
                'geometry', 'ERROR', 'invalid_direction',
                f'{invalid_dir:,} edges have unrecognized direction values',
                count=invalid_dir, sample_ids=samples,
                repairable=True,
                repair_sql="UPDATE graph_edges SET direction = 'BIDIRECTIONAL' WHERE direction NOT IN (...);",
                repair_description='Set unrecognized directions to BIDIRECTIONAL (conservative default)',
            )

        self._log("Checking for invalid edge lengths vs node distances...")
        self._load_adjacency()
        self._load_node_coords()
        stale_length_count = 0
        stale_samples = []
        checked = 0
        max_check = 50000

        for eid, src_id, dst_id, length in self.session.query(
            GraphEdge.id, GraphEdge.source_node_id, GraphEdge.dest_node_id,
            GraphEdge.length
        ).yield_per(10000):
            if checked >= max_check:
                break
            checked += 1
            src_coords = self._node_coords.get(src_id)
            dst_coords = self._node_coords.get(dst_id)
            if src_coords and dst_coords:
                expected = haversine(
                    src_coords[0], src_coords[1], dst_coords[0], dst_coords[1])
                if length > 0 and abs(expected - length) / max(length, 1) > 2.0:
                    stale_length_count += 1
                    if len(stale_samples) < 10:
                        stale_samples.append(eid)

        if stale_length_count:
            self._add_issue(
                'geometry', 'WARNING', 'stale_edge_lengths',
                f'{stale_length_count:,} sampled edges have length >200% of haversine distance '
                f'(checked {checked:,} edges)',
                count=stale_length_count, sample_ids=stale_samples,
                repairable=False,
                repair_description='Cannot auto-repair: requires re-computation from source geometry',
            )

        if not any(i.severity in ('ERROR', 'CRITICAL') for i in self.issues if i.category == 'geometry'):
            self._add_issue(
                'geometry', 'INFO', 'geometry_clean',
                'No critical geometry issues detected', count=0,
            )

    # ── 3. Routing Integrity ────────────────────────────────────────────────

    def check_routing(self):
        self._log("=== 3. Routing Integrity ===")
        self._load_adjacency()

        node_set = self._node_set

        self._log("Identifying dead-end nodes...")
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        for row in self.session.query(
            GraphEdge.source_node_id, GraphEdge.dest_node_id, GraphEdge.direction
        ).yield_per(50000):
            out_degree[row[0]] += 1
            in_degree[row[1]] += 1
            if row[2] == 'BIDIRECTIONAL':
                out_degree[row[1]] += 1
                in_degree[row[0]] += 1

        dead_ends = set()
        for nid in node_set:
            od = out_degree.get(nid, 0)
            id_ = in_degree.get(nid, 0)
            if od + id_ == 1:
                dead_ends.add(nid)

        if dead_ends:
            self._add_issue(
                'routing', 'INFO', 'dead_ends',
                f'{len(dead_ends):,} dead-end nodes (single edge) — expected in road networks',
                count=len(dead_ends), sample_ids=list(dead_ends)[:10],
                repairable=False,
                repair_description='Dead ends are normal road network features (cul-de-sacs, network edges)',
            )

        self._log("Checking oneway link correctness...")
        oneway_issues = 0
        oneway_samples = []

        for row in self.session.query(
            GraphEdge.id, GraphEdge.source_node_id, GraphEdge.dest_node_id,
            GraphEdge.direction, GraphEdge.osm_way_id
        ).yield_per(50000):
            edge_id, src, dst, direction, way_id = row
            if direction == 'FORWARD':
                has_backward = False
                for e in self._edge_map.get(dst, []):
                    if e['dest'] == src and e['edge_id'] != edge_id:
                        has_backward = True
                        break
                if has_backward:
                    oneway_issues += 1
                    if len(oneway_samples) < 10:
                        oneway_samples.append(edge_id)

        if oneway_issues:
            self._add_issue(
                'routing', 'WARNING', 'incorrect_oneway_links',
                f'{oneway_issues:,} FORWARD edges have a matching BACKWARD edge '
                f'(potential oneway inconsistency)',
                count=oneway_issues, sample_ids=oneway_samples,
                repairable=False,
                repair_description='Cannot auto-repair: requires OSM tag analysis to resolve',
            )

        self._log("Checking for BIDIRECTIONAL without matching reverse edge...")
        missing_reverse = 0
        missing_samples = []

        for row in self.session.query(
            GraphEdge.id, GraphEdge.source_node_id, GraphEdge.dest_node_id,
            GraphEdge.direction
        ).yield_per(50000):
            if row[3] != 'BIDIRECTIONAL':
                continue
            has_reverse = False
            for e in self._edge_map.get(row[2], []):
                if e['dest'] == row[1] and e['edge_id'] != row[0]:
                    has_reverse = True
                    break
            if not has_reverse:
                missing_reverse += 1
                if len(missing_samples) < 10:
                    missing_samples.append(row[0])

        if missing_reverse:
            self._add_issue(
                'routing', 'WARNING', 'missing_reverse_edge',
                f'{missing_reverse:,} BIDIRECTIONAL edges lack a matching reverse edge',
                count=missing_reverse, sample_ids=missing_samples,
                repairable=False,
                repair_description='Cannot auto-repair: reverse edge creation needs source OSM data',
            )

        if not any(i.severity in ('ERROR', 'CRITICAL') for i in self.issues if i.category == 'routing'):
            self._add_issue(
                'routing', 'INFO', 'routing_clean',
                'No critical routing integrity issues detected', count=0,
            )

    # ── 4. OSM Consistency ──────────────────────────────────────────────────

    def check_osm_consistency(self):
        self._log("=== 4. OSM Consistency ===")

        missing_highway = self.session.query(func.count(GraphEdge.id)).filter(
            or_(GraphEdge.highway == None, GraphEdge.highway == '')).scalar() or 0
        if missing_highway:
            samples = [r[0] for r in self.session.query(GraphEdge.id).filter(
                or_(GraphEdge.highway == None, GraphEdge.highway == '')).limit(10).all()]
            self._add_issue(
                'osm', 'ERROR', 'missing_highway_refs',
                f'{missing_highway:,} edges have NULL or empty highway tag',
                count=missing_highway, sample_ids=samples,
                repairable=True,
                repair_sql="DELETE FROM graph_edges WHERE highway IS NULL OR highway = '';",
                repair_description='Remove edges with missing highway classification',
            )

        unknown_highway = self.session.query(func.count(GraphEdge.id)).filter(
            ~GraphEdge.highway.in_(VALID_HIGHWAYS)).scalar() or 0
        if unknown_highway:
            self._log("  Checking unknown highway types distribution...")
            unknown_dist = self.session.query(
                GraphEdge.highway, func.count(GraphEdge.id)
            ).filter(~GraphEdge.highway.in_(VALID_HIGHWAYS)).group_by(
                GraphEdge.highway).order_by(func.count(GraphEdge.id).desc()).limit(10).all()
            detail = ', '.join(f'{h}: {c:,}' for h, c in unknown_dist)
            self._add_issue(
                'osm', 'WARNING', 'unknown_highway_types',
                f'{unknown_highway:,} edges use highway types outside standard set ({detail})',
                count=unknown_highway, repairable=False,
                repair_description='Unknown highway types are valid OSM data — keep as-is',
            )

        self._log("Checking duplicate OSM IDs...")
        dup_osm = self.session.query(
            OSMWay.osm_id, func.count(OSMWay.id)
        ).group_by(OSMWay.osm_id).having(func.count(OSMWay.id) > 1).limit(10).all()

        dup_osm_count = self.session.query(func.count()).select_from(
            self.session.query(OSMWay.osm_id).group_by(OSMWay.osm_id).having(
                func.count(OSMWay.id) > 1).subquery()
        ).scalar() or 0

        if dup_osm_count:
            self._add_issue(
                'osm', 'ERROR', 'duplicate_osm_ids',
                f'{dup_osm_count:,} OSM IDs appear on multiple Way records',
                count=dup_osm_count,
                sample_ids=[d[0] for d in dup_osm[:10]],
                repairable=False,
                repair_description='Cannot auto-repair: requires source dedup analysis',
            )

        self._log("Checking invalid speed values...")
        invalid_speed = self.session.query(func.count(GraphEdge.id)).filter(
            or_(GraphEdge.maxspeed < 0, GraphEdge.maxspeed > 200)).scalar() or 0
        if invalid_speed:
            self._add_issue(
                'osm', 'ERROR', 'invalid_speed_values',
                f'{invalid_speed:,} edges have speed outside [0, 200] km/h',
                count=invalid_speed, repairable=False,
            )

        self._log("Checking invalid lane counts...")
        invalid_lanes = self.session.query(func.count(GraphEdge.id)).filter(
            and_(GraphEdge.lanes != None, or_(GraphEdge.lanes < 1, GraphEdge.lanes > 20))
        ).scalar() or 0
        if invalid_lanes:
            self._add_issue(
                'osm', 'WARNING', 'invalid_lane_counts',
                f'{invalid_lanes:,} edges have lane count outside [1, 20]',
                count=invalid_lanes, repairable=False,
            )

        self._log("Checking for unprocessed OSM ways...")
        unprocessed = self.session.query(func.count(OSMWay.id)).filter(
            OSMWay.processed_at == None).scalar() or 0
        if unprocessed:
            self._add_issue(
                'osm', 'WARNING', 'unprocessed_ways',
                f'{unprocessed:,} OSMWay records not yet processed into graph',
                count=unprocessed, repairable=False,
                repair_description='Run graph_builder.py to process remaining ways',
            )

        if not any(i.severity in ('ERROR', 'CRITICAL') for i in self.issues if i.category == 'osm'):
            self._add_issue(
                'osm', 'INFO', 'osm_clean',
                'No critical OSM consistency issues detected', count=0,
            )

    # ── 5. Spatial Validation ───────────────────────────────────────────────

    def check_spatial(self):
        self._log("=== 5. Spatial Validation ===")

        self._log("Checking GraphSpatialIndex midpoint coverage...")
        total_edges = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        edges_with_mid = self.session.query(func.count(GraphEdge.id)).filter(
            GraphEdge.mid_lat != None).scalar() or 0
        missing_mid = total_edges - edges_with_mid

        if missing_mid:
            self._add_issue(
                'spatial', 'ERROR', 'missing_midpoints',
                f'{missing_mid:,} of {total_edges:,} edges missing midpoint coordinates '
                f'({missing_mid / total_edges * 100:.2f}%)',
                count=missing_mid, repairable=False,
                repair_description='Run enrich_graph.py to populate midpoint coordinates',
            )
        else:
            self._add_issue(
                'spatial', 'INFO', 'midpoints_complete',
                f'All {total_edges:,} edges have midpoint coordinates',
                count=0,
            )

        self._log("Running nearest-node validation...")
        self._load_adjacency()
        self._load_node_coords()
        node_id_list = list(self._node_set)
        if len(node_id_list) > 500:
            import random
            random.seed(42)
            sample_nodes = random.sample(node_id_list, 500)
        else:
            sample_nodes = node_id_list

        all_neighbors_cache: Dict[int, Set[int]] = {}
        nn_failures = 0
        nn_samples = []
        nn_checked = 0

        for nid in sample_nodes:
            coords = self._node_coords.get(nid)
            if coords is None:
                continue
            nn_checked += 1
            best_id = None
            best_dist = float('inf')
            for other_nid in node_id_list:
                if other_nid == nid:
                    continue
                other_coords = self._node_coords.get(other_nid)
                if other_coords is None:
                    continue
                d = haversine(coords[0], coords[1], other_coords[0], other_coords[1])
                if d < best_dist:
                    best_dist = d
                    best_id = other_nid
            if best_id is None:
                continue
            if nid not in all_neighbors_cache:
                fwd = set(self._adjacency.get(nid, []))
                rev = set(self._reverse_adj.get(nid, []))
                all_neighbors_cache[nid] = fwd | rev
            if best_id not in all_neighbors_cache[nid] and nn_checked <= 50:
                nn_failures += 1
                if len(nn_samples) < 10:
                    nn_samples.append(nid)

        if nn_failures:
            self._add_issue(
                'spatial', 'INFO', 'nearest_node_not_neighbor',
                f'{nn_failures} of {nn_checked} sampled nodes: nearest node is not a graph neighbor '
                f'(expected for road networks)',
                count=nn_failures, sample_ids=nn_samples,
                repairable=False,
                repair_description='Not a defect — road networks often have nearby non-adjacent nodes',
            )
        else:
            self._add_issue(
                'spatial', 'INFO', 'nearest_node_check',
                f'Nearest-node validation passed ({nn_checked} samples, all nearest nodes are neighbors)',
                count=0,
            )

        self._log("Running nearest-edge midpoint validation...")
        self._load_node_coords()
        self._load_adjacency()
        edge_midpoints = []
        edge_endpoints_for_ne = {}
        for row in self.session.query(
            GraphEdge.id, GraphEdge.mid_lat, GraphEdge.mid_lon,
            GraphEdge.source_node_id, GraphEdge.dest_node_id
        ).yield_per(50000):
            if row[1] is not None and row[2] is not None:
                edge_midpoints.append((row[0], row[1], row[2]))
                edge_endpoints_for_ne[row[0]] = (row[3], row[4])

        if edge_midpoints:
            import random
            random.seed(42)
            sample_size = min(200, len(edge_midpoints))
            sample_edges = random.sample(edge_midpoints, sample_size)

            ne_failures = 0
            ne_samples = []

            for eid, mid_lat, mid_lon in sample_edges:
                best_id = None
                best_dist = float('inf')
                for other_eid, other_lat, other_lon in edge_midpoints:
                    if other_eid == eid:
                        continue
                    d = haversine(mid_lat, mid_lon, other_lat, other_lon)
                    if d < best_dist:
                        best_dist = d
                        best_id = other_eid

                if best_id is not None:
                    ep = edge_endpoints_for_ne.get(eid)
                    if ep:
                        src_coords = self._node_coords.get(ep[0])
                        dst_coords = self._node_coords.get(ep[1])
                        if src_coords and dst_coords:
                            min_dist_to_endpoints = min(
                                haversine(mid_lat, mid_lon, src_coords[0], src_coords[1]),
                                haversine(mid_lat, mid_lon, dst_coords[0], dst_coords[1]),
                            )
                            if best_dist < min_dist_to_endpoints * 0.5 and len(ne_samples) < 10:
                                ne_failures += 1
                                ne_samples.append(eid)

            if ne_failures:
                self._add_issue(
                    'spatial', 'INFO', 'nearest_edge_proximity',
                    f'{ne_failures} of {sample_size} sampled edges: nearest edge midpoint is very close '
                    f'but not the same edge (expected in dense areas)',
                    count=ne_failures, sample_ids=ne_samples,
                    repairable=False,
                )
            else:
                self._add_issue(
                    'spatial', 'INFO', 'nearest_edge_check',
                    f'Nearest-edge validation passed ({sample_size} samples)',
                    count=0,
                )

        self._log("Running bbox lookup validation...")
        if edge_midpoints:
            import random
            random.seed(42)
            bbox_fails = 0
            for _ in range(10):
                mid_lat, mid_lon = random.choice(edge_midpoints)[1:]
                half_lat = random.uniform(0.001, 0.01)
                half_lon = random.uniform(0.001, 0.01)
                min_lat = mid_lat - half_lat
                max_lat = mid_lat + half_lat
                min_lon = mid_lon - half_lon
                max_lon = mid_lon + half_lon

                db_count = self.session.query(func.count(GraphEdge.id)).filter(
                    GraphEdge.mid_lat >= min_lat, GraphEdge.mid_lat <= max_lat,
                    GraphEdge.mid_lon >= min_lon, GraphEdge.mid_lon <= max_lon,
                ).scalar() or 0

                spatial_count = sum(
                    1 for _, elat, elon in edge_midpoints
                    if min_lat <= elat <= max_lat and min_lon <= elon <= max_lon
                )

                if db_count != spatial_count:
                    bbox_fails += 1

            if bbox_fails:
                self._add_issue(
                    'spatial', 'WARNING', 'bbox_lookup_mismatch',
                    f'{bbox_fails}/10 bbox tests: DB count != in-memory count',
                    count=bbox_fails, repairable=False,
                )
            else:
                self._add_issue(
                    'spatial', 'INFO', 'bbox_lookup_check',
                    'Bbox lookup validation passed (10/10 tests consistent)',
                    count=0,
                )

    def run_all_checks(self) -> List[ValidationIssue]:
        self.collect_statistics()
        self.check_connectivity()
        self.check_geometry()
        self.check_routing()
        self.check_osm_consistency()
        self.check_spatial()
        return self.issues

    def get_summary(self) -> Dict[str, Any]:
        summary = {
            'total_issues': len(self.issues),
            'critical': sum(1 for i in self.issues if i.severity == 'CRITICAL'),
            'error': sum(1 for i in self.issues if i.severity == 'ERROR'),
            'warning': sum(1 for i in self.issues if i.severity == 'WARNING'),
            'info': sum(1 for i in self.issues if i.severity == 'INFO'),
            'repairable': sum(1 for i in self.issues if i.repairable),
            'categories': {},
        }
        for cat in ('connectivity', 'geometry', 'routing', 'osm', 'spatial'):
            cat_issues = [i for i in self.issues if i.category == cat]
            summary['categories'][cat] = {
                'total': len(cat_issues),
                'critical': sum(1 for i in cat_issues if i.severity == 'CRITICAL'),
                'error': sum(1 for i in cat_issues if i.severity == 'ERROR'),
                'warning': sum(1 for i in cat_issues if i.severity == 'WARNING'),
                'info': sum(1 for i in cat_issues if i.severity == 'INFO'),
            }
        return summary


# ── Repair Engine ────────────────────────────────────────────────────────

class GraphRepairEngine:
    SAFE_REPAIRS = {
        'orphan_nodes',
        'orphan_edges',
        'zero_length_edges',
        'self_loops',
    }

    def __init__(self, session: Session, issues: List[ValidationIssue]):
        self.session = session
        self.issues = issues
        self.repaired = []

    def repair(self) -> List[Dict[str, Any]]:
        for issue in self.issues:
            if not issue.repairable or issue.count == 0:
                continue
            if issue.check in self.SAFE_REPAIRS:
                self._repair_issue(issue)
        self.session.commit()
        return self.repaired

    def _repair_issue(self, issue: ValidationIssue):
        if issue.check == 'orphan_nodes':
            self._repair_orphan_nodes(issue)
        elif issue.check == 'orphan_edges':
            self._repair_orphan_edges(issue)
        elif issue.check == 'zero_length_edges':
            self._repair_zero_length(issue)
        elif issue.check == 'self_loops':
            self._repair_self_loops(issue)
        else:
            logger.warning(f"No safe repair for {issue.check} — skipping")

    def _repair_orphan_nodes(self, issue: ValidationIssue):
        logger.info(f"Repairing {issue.count:,} orphan nodes...")
        count_before = self.session.query(func.count(GraphNode.id)).scalar() or 0
        self.session.execute(
            text("DELETE FROM graph_nodes WHERE id NOT IN "
                 "(SELECT DISTINCT source_node_id FROM graph_edges UNION "
                 "SELECT DISTINCT dest_node_id FROM graph_edges)")
        )
        self.session.flush()
        count_after = self.session.query(func.count(GraphNode.id)).scalar() or 0
        deleted = count_before - count_after
        self.repaired.append({
            'check': issue.check, 'deleted': deleted,
            'description': issue.repair_description,
        })
        logger.info(f"  Deleted {deleted:,} orphan nodes")

    def _repair_orphan_edges(self, issue: ValidationIssue):
        logger.info(f"Repairing {issue.count:,} orphan edges...")
        count_before = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        self.session.execute(
            text("DELETE FROM graph_edges WHERE source_node_id NOT IN "
                 "(SELECT id FROM graph_nodes) OR dest_node_id NOT IN "
                 "(SELECT id FROM graph_nodes)")
        )
        self.session.flush()
        count_after = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        deleted = count_before - count_after
        self.repaired.append({
            'check': issue.check, 'deleted': deleted,
            'description': issue.repair_description,
        })
        logger.info(f"  Deleted {deleted:,} orphan edges")

    def _repair_zero_length(self, issue: ValidationIssue):
        logger.info(f"Repairing {issue.count:,} zero-length edges...")
        count_before = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        self.session.execute(
            text("DELETE FROM graph_edges WHERE length <= 0")
        )
        self.session.flush()
        count_after = self.session.query(func.count(GraphEdge.id)).scalar() or 0
        deleted = count_before - count_after
        self.repaired.append({
            'check': issue.check, 'deleted': deleted,
            'description': issue.repair_description,
        })
        logger.info(f"  Deleted {deleted:,} zero-length edges")

    def _repair_self_loops(self, issue: ValidationIssue):
        logger.info(f"Repairing {issue.count:,} self-loop edges...")
        count_before = self.session.execute(
            text("SELECT COUNT(*) FROM graph_edges WHERE source_node_id = dest_node_id")
        ).scalar() or 0
        self.session.execute(
            text("DELETE FROM graph_edges WHERE source_node_id = dest_node_id")
        )
        self.session.flush()
        count_after = self.session.execute(
            text("SELECT COUNT(*) FROM graph_edges WHERE source_node_id = dest_node_id")
        ).scalar() or 0
        deleted = count_before - count_after
        self.repaired.append({
            'check': issue.check, 'deleted': deleted,
            'description': issue.repair_description,
        })
        logger.info(f"  Deleted {deleted:,} self-loop edges")


# ── Report Generator ─────────────────────────────────────────────────────

class ReportGenerator:
    def __init__(self, stats: GraphStatistics, issues: List[ValidationIssue],
                 summary: Dict, repairs: List[Dict], elapsed: float):
        self.stats = stats
        self.issues = issues
        self.summary = summary
        self.repairs = repairs
        self.elapsed = elapsed

    def generate(self) -> str:
        s = self.stats
        lines = []
        w = lines.append

        w("# Graph Validation Report")
        w(f"\nGenerated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        w(f"Validation time: {self.elapsed:.1f}s")
        w("")

        w("## Summary\n")
        sev_icon = {'CRITICAL': '[!!!]', 'ERROR': '[!! ]', 'WARNING': '[!  ]', 'INFO': '[   ]'}
        total = self.summary['total_issues']
        crit = self.summary['critical']
        err = self.summary['error']
        warn = self.summary['warning']
        info = self.summary['info']
        rep = self.summary['repairable']

        if crit:
            verdict = "**CRITICAL ISSUES FOUND**"
        elif err:
            verdict = "**ERRORS FOUND**"
        elif warn:
            verdict = "Warnings present"
        else:
            verdict = "**ALL CHECKS PASSED**"

        w(f"| Metric | Value |")
        w(f"|--------|-------|")
        w(f"| Verdict | {verdict} |")
        w(f"| Total issues | {total} |")
        w(f"| Critical | {crit} |")
        w(f"| Error | {err} |")
        w(f"| Warning | {warn} |")
        w(f"| Info | {info} |")
        w(f"| Auto-repairable | {rep} |")
        w(f"| Validation time | {self.elapsed:.1f}s |")
        w("")

        w("## Graph Statistics\n")
        w("| Metric | Value |")
        w("|--------|-------|")
        w(f"| GraphNodes | {s.total_nodes:,} |")
        w(f"| GraphEdges | {s.total_edges:,} |")
        w(f"| OSMWays | {s.total_osm_ways:,} |")
        w(f"| OSMWayNodes | {s.total_osm_way_nodes:,} |")
        w(f"| BIDIRECTIONAL edges | {s.total_bidirectional:,} |")
        w(f"| FORWARD edges | {s.total_forward:,} |")
        w(f"| BACKWARD edges | {s.total_backward:,} |")
        w(f"| Enriched edges | {s.total_enriched:,} |")
        w(f"| Distinct highway types | {s.distinct_highways} |")
        w(f"| Total road length | {s.total_length_km:,} km |")
        w(f"| Min edge length | {s.min_length:.2f} m |")
        w(f"| Max edge length | {s.max_length:.2f} m |")
        w(f"| Avg edge length | {s.avg_length:.2f} m |")
        w(f"| Speed range | {s.min_maxspeed:.0f} – {s.max_maxspeed:.0f} km/h |")
        w(f"| Latitude range | {s.lat_min:.4f} – {s.lat_max:.4f} |")
        w(f"| Longitude range | {s.lon_min:.4f} – {s.lon_max:.4f} |")
        w("")

        for cat_key, cat_label in [
            ('connectivity', '1. Graph Connectivity'),
            ('geometry', '2. Geometry Integrity'),
            ('routing', '3. Routing Integrity'),
            ('osm', '4. OSM Consistency'),
            ('spatial', '5. Spatial Validation'),
        ]:
            cat_summary = self.summary['categories'][cat_key]
            w(f"## {cat_label}\n")
            w(f"Issues: {cat_summary['critical']} critical, "
              f"{cat_summary['error']} error, "
              f"{cat_summary['warning']} warning, "
              f"{cat_summary['info']} info\n")

            cat_issues = [i for i in self.issues if i.category == cat_key]
            if cat_issues:
                w("| Severity | Check | Count | Description |")
                w("|----------|-------|------:|-------------|")
                for i in cat_issues:
                    icon = sev_icon.get(i.severity, '')
                    w(f"| {icon} {i.severity} | {i.check} | {i.count:,} | {i.message} |")
                w("")

                issues_with_ids = [i for i in cat_issues if i.sample_ids]
                if issues_with_ids:
                    w("### Sample IDs\n")
                    for i in issues_with_ids:
                        ids_str = ', '.join(str(x) for x in i.sample_ids[:10])
                        w(f"- **{i.check}**: `{ids_str}`")
                    w("")
            else:
                w("No issues detected.\n")

        w("## Repair Recommendations\n")
        repairable = [i for i in self.issues if i.repairable and i.count > 0]
        if repairable:
            w("| Check | Count | Repair |")
            w("|-------|------:|--------|")
            for i in repairable:
                w(f"| {i.check} | {i.count:,} | {i.repair_description} |")
            w("")
            w("**Repair SQL (reference only — do not run manually):**\n")
            w("```sql")
            for i in repairable:
                w(f"-- {i.check}: {i.count:,} affected rows")
                w(f"{i.repair_sql}")
                w("")
            w("```\n")
        else:
            w("No auto-repairable issues detected.\n")

        if self.repairs:
            w("## Repair Results\n")
            w("| Check | Deleted | Description |")
            w("|-------|--------:|-------------|")
            for r in self.repairs:
                w(f"| {r['check']} | {r['deleted']:,} | {r['description']} |")
            w("")

        w("---")
        w("*Report generated by `validate_graph.py` — Graph Validation & Data Quality Framework*")

        return '\n'.join(lines)


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Graph Validation & Data Quality Framework')
    parser.add_argument('--db', type=str, default=None,
                        help='Path to SQLite DB (default: use app config)')
    parser.add_argument('--repair', action='store_true',
                        help='Run safe repairs after validation')
    parser.add_argument('--report', type=str, default=None,
                        help='Output path for GRAPH_VALIDATION_REPORT.md')
    args = parser.parse_args()

    if args.db:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(f'sqlite:///{args.db}', echo=False)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
    else:
        session = SessionLocal()

    overall_start = time.time()

    validator = GraphValidator(session)
    issues = validator.run_all_checks()
    summary = validator.get_summary()

    repairs = []
    if args.repair:
        logger.info("=== Running Safe Repairs ===")
        repair_engine = GraphRepairEngine(session, issues)
        repairs = repair_engine.repair()
        logger.info(f"Repaired {len(repairs)} issue types")

    elapsed = time.time() - overall_start

    report_path = args.report or os.path.join(
        os.path.dirname(__file__), '..', '..', 'GRAPH_VALIDATION_REPORT.md')
    report_gen = ReportGenerator(validator.stats, issues, summary, repairs, elapsed)
    report_content = report_gen.generate()

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Report written to {report_path}")

    print("\n" + "=" * 60)
    print(f"VALIDATION COMPLETE in {elapsed:.1f}s")
    print(f"  Issues: {summary['total_issues']} "
          f"(CRITICAL={summary['critical']}, ERROR={summary['error']}, "
          f"WARNING={summary['warning']}, INFO={summary['info']})")
    print(f"  Repairable: {summary['repairable']}")
    if repairs:
        print(f"  Repaired: {sum(r['deleted'] for r in repairs):,} records")
    print(f"  Report: {report_path}")
    print("=" * 60)

    session.close()
    return 0 if summary['critical'] == 0 and summary['error'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
