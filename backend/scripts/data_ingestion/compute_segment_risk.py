"""
HighwayBlackSpot + AccidentRecord -> RoadSegmentRisk computation.

Pre-computes risk scores for grid-based road segments using:
  - Severity-weighted accident density with temporal decay
  - Black spot proximity penalty with temporal decay
  - Configurable weights and thresholds

Usage:
    from scripts.data_ingestion import RoadSegmentRiskBuilder
    builder = RoadSegmentRiskBuilder()
    result = builder.run()
    print(result["segments_created"])
"""

import sys, os, json, time
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import sessionmaker
from app.db.session import engine as app_engine
from app.db.models import (
    HighwayBlackSpot, AccidentRecord, RoadSegmentRisk,
    BlackSpotSeverity, AccidentSeverity,
)
from .geo import haversine_distance as _haversine_m

# ---------------------------------------------------------------------------
# Configurable constants (override via constructor kwargs)
# ---------------------------------------------------------------------------
DEFAULT_GRID_SPACING_M = 200.0
DEFAULT_ACCIDENT_RADIUS_M = 200.0
DEFAULT_BLACKSPOT_RADIUS_M = 500.0
DEFAULT_RECENCY_HALF_LIFE_Y = 2.0
DEFAULT_BLACKSPOT_RECENCY_HALF_LIFE_Y = 3.0
DEFAULT_ACCIDENT_DENSITY_MAX = 50.0
DEFAULT_BLACKSPOT_MAX_CONTRIBUTION = 3.0
DEFAULT_WEIGHT_DENSITY = 0.6
DEFAULT_WEIGHT_BLACKSPOT = 0.4
DEFAULT_MIN_RECORDS_CONFIDENCE = 5

SEVERITY_WEIGHTS = {
    AccidentSeverity.FATAL: 3.0,
    AccidentSeverity.GRIEVOUS: 1.5,
    AccidentSeverity.SIMPLE: 1.0,
}

BLACKSPOT_SEVERITY_WEIGHTS = {
    BlackSpotSeverity.HIGH: 1.0,
    BlackSpotSeverity.MEDIUM: 0.6,
    BlackSpotSeverity.LOW: 0.3,
}


def _recency_weight(accident_date: Optional[datetime], half_life_y: float) -> float:
    if accident_date is None:
        return 0.3
    years_ago = (datetime.utcnow() - accident_date).days / 365.0
    return 2.0 ** (-years_ago / half_life_y)


def _meters_to_deg_lat(m: float) -> float:
    return m / 111320.0


def _meters_to_deg_lon(m: float, at_lat: float) -> float:
    from math import radians, cos
    return m / (111320.0 * cos(radians(at_lat)))


