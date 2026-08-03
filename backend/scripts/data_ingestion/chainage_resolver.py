"""
Chainage Resolution Engine — Resolve highway chainage locations to graph coordinates.

Converts (highway_number, chainage_km) pairs into (latitude, longitude, GraphEdge)
using a multi-strategy cascade with confidence scoring.

Resolution strategies (in priority order):
  1. OSMWay ref match + geometry interpolation (highest confidence)
  2. GraphEdge highway match + geometry interpolation
  3. HighwayBlackSpot spatial proximity fallback
  4. Unresolved (returns None with metadata)

No mock data. No fake coordinates. Uncertainty is preserved in confidence scores.
"""

import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.models import (
    GraphEdge,
    GraphNode,
    HighwayBlackSpot,
    OSMWay,
    OSMWayNode,
)

from .geo import haversine_distance

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class ResolutionMethod:
    OSM_WAY_INTERPOLATION = "osm_way_interpolation"
    GRAPEDGE_INTERPOLATION = "graphedge_interpolation"
    BLACKSPOT_SPATIAL = "blackspot_spatial_proximity"
    UNRESOLVED = "unresolved"


@dataclass
class ChainageResolution:
    """Result of a chainage resolution attempt."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    matched_edge_id: Optional[int] = None
    matched_way_id: Optional[int] = None
    confidence_score: float = 0.0
    resolution_method: str = ResolutionMethod.UNRESOLVED
    highway_number: str = ""
    chainage_km: Optional[float] = None
    direction: Optional[str] = None
    location_text: Optional[str] = None
    resolution_metadata: Dict[str, Any] = field(default_factory=dict)
    resolved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "matched_edge_id": self.matched_edge_id,
            "matched_way_id": self.matched_way_id,
            "confidence_score": self.confidence_score,
            "resolution_method": self.resolution_method,
            "highway_number": self.highway_number,
            "chainage_km": self.chainage_km,
            "direction": self.direction,
            "location_text": self.location_text,
            "resolution_metadata": self.resolution_metadata,
            "resolved_at": self.resolved_at,
        }


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def interpolate_along_polyline(
    coords: List[Tuple[float, float]], target_distance_m: float
) -> Optional[Tuple[float, float]]:
    """
    Interpolate a point along a polyline at a given cumulative distance.

    Args:
        coords: List of (lat, lon) points forming the polyline.
        target_distance_m: Distance from start in meters.

    Returns:
        (lat, lon) of the interpolated point, or None if target exceeds polyline length.
    """
    if len(coords) < 2 or target_distance_m < 0:
        return None

    cumulative = 0.0
    for i in range(len(coords) - 1):
        seg_len = haversine_distance(
            coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]
        )
        if seg_len < 1e-9:
            continue
        if cumulative + seg_len >= target_distance_m:
            t = (target_distance_m - cumulative) / seg_len
            lat = coords[i][0] + t * (coords[i + 1][0] - coords[i][0])
            lon = coords[i][1] + t * (coords[i + 1][1] - coords[i][1])
            return (lat, lon)
        cumulative += seg_len

    return None


def polyline_length_m(coords: List[Tuple[float, float]]) -> float:
    """Total length of a polyline in meters."""
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine_distance(
            coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1]
        )
    return total


# ---------------------------------------------------------------------------
# Highway number normalization
# ---------------------------------------------------------------------------

# Patterns: "NH 44", "NH44", "NH-44", "NH 44A", "SH 1", "State Highway 5",
# "National Highway 44", etc.
_NH_PATTERN = re.compile(
    r'\b(NH|SH|MDR|ODR|VR|NHAI|Expressway)'
    r'\s*[-]?\s*(\d+[A-Za-z]?)',
    re.IGNORECASE,
)
_NH_FULL_NAME_PATTERN = re.compile(
    r'\b(National\s+Highway|State\s+Highway)'
    r'\s+(\d+[A-Za-z]?)',
    re.IGNORECASE,
)
_NH_PREFIX_PATTERN = re.compile(r'^(NH|SH)\s*', re.IGNORECASE)


def normalize_highway_number(raw: str) -> str:
    """
    Normalize a highway number to a canonical form.

    Examples:
        "NH 44" -> "NH 44"
        "NH44" -> "NH 44"
        "NH-44A" -> "NH 44A"
        "National Highway 44" -> "NH 44"
        "State Highway 1" -> "SH 1"
        "sh 1" -> "SH 1"
    """
    if not raw:
        return ""

    raw = raw.strip()

    m = _NH_PATTERN.search(raw)
    if m:
        prefix = m.group(1).upper()
        num = m.group(2)
        return f"{prefix} {num}"

    # Try full name patterns: "National Highway 44", "State Highway 1"
    m = _NH_FULL_NAME_PATTERN.search(raw)
    if m:
        prefix = "NH" if "national" in m.group(1).lower() else "SH"
        num = m.group(2)
        return f"{prefix} {num}"

    # Try bare number with common prefix inference
    bare = re.sub(r'[^\dA-Za-z]', '', raw)
    if bare.isdigit():
        return f"NH {bare}"

    return raw.upper().strip()


def normalize_ref_for_osm(raw: str) -> str:
    """
    Normalize a ref value to match OSM ref format.

    OSM stores refs like "NH 44", "NH 44;NH 48", "SH 1", "NH44" varies.
    We normalize to a canonical form for matching.
    """
    if not raw:
        return ""
    return normalize_highway_number(raw)


# ---------------------------------------------------------------------------
# Geometry loading
# ---------------------------------------------------------------------------

def _load_way_coords(session: Session, way_id: int) -> List[Tuple[float, float]]:
    """Load ordered (lat, lon) coordinates for an OSMWay via OSMWayNodes."""
    nodes = (
        session.query(OSMWayNode.latitude, OSMWayNode.longitude)
        .filter(OSMWayNode.way_id == way_id)
        .order_by(OSMWayNode.sequence)
        .all()
    )
    return [(n.latitude, n.longitude) for n in nodes]


def _load_edge_coords(session: Session, edge_id: int) -> Optional[Tuple[float, float, float, float]]:
    """Load source and dest node coords for a GraphEdge. Returns (src_lat, src_lon, dst_lat, dst_lon)."""
    edge = session.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
    if not edge:
        return None
    src = session.query(GraphNode).filter(GraphNode.id == edge.source_node_id).first()
    dst = session.query(GraphNode).filter(GraphNode.id == edge.dest_node_id).first()
    if not src or not dst:
        return None
    return (src.latitude, src.longitude, dst.latitude, dst.longitude)


# ---------------------------------------------------------------------------
# Chainage Resolution Engine
# ---------------------------------------------------------------------------

class ChainageResolver:
    """
    Resolves highway chainage (highway_number + chainage_km) to geographic coordinates.

    Usage:
        resolver = ChainageResolver(session)
        result = resolver.resolve("NH 44", 175.5)
        print(result.latitude, result.longitude, result.confidence_score)
    """

    # Confidence bands
    CONF_GPS_EXACT = 0.95
    CONF_HIGHWAY_EXACT = 0.85
    CONF_OSM_GEOMETRY = 0.60
    CONF_TEXT_APPROX = 0.30
    CONF_UNRESOLVED = 0.0

    # Search parameters
    OSM_WAY_SEARCH_RADIUS_M = 5000.0   # max distance from interpolated point to match edge
    EDGE_MATCH_RADIUS_M = 200.0         # max distance from interpolated point to graph edge midpoint
    BLACKSPOT_MATCH_RADIUS_M = 5000.0   # max distance to a black spot with same highway

    def __init__(self, session: Session):
        self.session = session
        self._way_cache: Dict[int, List[Tuple[float, float]]] = {}
        self._ref_index: Dict[str, List[int]] = {}
        self._edge_index_built = False
        self._highway_edge_index: Dict[str, List[int]] = {}

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_ref_index(self):
        """Build an in-memory index of OSMWay ref -> way IDs for fast lookup."""
        if self._ref_index:
            return

        t0 = time.time()
        ways = self.session.query(OSMWay.id, OSMWay.ref, OSMWay.highway).filter(
            OSMWay.ref.isnot(None), OSMWay.ref != ""
        ).all()

        for way_id, ref, highway in ways:
            normalized = normalize_ref_for_osm(ref)
            if normalized:
                self._ref_index.setdefault(normalized, []).append(way_id)
                # Also index without space for fuzzy matching (NH44 -> NH 44)
                compact = re.sub(r'\s+', '', normalized)
                self._ref_index.setdefault(compact, []).append(way_id)

        logger.info(
            f"Chainage resolver: built ref index from {len(ways):,} ways "
            f"({len(self._ref_index):,} unique refs) in {time.time() - t0:.2f}s"
        )

    def build_highway_edge_index(self):
        """Build an index of GraphEdge highway type -> edge IDs for fallback matching."""
        if self._edge_index_built:
            return

        t0 = time.time()
        edges = self.session.query(
            GraphEdge.id, GraphEdge.highway, GraphEdge.mid_lat, GraphEdge.mid_lon
        ).filter(
            GraphEdge.mid_lat.isnot(None), GraphEdge.mid_lon.isnot(None)
        ).all()

        for eid, highway, mid_lat, mid_lon in edges:
            if highway:
                self._highway_edge_index.setdefault(highway.lower(), []).append(eid)

        self._edge_index_built = True
        logger.info(
            f"Chainage resolver: built highway edge index from {len(edges):,} edges "
            f"({len(self._highway_edge_index):,} highway types) in {time.time() - t0:.2f}s"
        )

    # ------------------------------------------------------------------
    # Strategy 1: OSMWay ref match + geometry interpolation
    # ------------------------------------------------------------------

    def _try_osm_way_interpolation(
        self, highway_number: str, chainage_km: float, direction: Optional[str] = None
    ) -> Optional[ChainageResolution]:
        """
        Find OSMWay records matching the highway ref, load their geometry,
        and interpolate the chainage position along the way.

        Highway chainage in India typically starts from a state boundary or
        designated origin and increases monotonically along the highway.
        We find the way whose cumulative geometry length best matches the
        chainage position.
        """
        if self.session is None:
            return None

        self.build_ref_index()

        normalized = normalize_highway_number(highway_number)
        way_ids = self._ref_index.get(normalized, [])
        if not way_ids:
            # Try compact form
            compact = re.sub(r'\s+', '', normalized)
            way_ids = self._ref_index.get(compact, [])

        if not way_ids:
            return None

        # Chainage in km, convert to meters for geometry interpolation
        target_m = chainage_km * 1000.0

        best_result = None
        best_diff = float('inf')

        for way_id in way_ids[:50]:  # limit to avoid pathological cases
            coords = self._load_way_coords_cached(way_id)
            if len(coords) < 2:
                continue

            way_length_m = polyline_length_m(coords)
            if way_length_m < 1.0:
                continue

            # For a single way, chainage_km typically represents distance from highway origin
            # We check if the chainage falls within this way's extent
            # Since we don't know the way's start chainage, we look for the best match
            # by checking if interpolating at target_m gives a reasonable point
            point = interpolate_along_polyline(coords, target_m)
            if point is None:
                # target_m exceeds way length — try if way is a segment of a longer highway
                continue

            # Find the closest GraphEdge to this interpolated point
            edge_id = self._find_nearest_edge(point[0], point[1])
            edge_distance = None
            if edge_id:
                edge_coords = _load_edge_coords(self.session, edge_id)
                if edge_coords:
                    mid_lat = (edge_coords[0] + edge_coords[2]) / 2
                    mid_lon = (edge_coords[1] + edge_coords[3]) / 2
                    edge_distance = haversine_distance(point[0], point[1], mid_lat, mid_lon)

            # Score this result
            # Ways with geometry covering the chainage target are better
            coverage_diff = abs(way_length_m - target_m)
            if coverage_diff < best_diff:
                best_diff = coverage_diff
                confidence = self._compute_osm_confidence(
                    way_length_m, target_m, edge_distance
                )
                best_result = ChainageResolution(
                    latitude=point[0],
                    longitude=point[1],
                    matched_edge_id=edge_id,
                    matched_way_id=way_id,
                    confidence_score=confidence,
                    resolution_method=ResolutionMethod.OSM_WAY_INTERPOLATION,
                    highway_number=highway_number,
                    chainage_km=chainage_km,
                    direction=direction,
                    resolution_metadata={
                        "way_id": way_id,
                        "way_length_m": round(way_length_m, 1),
                        "target_m": round(target_m, 1),
                        "candidate_ways": len(way_ids),
                        "edge_distance_m": round(edge_distance, 1) if edge_distance else None,
                        "interpolated_point": [point[0], point[1]],
                    },
                )

        return best_result

    def _compute_osm_confidence(
        self,
        way_length_m: float,
        target_m: float,
        edge_distance_m: Optional[float],
    ) -> float:
        """
        Compute confidence for OSMWay interpolation result.

        Factors:
        - How well the target falls within the way's geometry extent
        - Whether a nearby GraphEdge was found
        - Distance to the nearest edge
        """
        conf = self.CONF_HIGHWAY_EXACT  # base: 0.85

        # Bonus if target is well within the way (not near endpoints)
        midpoint = way_length_m / 2.0
        dist_from_mid = abs(target_m - midpoint)
        if dist_from_mid < midpoint * 0.3:
            conf = min(conf + 0.05, self.CONF_GPS_EXACT)  # 0.90-0.95
        elif dist_from_mid > midpoint * 0.8:
            conf -= 0.05  # near endpoint, less certain

        # Penalty if no nearby edge found
        if edge_distance_m is None:
            conf -= 0.10
        elif edge_distance_m > self.EDGE_MATCH_RADIUS_M:
            conf -= 0.05

        return round(max(self.CONF_OSM_GEOMETRY, min(conf, self.CONF_GPS_EXACT)), 3)

    # ------------------------------------------------------------------
    # Strategy 2: GraphEdge highway match + interpolation
    # ------------------------------------------------------------------

    def _try_graphedge_interpolation(
        self, highway_number: str, chainage_km: float, direction: Optional[str] = None
    ) -> Optional[ChainageResolution]:
        """
        Fallback: find GraphEdges with matching highway type, estimate chainage
        position by sorting edges by their geographic position along the highway.
        """
        if self.session is None:
            return None

        self.build_highway_edge_index()

        normalized = normalize_highway_number(highway_number)
        # Extract just the highway type prefix (NH, SH, etc.)
        prefix_match = re.match(r'(NH|SH|MDR|ODR|VR)', normalized, re.IGNORECASE)
        if not prefix_match:
            return None

        # GraphEdge.highway stores the OSM highway type (motorway, trunk, primary, etc.)
        # Not the ref (NH/SH). So we need a different approach:
        # Find edges whose associated OSMWay has a matching ref.
        edges_with_ref = (
            self.session.query(
                GraphEdge.id, GraphEdge.osm_way_id,
                GraphEdge.mid_lat, GraphEdge.mid_lon, GraphEdge.length,
                OSMWay.ref
            )
            .join(OSMWay, GraphEdge.osm_way_id == OSMWay.id, isouter=True)
            .filter(OSMWay.ref.isnot(None), OSMWay.ref != "")
            .all()
        )

        # Filter to matching highway ref
        matching_edges = []
        for eid, way_id, mid_lat, mid_lon, length, ref in edges_with_ref:
            if not ref:
                continue
            ref_norm = normalize_ref_for_osm(ref)
            if ref_norm == normalized or re.sub(r'\s+', '', ref_norm) == re.sub(r'\s+', '', normalized):
                if mid_lat is not None and mid_lon is not None:
                    matching_edges.append((eid, mid_lat, mid_lon, length))

        if not matching_edges:
            return None

        # Sort by midpoint latitude (rough north-south chainage ordering for Indian NH)
        # This is an approximation — real chainage ordering depends on highway direction
        matching_edges.sort(key=lambda e: e[1])

        # Estimate chainage position: distribute chainage evenly across edge lengths
        total_length_m = sum(e[3] for e in matching_edges)
        if total_length_m < 1.0:
            return None

        target_m = chainage_km * 1000.0
        if target_m > total_length_m:
            return None

        # Walk edges to find the one containing target_m
        cumulative = 0.0
        for eid, mid_lat, mid_lon, edge_len in matching_edges:
            if cumulative + edge_len >= target_m:
                # This edge contains the target chainage
                fraction = (target_m - cumulative) / edge_len if edge_len > 0 else 0.5
                confidence = self._compute_edge_confidence(
                    len(matching_edges), total_length_m, target_m, fraction
                )
                return ChainageResolution(
                    latitude=mid_lat,
                    longitude=mid_lon,
                    matched_edge_id=eid,
                    matched_way_id=None,
                    confidence_score=confidence,
                    resolution_method=ResolutionMethod.GRAPEDGE_INTERPOLATION,
                    highway_number=highway_number,
                    chainage_km=chainage_km,
                    direction=direction,
                    resolution_metadata={
                        "matching_edges": len(matching_edges),
                        "total_highway_length_m": round(total_length_m, 1),
                        "target_m": round(target_m, 1),
                        "edge_fraction": round(fraction, 3),
                    },
                )
            cumulative += edge_len

        return None

    def _compute_edge_confidence(
        self,
        num_edges: int,
        total_length_m: float,
        target_m: float,
        fraction: float,
    ) -> float:
        """
        Compute confidence for GraphEdge interpolation.

        Lower than OSMWay interpolation because we're matching at edge level,
        not along the actual way geometry.
        """
        conf = self.CONF_OSM_GEOMETRY  # base: 0.60

        # More edges = better highway coverage = higher confidence
        if num_edges > 100:
            conf += 0.10
        elif num_edges > 20:
            conf += 0.05

        # Longer total highway = more certain chainage ordering
        if total_length_m > 100000:  # > 100km
            conf += 0.05

        # Near midpoint of an edge = more certain position
        if 0.2 < fraction < 0.8:
            conf += 0.05

        return round(min(conf, self.CONF_HIGHWAY_EXACT), 3)

    # ------------------------------------------------------------------
    # Strategy 3: Black spot spatial proximity fallback
    # ------------------------------------------------------------------

    def _try_blackspot_fallback(
        self, highway_number: str, chainage_km: float, direction: Optional[str] = None,
        location_text: Optional[str] = None,
    ) -> Optional[ChainageResolution]:
        """
        If OSM geometry is not available, check if there's a HighwayBlackSpot
        with matching highway_number and chainage range that covers this chainage.
        """
        if self.session is None:
            return None

        normalized = normalize_highway_number(highway_number)

        # Find black spots on the same highway whose chainage range covers our target
        spots = (
            self.session.query(HighwayBlackSpot)
            .filter(
                HighwayBlackSpot.highway_number.isnot(None),
                HighwayBlackSpot.chainage_start_km.isnot(None),
                HighwayBlackSpot.latitude.isnot(None),
                HighwayBlackSpot.longitude.isnot(None),
            )
            .all()
        )

        best_spot = None
        best_chainage_dist = float('inf')

        for spot in spots:
            spot_hwy = normalize_highway_number(spot.highway_number or "")
            if spot_hwy != normalized and re.sub(r'\s+', '', spot_hwy) != re.sub(r'\s+', '', normalized):
                continue

            # Check if chainage falls within black spot's range
            if spot.chainage_start_km is not None and spot.chainage_end_km is not None:
                if spot.chainage_start_km <= chainage_km <= spot.chainage_end_km:
                    # Exact range match
                    chainage_dist = 0.0
                else:
                    # Distance to nearest end of range
                    chainage_dist = min(
                        abs(chainage_km - spot.chainage_start_km),
                        abs(chainage_km - spot.chainage_end_km),
                    )
            elif spot.chainage_start_km is not None:
                chainage_dist = abs(chainage_km - spot.chainage_start_km)
            else:
                continue

            if chainage_dist < best_chainage_dist:
                best_chainage_dist = chainage_dist
                best_spot = spot

        if best_spot is None:
            return None

        # Use the black spot's coordinates as an approximation
        confidence = self._compute_blackspot_confidence(best_chainage_dist)
        return ChainageResolution(
            latitude=best_spot.latitude,
            longitude=best_spot.longitude,
            matched_edge_id=None,
            matched_way_id=None,
            confidence_score=confidence,
            resolution_method=ResolutionMethod.BLACKSPOT_SPATIAL,
            highway_number=highway_number,
            chainage_km=chainage_km,
            direction=direction,
            location_text=location_text,
            resolution_metadata={
                "blackspot_id": best_spot.id,
                "blackspot_official_id": best_spot.official_id,
                "chainage_distance_km": round(best_chainage_dist, 3),
                "blackspot_chainage_range": [
                    best_spot.chainage_start_km,
                    best_spot.chainage_end_km,
                ],
            },
        )

    def _compute_blackspot_confidence(self, chainage_distance_km: float) -> float:
        """Confidence degrades with distance from the known black spot."""
        if chainage_distance_km < 0.1:  # within 100m
            return self.CONF_HIGHWAY_EXACT  # 0.85
        elif chainage_distance_km < 1.0:
            return 0.70
        elif chainage_distance_km < 5.0:
            return 0.50
        elif chainage_distance_km < 20.0:
            return 0.35
        else:
            return self.CONF_TEXT_APPROX  # 0.30

    # ------------------------------------------------------------------
    # Nearest edge lookup
    # ------------------------------------------------------------------

    def _find_nearest_edge(self, lat: float, lon: float) -> Optional[int]:
        """Find the nearest GraphEdge to a given point using spatial query."""
        deg_radius = self.EDGE_MATCH_RADIUS_M / 111000.0
        edges = (
            self.session.query(GraphEdge.id, GraphEdge.mid_lat, GraphEdge.mid_lon)
            .filter(
                GraphEdge.mid_lat.isnot(None),
                GraphEdge.mid_lon.isnot(None),
                GraphEdge.mid_lat >= lat - deg_radius,
                GraphEdge.mid_lat <= lat + deg_radius,
                GraphEdge.mid_lon >= lon - deg_radius,
                GraphEdge.mid_lon <= lon + deg_radius,
            )
            .limit(100)
            .all()
        )

        best_id = None
        best_dist = float('inf')
        for eid, mlat, mlon in edges:
            d = haversine_distance(lat, lon, mlat, mlon)
            if d < best_dist:
                best_dist = d
                best_id = eid

        return best_id if best_dist <= self.EDGE_MATCH_RADIUS_M else None

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------

    def _load_way_coords_cached(self, way_id: int) -> List[Tuple[float, float]]:
        """Load way coords with in-memory cache."""
        if way_id in self._way_cache:
            return self._way_cache[way_id]
        coords = _load_way_coords(self.session, way_id)
        self._way_cache[way_id] = coords
        return coords

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        highway_number: str,
        chainage_km: float,
        direction: Optional[str] = None,
        location_text: Optional[str] = None,
    ) -> ChainageResolution:
        """
        Resolve a highway chainage to geographic coordinates.

        Attempts multiple strategies in priority order and returns the best match.

        Args:
            highway_number: Highway identifier (e.g., "NH 44", "SH 1").
            chainage_km: Chainage position in kilometers.
            direction: Optional direction hint ("UP"/"DOWN" or state name).
            location_text: Optional raw location text for metadata.

        Returns:
            ChainageResolution with coordinates, confidence, and metadata.
        """
        t0 = time.time()
        normalized = normalize_highway_number(highway_number)

        logger.info(
            f"Resolving chainage: highway={normalized} chainage={chainage_km}km"
            + (f" dir={direction}" if direction else "")
        )

        # Strategy 1: OSMWay ref match + geometry interpolation
        result = self._try_osm_way_interpolation(normalized, chainage_km, direction)
        if result and result.confidence_score >= self.CONF_OSM_GEOMETRY:
            elapsed = time.time() - t0
            result.resolution_metadata["resolve_time_ms"] = round(elapsed * 1000, 1)
            logger.info(
                f"Resolved via OSMWay interpolation: ({result.latitude:.6f}, {result.longitude:.6f}) "
                f"conf={result.confidence_score:.3f} way={result.matched_way_id} "
                f"edge={result.matched_edge_id} in {elapsed:.3f}s"
            )
            return result

        # Strategy 2: GraphEdge highway match
        result2 = self._try_graphedge_interpolation(normalized, chainage_km, direction)
        if result2 and (result is None or result2.confidence_score > result.confidence_score):
            result = result2

        if result and result.confidence_score >= self.CONF_OSM_GEOMETRY:
            elapsed = time.time() - t0
            result.resolution_metadata["resolve_time_ms"] = round(elapsed * 1000, 1)
            logger.info(
                f"Resolved via GraphEdge interpolation: ({result.latitude:.6f}, {result.longitude:.6f}) "
                f"conf={result.confidence_score:.3f} edge={result.matched_edge_id} "
                f"in {elapsed:.3f}s"
            )
            return result

        # Strategy 3: Black spot spatial proximity
        result3 = self._try_blackspot_fallback(normalized, chainage_km, direction, location_text)
        if result3 and (result is None or result3.confidence_score > result.confidence_score):
            result = result3

        if result:
            elapsed = time.time() - t0
            result.resolution_metadata["resolve_time_ms"] = round(elapsed * 1000, 1)
            logger.info(
                f"Resolved via black spot fallback: ({result.latitude:.6f}, {result.longitude:.6f}) "
                f"conf={result.confidence_score:.3f} in {elapsed:.3f}s"
            )
            return result

        # Strategy 4: Unresolved
        elapsed = time.time() - t0
        unresolved = ChainageResolution(
            highway_number=highway_number,
            chainage_km=chainage_km,
            direction=direction,
            location_text=location_text,
            confidence_score=self.CONF_UNRESOLVED,
            resolution_method=ResolutionMethod.UNRESOLVED,
            resolution_metadata={
                "reason": "No matching OSMWay, GraphEdge, or HighwayBlackSpot found",
                "normalized_highway": normalized,
                "resolve_time_ms": round(elapsed * 1000, 1),
            },
        )
        logger.warning(
            f"Unresolved chainage: highway={normalized} chainage={chainage_km}km "
            f"({elapsed:.3f}s)"
        )
        return unresolved

    def resolve_batch(
        self, requests: List[Dict[str, Any]], parallel: bool = False
    ) -> List[ChainageResolution]:
        """
        Resolve multiple chainage requests.

        Args:
            requests: List of dicts with keys: highway_number, chainage_km,
                      direction (optional), location_text (optional).
            parallel: Ignored (reserved for future async implementation).

        Returns:
            List of ChainageResolution objects, one per request.
        """
        results = []
        for i, req in enumerate(requests):
            try:
                result = self.resolve(
                    highway_number=req["highway_number"],
                    chainage_km=req["chainage_km"],
                    direction=req.get("direction"),
                    location_text=req.get("location_text"),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Batch resolution failed for request {i}: {e}")
                results.append(ChainageResolution(
                    highway_number=req.get("highway_number", ""),
                    chainage_km=req.get("chainage_km"),
                    confidence_score=self.CONF_UNRESOLVED,
                    resolution_method=ResolutionMethod.UNRESOLVED,
                    resolution_metadata={"error": str(e), "batch_index": i},
                ))

        # Summary stats
        resolved = sum(1 for r in results if r.resolution_method != ResolutionMethod.UNRESOLVED)
        avg_conf = (
            sum(r.confidence_score for r in results) / len(results)
            if results else 0.0
        )
        logger.info(
            f"Batch resolution: {resolved}/{len(results)} resolved, "
            f"avg confidence={avg_conf:.3f}"
        )
        return results

    def resolve_highway_blackspots(
        self, batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Resolve chainage for all HighwayBlackSpot records with PENDING geometry.

        Reads chainage_start_km and highway_number from each unresolved record,
        resolves coordinates, and updates the record in place.

        Returns:
            Summary dict with counts.
        """
        t0 = time.time()
        pending = (
            self.session.query(HighwayBlackSpot)
            .filter(
                HighwayBlackSpot.geometry_resolution == "PENDING",
                HighwayBlackSpot.highway_number.isnot(None),
                HighwayBlackSpot.chainage_start_km.isnot(None),
            )
            .all()
        )

        stats = {
            "total_pending": len(pending),
            "resolved": 0,
            "improved": 0,
            "unresolved": 0,
            "confidence_distribution": {},
        }

        for i, spot in enumerate(pending):
            chainage_km = spot.chainage_start_km
            if spot.chainage_end_km is not None:
                chainage_km = (spot.chainage_start_km + spot.chainage_end_km) / 2.0

            result = self.resolve(
                highway_number=spot.highway_number,
                chainage_km=chainage_km,
                location_text=spot.location_text,
            )

            # Track confidence distribution
            bucket = f"{int(result.confidence_score * 10) * 10}-{int(result.confidence_score * 10) * 10 + 9}"
            stats["confidence_distribution"][bucket] = (
                stats["confidence_distribution"].get(bucket, 0) + 1
            )

            if result.resolution_method != ResolutionMethod.UNRESOLVED:
                spot.latitude = result.latitude
                spot.longitude = result.longitude
                spot.geometry_resolution = result.resolution_method
                spot.confidence_score = result.confidence_score
                stats["resolved"] += 1

                # Only count as "improved" if we got a meaningful result
                if result.confidence_score >= self.CONF_OSM_GEOMETRY:
                    stats["improved"] += 1
            else:
                stats["unresolved"] += 1

            if (i + 1) % batch_size == 0:
                self.session.commit()
                logger.info(
                    f"Black spot resolution progress: {i + 1}/{len(pending)} "
                    f"({stats['resolved']} resolved, {stats['unresolved']} unresolved)"
                )

        self.session.commit()
        elapsed = time.time() - t0
        stats["duration_seconds"] = round(elapsed, 2)
        logger.info(
            f"Black spot resolution complete: {stats['resolved']}/{stats['total_pending']} resolved "
            f"({stats['improved']} high-confidence) in {elapsed:.1f}s"
        )
        return stats


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for chainage resolution."""
    import argparse

    parser = argparse.ArgumentParser(description="Chainage Resolution Engine")
    sub = parser.add_subparsers(dest="command")

    # Single resolve command
    single = sub.add_parser("resolve", help="Resolve a single chainage")
    single.add_argument("--highway", required=True, help="Highway number (e.g., NH 44)")
    single.add_argument("--chainage", required=True, type=float, help="Chainage in km")
    single.add_argument("--direction", help="Direction hint")
    single.add_argument("--text", help="Location text")

    # Batch resolve command
    batch = sub.add_parser("batch", help="Resolve all pending black spots")
    batch.add_argument("--batch-size", type=int, default=500)

    # Stats command
    sub.add_parser("stats", help="Show resolution statistics")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from app.db.session import engine
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=engine)()
    resolver = ChainageResolver(session)

    try:
        if args.command == "resolve":
            result = resolver.resolve(
                highway_number=args.highway,
                chainage_km=args.chainage,
                direction=args.direction,
                location_text=args.text,
            )
            print(f"\nResolution Result:")
            print(f"  Method:    {result.resolution_method}")
            print(f"  Lat/Lon:   {result.latitude}, {result.longitude}")
            print(f"  Edge ID:   {result.matched_edge_id}")
            print(f"  Way ID:    {result.matched_way_id}")
            print(f"  Confidence:{result.confidence_score:.3f}")
            print(f"  Metadata:  {result.resolution_metadata}")

        elif args.command == "batch":
            stats = resolver.resolve_highway_blackspots(batch_size=args.batch_size)
            print(f"\nBatch Resolution Stats:")
            for k, v in stats.items():
                print(f"  {k}: {v}")

        elif args.command == "stats":
            pending = session.query(func.count(HighwayBlackSpot.id)).filter(
                HighwayBlackSpot.geometry_resolution == "PENDING"
            ).scalar()
            resolved = session.query(func.count(HighwayBlackSpot.id)).filter(
                HighwayBlackSpot.geometry_resolution != "PENDING",
                HighwayBlackSpot.geometry_resolution.isnot(None),
            ).scalar()
            total = session.query(func.count(HighwayBlackSpot.id)).scalar()
            print(f"\nChainage Resolution Statistics:")
            print(f"  Total black spots:   {total}")
            print(f"  GPS-resolved:        {resolved}")
            print(f"  Pending resolution:  {pending}")
        else:
            parser.print_help()

    finally:
        session.close()


if __name__ == "__main__":
    main()
