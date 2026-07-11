# cluster_blackspots.py
"""
AccidentRecord → HighwayBlackSpot clustering.

MoRTH definition: A 500m road stretch qualifies as a black spot if
  ≥5 fatal or grievous accidents, or ≥10 fatalities, occurred in the last 3 years.

This module implements DB-side clustering:
  1. Group AccidentRecord rows by highway + chainage proximity
  2. Sliding window of 500m along each highway
  3. Count fatal + grievous accidents within each window
  4. If threshold met, create/update HighwayBlackSpot record
  5. Link AccidentRecord rows to the black spot via black_spot_id FK

Usage triggered AFTER accident records exist in the DB.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from base_importer import BaseAccidentImporter
from app.db.models import (
    HighwayBlackSpot, AccidentRecord, AccidentSeverity, BlackSpotSeverity,
)


# MoRTH black spot qualification thresholds
FATAL_GRIEVOUS_THRESHOLD = 5
FATALITY_THRESHOLD = 10
WINDOW_METERS = 500
RECENCY_YEARS = 3


class BlackSpotClusterer(BaseAccidentImporter):
    """
    Clusters individual AccidentRecord entries into HighwayBlackSpot records
    following the MoRTH black spot definition.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def qualifies_as_blackspot(records: List[AccidentRecord]) -> Tuple[bool, BlackSpotSeverity]:
        """
        Check if a set of accident records qualifies as a black spot per MoRTH rules.
        Returns (qualifies, severity).
        """
        fatal_grievous = sum(
            1 for r in records
            if r.severity in (AccidentSeverity.FATAL, AccidentSeverity.GRIEVOUS)
        )
        total_fatalities = sum(r.fatalities or 0 for r in records)

        qualifies = (
            fatal_grievous >= FATAL_GRIEVOUS_THRESHOLD
            or total_fatalities >= FATALITY_THRESHOLD
        )

        if not qualifies:
            return (False, BlackSpotSeverity.LOW)

        if total_fatalities >= 10:
            severity = BlackSpotSeverity.HIGH
        elif fatal_grievous >= 10:
            severity = BlackSpotSeverity.HIGH
        elif fatal_grievous >= 5:
            severity = BlackSpotSeverity.MEDIUM
        else:
            severity = BlackSpotSeverity.LOW

        return (True, severity)

    @staticmethod
    def compute_centroid(records: List[AccidentRecord]) -> Tuple[float, float]:
        """Compute geographic centroid of a list of accident records."""
        if not records:
            return (0.0, 0.0)
        lat = sum(r.latitude for r in records) / len(records)
        lon = sum(r.longitude for r in records) / len(records)
        return (lat, lon)

    def cluster_by_highway(self, session, highway: str) -> int:
        """
        Cluster accidents along a single highway.
        Uses sliding window of WINDOW_METERS along chainage.

        Args:
            highway: Highway number (e.g., "NH-44")
            session: DB session

        Returns:
            Number of black spots created/updated.
        """
        # Load all accident records for this highway, ordered by chainage
        records = session.query(AccidentRecord).filter(
            AccidentRecord.road_name == highway
        ).order_by(AccidentRecord.accident_date.desc()).all()

        if not records:
            return 0

        # TODO: implement sliding window clustering
        #   1. Sort records by chainage_km (or lat/lon along highway)
        #   2. Sliding window of 500m
        #   3. For each window position, check qualifies_as_blackspot
        #   4. If qualifies, create HighwayBlackSpot at centroid
        #   5. Update AccidentRecord.black_spot_id FK

        return 0

    def run(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        Run clustering on all accident records in the database.

        Process:
          1. Get distinct highway values from AccidentRecord
          2. For each highway, run cluster_by_highway()
          3. Report created/updated black spots

        Args:
            filepath: Not used (operates on existing DB data).

        Returns:
            Dict with clustering summary.
        """
        session = self.get_session()
        try:
            # Get distinct highways from accident records
            highways = session.query(AccidentRecord.road_name).distinct().all()
            total_spots = 0
            for (hwy,) in highways:
                if not hwy:
                    continue
                spots = self.cluster_by_highway(session, hwy)
                total_spots += spots
            return {"highways_processed": len(highways), "black_spots_created": total_spots}
        finally:
            self.close_session(session)
