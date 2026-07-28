# nhai_blackspots_importer.py
"""
NHAI-specific Black Spot CSV → HighwayBlackSpot table.

Data source: NHAI black spot database (via blackspot.morth.gov.in).
Fields similar to MoRTH format but NHAI-specific agency codes.

Differences from MoRTH data:
  - Managed by "NHAI" exclusively
  - Different black_spot_id format
  - May include repair cost/expense fields
  - May include highway number explicitly

For the common MoRTH format, use morth_blackspots_importer.py.
This importer handles NHAI-specific nuances.
"""

import csv
import re
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.db.models import HighwayBlackSpot, BlackSpotSeverity
from .base_importer import BaseImporter
from .validators import (
    ValidatorRegistry, NotNullValidator, ChoiceValidator,
)
from .dedup import ByIdStrategy, FreshnessResolver

CANONICAL_AGENCIES = {
    "nhai": "NHAI",
    "morth": "MoRTH",
    "morh": "MoRTH",
    "morth pwd": "MoRTH",
    "morth (pwd)": "MoRTH",
    "morth pwd nh": "MoRTH",
    "nhidcl": "NHIDCL",
    "bro": "BRO",
    "border roads": "BRO",
    "border roads organisation": "BRO",
    "state pwd": "State PWD",
    "pwd": "State PWD",
    "state pwd (nh)": "State PWD",
    "public works department": "State PWD",
}

REPAIR_STATUS_KEYWORDS = {
    "Already Rectified": "already rectified",
    "Under Sanction / Investigation": "under sanction",
    "In Progress": "in progress",
}

STATE_NORMALIZE = {
    "delhi (ut)": "Delhi",
    "nct of delhi": "Delhi",
    "a & n islands": "Andaman and Nicobar Islands",
    "a and n islands": "Andaman and Nicobar Islands",
    "the dadra and nagar haveli": "Dadra and Nagar Haveli",
}