class RoadSegmentRiskBuilder:
    """
    Builds RoadSegmentRisk from HighwayBlackSpot and AccidentRecord.

    Strategy: grid-based. Divides the data bounding box into cells of
    GRID_SPACING_M, computes combined risk for each cell, and stores
    the result. Existing RoadSegmentRisk rows are replaced on rebuild.
    """

    def __init__(self, **kwargs):
        self.grid_spacing_m = kwargs.get("grid_spacing_m", DEFAULT_GRID_SPACING_M)
        self.accident_radius_m = kwargs.get("accident_radius_m", DEFAULT_ACCIDENT_RADIUS_M)
        self.blackspot_radius_m = kwargs.get("blackspot_radius_m", DEFAULT_BLACKSPOT_RADIUS_M)
        self.recency_half_life_y = kwargs.get("recency_half_life_y", DEFAULT_RECENCY_HALF_LIFE_Y)
        self.blackspot_recency_half_life_y = kwargs.get(
            "blackspot_recency_half_life_y", DEFAULT_BLACKSPOT_RECENCY_HALF_LIFE_Y
        )
        self.accident_density_max = kwargs.get("accident_density_max", DEFAULT_ACCIDENT_DENSITY_MAX)
        self.blackspot_max_contribution = kwargs.get(
            "blackspot_max_contribution", DEFAULT_BLACKSPOT_MAX_CONTRIBUTION
        )
        self.weight_density = kwargs.get("weight_density", DEFAULT_WEIGHT_DENSITY)
        self.weight_blackspot = kwargs.get("weight_blackspot", DEFAULT_WEIGHT_BLACKSPOT)
        self.min_records_confidence = kwargs.get(
            "min_records_confidence", DEFAULT_MIN_RECORDS_CONFIDENCE
        )

        self._Session = sessionmaker(bind=app_engine)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Compute RoadSegmentRisk for all areas with accident/blackspot data.

        Args:
            dry_run: If True, compute but do not persist.

        Returns:
            Dict with keys: segments_created, segments_skipped, duration_seconds
        """
        start = time.time()
        session = self._Session()
        try:
            black_spots = self._load_black_spots(session)
            accidents = self._load_accidents(session)

            if not black_spots and not accidents:
                return {"segments_created": 0, "segments_skipped": 0,
                        "duration_seconds": 0, "reason": "no_data"}

            grid_cells = self._build_grid(black_spots, accidents)
            segments = []
            for center_lat, center_lon, row_idx, col_idx in grid_cells:
                seg = self._compute_segment(center_lat, center_lon, row_idx, col_idx,
                                            black_spots, accidents)
                if seg is not None:
                    segments.append(seg)

            if not dry_run:
                self._persist(session, segments)

            return {
                "segments_created": len(segments),
                "segments_skipped": len(grid_cells) - len(segments),
                "duration_seconds": round(time.time() - start, 3),
            }
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_black_spots(session) -> List[HighwayBlackSpot]:
        return session.query(HighwayBlackSpot).filter(
            HighwayBlackSpot.latitude.isnot(None),
            HighwayBlackSpot.longitude.isnot(None),
        ).all()

    @staticmethod
    def _load_accidents(session) -> List[AccidentRecord]:
        return session.query(AccidentRecord).filter(
            AccidentRecord.latitude.isnot(None),
            AccidentRecord.longitude.isnot(None),
        ).all()

    # ------------------------------------------------------------------
    # Grid generation
    # ------------------------------------------------------------------

    def _build_grid(self, black_spots: List[HighwayBlackSpot],
                    accidents: List[AccidentRecord]) -> List[Tuple[float, float, int, int]]:
        """
        Map data points to grid cells. Only occupied cells are returned.
        Each cell is identified by (row_idx, col_idx) at grid_spacing_m resolution.
        Returns list of (center_lat, center_lon, row_idx, col_idx).
        """
        if not black_spots and not accidents:
            return []

        all_lats = [b.latitude for b in black_spots] + [a.latitude for a in accidents]
        all_lons = [b.longitude for b in black_spots] + [a.longitude for a in accidents]

        mid_lat = (min(all_lats) + max(all_lats)) / 2
        cell_lat = _meters_to_deg_lat(self.grid_spacing_m)
        cell_lon = _meters_to_deg_lon(self.grid_spacing_m, mid_lat)

        origin_lat = min(all_lats)
        origin_lon = min(all_lons)

        occupied = set()
        for lat, lon in zip(all_lats, all_lons):
            r = int((lat - origin_lat) / cell_lat)
            c = int((lon - origin_lon) / cell_lon)
            occupied.add((r, c))

        cells = []
        for r, c in occupied:
            center_lat = origin_lat + (r + 0.5) * cell_lat
            center_lon = origin_lon + (c + 0.5) * cell_lon
            cells.append((center_lat, center_lon, r, c))
        return cells

    # ------------------------------------------------------------------
    # Segment computation
    # ------------------------------------------------------------------

    def _compute_segment(self, center_lat: float, center_lon: float,
                         _row_idx: int, _col_idx: int,
                         black_spots: List[HighwayBlackSpot],
                         accidents: List[AccidentRecord]) -> Optional[Dict[str, Any]]:
        """
        Compute risk for one grid cell. Returns None if no data nearby.
        """
        nearby_accidents = []
        for a in accidents:
            d = _haversine_m(center_lat, center_lon, a.latitude, a.longitude)
            if d <= self.accident_radius_m:
                nearby_accidents.append((d, a))

        nearby_blackspots = []
        for b in black_spots:
            d = _haversine_m(center_lat, center_lon, b.latitude, b.longitude)
            if d <= self.blackspot_radius_m:
                nearby_blackspots.append((d, b))

        if not nearby_accidents and not nearby_blackspots:
            return None

        # -- Accident density --
        density_weighted_sum = 0.0
        fatal_count = 0
        grievous_count = 0
        simple_count = 0
        last_date = None
        for d, a in nearby_accidents:
            sw = SEVERITY_WEIGHTS.get(a.severity, 1.0)
            rw = _recency_weight(a.accident_date, self.recency_half_life_y)
            density_weighted_sum += sw * rw
            if a.severity == AccidentSeverity.FATAL:
                fatal_count += 1
            elif a.severity == AccidentSeverity.GRIEVOUS:
                grievous_count += 1
            else:
                simple_count += 1
            if a.accident_date and (last_date is None or a.accident_date > last_date):
                last_date = a.accident_date

        segment_length_km = self.grid_spacing_m / 1000.0
        years_of_data = self._compute_years_of_data(accidents)
        raw_accident_frequency = len(nearby_accidents) / (segment_length_km * years_of_data) if years_of_data > 0 else 0
        accident_density = density_weighted_sum / (segment_length_km * years_of_data) if years_of_data > 0 else 0
        norm_density = min(accident_density / self.accident_density_max, 1.0)

        # -- Black spot penalty --
        blackspot_penalty = 0.0
        for d, b in nearby_blackspots:
            sw = BLACKSPOT_SEVERITY_WEIGHTS.get(b.severity, 0.3)
            proximity = max(0.0, 1.0 - d / (b.radius or 250.0))
            rw = _recency_weight(b.last_accident_date, self.blackspot_recency_half_life_y)
            blackspot_penalty += proximity * sw * rw
        norm_blackspot = min(blackspot_penalty / self.blackspot_max_contribution, 1.0)

        # -- Combined risk --
        risk_score = self.weight_density * norm_density + self.weight_blackspot * norm_blackspot

        # -- Confidence --
        record_count = len(nearby_accidents)
        confidence = min(record_count / self.min_records_confidence, 1.0)

        # -- Segment endpoints: approximate corners of the grid cell --
        half_cell_lat = _meters_to_deg_lat(self.grid_spacing_m) / 2
        half_cell_lon = _meters_to_deg_lon(self.grid_spacing_m, center_lat) / 2

        return {
            "start_latitude": round(center_lat - half_cell_lat, 6),
            "start_longitude": round(center_lon - half_cell_lon, 6),
            "end_latitude": round(center_lat + half_cell_lat, 6),
            "end_longitude": round(center_lon + half_cell_lon, 6),
            "segment_length_m": self.grid_spacing_m,
            "segment_length_km": round(segment_length_km, 4),
            "risk_score": round(risk_score, 6),
            "accident_frequency": round(raw_accident_frequency, 6),
            "accident_density": round(accident_density, 6),
            "fatality_weight": round(norm_density, 6),
            "blackspot_weight": round(norm_blackspot, 6),
            "severity_distribution": json.dumps({
                "fatal": fatal_count,
                "grievous": grievous_count,
                "simple": simple_count,
            }),
            "record_count": record_count,
            "last_accident_date": last_date,
            "confidence_score": round(confidence, 4),
            "last_updated": datetime.utcnow(),
        }

    @staticmethod
    def _compute_years_of_data(accidents: List[AccidentRecord]) -> float:
        dates = [a.accident_date for a in accidents if a.accident_date]
        if len(dates) < 2:
            return 1.0
        span = (max(dates) - min(dates)).days / 365.0
        return max(span, 1.0)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _persist(session, segments: List[Dict[str, Any]]):
        session.query(RoadSegmentRisk).delete()

        batch = []
        for s in segments:
            row = RoadSegmentRisk(
                start_latitude=s["start_latitude"],
                start_longitude=s["start_longitude"],
                end_latitude=s["end_latitude"],
                end_longitude=s["end_longitude"],
                segment_length_m=s["segment_length_m"],
                risk_score=s["risk_score"],
                accident_frequency=s["accident_frequency"],
                severity_distribution=s["severity_distribution"],
                record_count=s["record_count"],
                last_accident_date=s["last_accident_date"],
                confidence_score=s["confidence_score"],
                last_updated=s["last_updated"],
                segment_length_km=s.get("segment_length_km"),
                accident_density=s.get("accident_density"),
                fatality_weight=s.get("fatality_weight"),
                blackspot_weight=s.get("blackspot_weight"),
            )
            batch.append(row)

        session.bulk_save_objects(batch)
        session.commit()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rebuild RoadSegmentRisk from accident data")
    parser.add_argument("--dry-run", action="store_true", help="Compute without persisting")
    parser.add_argument("--grid-spacing-m", type=float, default=DEFAULT_GRID_SPACING_M)
    parser.add_argument("--accident-radius-m", type=float, default=DEFAULT_ACCIDENT_RADIUS_M)
    parser.add_argument("--blackspot-radius-m", type=float, default=DEFAULT_BLACKSPOT_RADIUS_M)
    args = parser.parse_args()

    builder = RoadSegmentRiskBuilder(
        grid_spacing_m=args.grid_spacing_m,
        accident_radius_m=args.accident_radius_m,
        blackspot_radius_m=args.blackspot_radius_m,
    )
    result = builder.run(dry_run=args.dry_run)
    status = "DRY RUN" if args.dry_run else "PERSISTED"
    print(f"[{status}] segments_created={result['segments_created']} "
          f"skipped={result['segments_skipped']} "
          f"duration={result.get('duration_seconds', 'N/A')}s")
    if "reason" in result:
        print(f"  reason: {result['reason']}")