class NHAIBlackspotsImporter(BaseImporter):
    source_name = "nhai_blackspots"
    target_model = HighwayBlackSpot

    # CSV columns the normalize_row method reads
    REQUIRED_CSV_COLUMNS = {"state", "agency"}
    KNOWN_CSV_COLUMNS = REQUIRED_CSV_COLUMNS | {
        "black_spot_id", "latitude", "longitude", "location",
        "road_name", "final_repair_status", "repair_details", "district",
    }
    # Extra columns known to appear in NHAI CSV but not read by importer
    RECOGNIZED_EXTRA_COLUMNS = {
        "managed_by", "police_station",
        "data_as_on", "repair_start_date", "repair_end_date",
        "temporary_repair_status",
    }

    def __init__(self):
        super().__init__(source_name=self.source_name)

        self.validators.add_rule("state", NotNullValidator())
        self.validators.add_rule("agency", ChoiceValidator(list(CANONICAL_AGENCIES.keys())))

        self.dedup_strategy = ByIdStrategy(
            model=HighwayBlackSpot, id_field="official_id",
        )
        self.freshness_resolver = FreshnessResolver(timestamp_field="updated_at")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, filepath: Optional[str] = None, dry_run: bool = False,
            rows: Optional[List[Dict[str, Any]]] = None,
            metadata: Optional[dict] = None) -> Dict[str, Any]:
        if filepath:
            columns = self._get_csv_columns(filepath)
            schema_msg = self.validate_schema(columns)
            if "MISSING REQUIRED" in schema_msg:
                self.logger.error(f"Schema validation failed: {schema_msg}")
                raise ValueError(
                    f"CSV schema validation failed — {schema_msg}. "
                    f"Expected columns: {sorted(self.KNOWN_CSV_COLUMNS)}. "
                    f"Found columns: {columns}"
                )
            if schema_msg:
                self.logger.warn(f"CSV schema notes: {schema_msg}")

        parsed = self._read_csv(filepath) if filepath else (rows or [])
        batch_meta = {**(metadata or {}), "num_csv_rows": len(parsed)}
        return super().run(filepath=filepath, dry_run=dry_run, rows=parsed, metadata=batch_meta)

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    @classmethod
    def validate_schema(cls, columns: List[str]) -> str:
        col_set = set(c.strip() for c in columns)
        recognized = cls.KNOWN_CSV_COLUMNS | cls.RECOGNIZED_EXTRA_COLUMNS

        missing_required = cls.REQUIRED_CSV_COLUMNS - col_set
        missing_optional = cls.KNOWN_CSV_COLUMNS - cls.REQUIRED_CSV_COLUMNS - col_set
        unrecognized = col_set - recognized

        parts = []
        if missing_required:
            parts.append(
                f"MISSING REQUIRED columns: {', '.join(sorted(missing_required))}"
            )
        if missing_optional:
            parts.append(
                f"MISSING (optional) columns: {', '.join(sorted(missing_optional))}"
            )
        if unrecognized:
            parts.append(
                f"UNRECOGNIZED columns (will be ignored): {', '.join(sorted(unrecognized))}"
            )
        return "; ".join(parts)

    # ------------------------------------------------------------------
    # CSV reading
    # ------------------------------------------------------------------

    @staticmethod
    def _get_csv_columns(filepath: str) -> List[str]:
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            return next(reader, [])

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def normalize_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lat = self._parse_float(row.get("latitude"))
        lon = self._parse_float(row.get("longitude"))
        has_gps = lat is not None and lon is not None

        location_raw = (row.get("location") or "").strip()
        chainage_start = None
        chainage_end = None
        if location_raw:
            parsed = self.parse_chainage(location_raw)
            if parsed:
                chainage_start, chainage_end = parsed

        black_spot_id = (row.get("black_spot_id") or "").strip()
        highway_number = self._extract_highway_number(black_spot_id)
        agency_raw = (row.get("agency") or "").strip()
        managed_by = self._map_agency(agency_raw)
        state = self._normalize_state((row.get("state") or "").strip())
        district = (row.get("district") or "").strip()
        road_name = (row.get("road_name") or "").strip()
        description = self._build_description(
            row.get("final_repair_status"),
            row.get("repair_details"),
            location_raw,
        )
        confidence = self._compute_confidence(
            has_gps=has_gps,
            has_official_id=bool(black_spot_id),
            has_repair=bool(row.get("final_repair_status")),
        )

        return {
            "latitude": lat if has_gps else None,
            "longitude": lon if has_gps else None,
            "radius": 250.0,
            "severity": BlackSpotSeverity.MEDIUM,  # Default, adjust if data provides
            "accident_count": 0,
            "fatalities": 0,
            "last_accident_date": None,
            "road_name": road_name or None,
            "description": description or None,
            "source": "NHAI",
            "updated_at": datetime.utcnow(),
            "state": state or None,
            "district": district or None,
            "highway_number": highway_number,
            "managed_by": managed_by,
            "official_id": black_spot_id or None,
            "chainage_start_km": chainage_start,
            "chainage_end_km": chainage_end,
            "location_text": location_raw or None,
            "geometry_resolution": "GPS" if has_gps else "PENDING",
            "source_name": "NHAI Black Spot Dataset",
            "source_url": "https://blackspot.morth.gov.in/",
            "confidence_score": confidence,
        }

    # ------------------------------------------------------------------
    # Field-level normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_highway_number(black_spot_id: str) -> Optional[str]:
        if not black_spot_id:
            return None
        m = re.search(r'(NH|SH)\s*[-\s]*(\d+)', black_spot_id, re.IGNORECASE)
        if m:
            prefix = m.group(1).upper()
            number = m.group(2)
            return f"{prefix}-{number}"
        return None

    @staticmethod
    def _map_agency(raw: str) -> str:
        key = raw.strip().lower()
        return CANONICAL_AGENCIES.get(key, "Other")

    @staticmethod
    def _normalize_state(raw: str) -> str:
        key = raw.strip().lower()
        return STATE_NORMALIZE.get(key, raw.strip())

    @staticmethod
    def _build_description(
        repair_status: Optional[str],
        repair_details: Optional[str],
        location_text: str,
    ) -> str:
        parts = []
        if location_text:
            parts.append(f"Location: {location_text[:200]}")
        if repair_status:
            cleaned = repair_status.strip()
            parts.append(f"Repair: {cleaned}")
        if repair_details:
            cleaned = repair_details.strip()[:200]
            parts.append(f"Details: {cleaned}")
        combined = " | ".join(parts)
        return combined[:500] if combined else ""

    @staticmethod
    def _compute_confidence(
        has_gps: bool,
        has_official_id: bool,
        has_repair: bool,
    ) -> float:
        score = 0.0
        if has_gps:
            score += 0.40 * 0.9
        else:
            score += 0.40 * 0.1
        if has_official_id:
            score += 0.20 * 0.9
        score += 0.15 * 0.5
        if has_repair:
            score += 0.10 * 0.9
        score += 0.10 * 0.9
        return min(round(score, 4), 1.0)

    # ------------------------------------------------------------------
    # Preserved helpers from original stub (for external callers)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_repair_status(status_str: Optional[str]) -> str:
        if not status_str:
            return "UNKNOWN"
        clean = status_str.strip().lower()
        for canonical, keyword in REPAIR_STATUS_KEYWORDS.items():
            if keyword in clean:
                return canonical
        return "UNKNOWN"

    @staticmethod
    def infer_severity(accident_count: Optional[int],
                       fatalities: Optional[int]) -> BlackSpotSeverity:
        if fatalities and fatalities >= 10:
            return BlackSpotSeverity.HIGH
        if accident_count and accident_count >= 5:
            return BlackSpotSeverity.MEDIUM
        return BlackSpotSeverity.LOW