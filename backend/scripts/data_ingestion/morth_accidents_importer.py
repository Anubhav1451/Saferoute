"""
MoRTH Accident CSV → AccidentRecord table.

Source: MoRTH "Road Accidents in India" data (OpenCity, data.gov.in, e-DAR).
Flow: CSV → validate → normalize (field mapping) → dedup → insert/update.
Supports both individual FIR records and aggregated state/city-level data.

Severity inference:
  - If CSV provides severity: map directly.
  - If fatalities > 0 and no severity: treat as FATAL.
  - If injuries > 0 and no severity: treat as GRIEVOUS.
  - Otherwise: SIMPLE.
"""

import csv
from datetime import datetime
from typing import Optional, Dict, Any, List

from app.db.models import AccidentRecord, AccidentSeverity
from .base_importer import BaseImporter
from .validators import RangeValidator
from .dedup import BaseDedupStrategy, DedupResult, FreshnessResolver

SEVERITY_MAP = {
    "fatal": AccidentSeverity.FATAL,
    "fatalities": AccidentSeverity.FATAL,
    "grievous": AccidentSeverity.GRIEVOUS,
    "grievous injury": AccidentSeverity.GRIEVOUS,
    "grievously injured": AccidentSeverity.GRIEVOUS,
    "simple": AccidentSeverity.SIMPLE,
    "simple injury": AccidentSeverity.SIMPLE,
    "minor": AccidentSeverity.SIMPLE,
    "medium": AccidentSeverity.SIMPLE,
    "high": AccidentSeverity.GRIEVOUS,
    "": None,
}

AGGREGATION_LEVELS = {"state", "district", "city", "collision_type", "violation_type",
                       "road_user", "vehicle_type", "road_class", "fir", "unknown"}


class ByAccidentRecordCompositeStrategy(BaseDedupStrategy):
    """Match existing AccidentRecord by composite key fields.

    Tries in order:
      1. (state, year, collision_type, aggregation_level) — aggregated records.
      2. (state, year, district, collision_type, aggregation_level) — city-level.
    """

    def find(self, session, row):
        q = session.query(AccidentRecord)

        state = row.get("state")
        year = row.get("year")
        coll = row.get("collision_type")
        agg = row.get("aggregation_level")

        if state and year and coll and agg:
            existing = q.filter(
                AccidentRecord.state == state,
                AccidentRecord.year == year,
                AccidentRecord.collision_type == coll,
                AccidentRecord.aggregation_level == agg,
            ).first()
            if existing:
                return DedupResult(action="UPDATE", existing_record=existing,
                                   reason=f"composite (state={state} year={year} coll={coll} agg={agg})")

            district = row.get("district")
            if district:
                existing = q.filter(
                    AccidentRecord.state == state,
                    AccidentRecord.year == year,
                    AccidentRecord.district == district,
                    AccidentRecord.collision_type == coll,
                    AccidentRecord.aggregation_level == agg,
                ).first()
                if existing:
                    return DedupResult(action="UPDATE", existing_record=existing,
                                       reason=f"composite (state={state} year={year} district={district} coll={coll} agg={agg})")

        return None


class AccidentRecordImporter(BaseImporter):
    source_name = "morth_accidents"
    target_model = AccidentRecord

    def __init__(self):
        super().__init__(source_name=self.source_name)

        self.validators.add_rule("year", RangeValidator(2000, 2030))
        self.validators.add_rule("fatalities", RangeValidator(0, 1000))
        self.validators.add_rule("injuries", RangeValidator(0, 1000))

        self.dedup_strategy = ByAccidentRecordCompositeStrategy()
        self.freshness_resolver = FreshnessResolver(timestamp_field="created_at")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, filepath: Optional[str] = None, dry_run: bool = False,
            rows: Optional[List[Dict[str, Any]]] = None,
            metadata: Optional[dict] = None) -> Dict[str, Any]:
        parsed = self._read_csv(filepath) if filepath else (rows or [])
        batch_meta = {**(metadata or {}), "num_csv_rows": len(parsed)}
        return super().run(filepath=filepath, dry_run=dry_run, rows=parsed, metadata=batch_meta)

    # ------------------------------------------------------------------
    # CSV reading
    # ------------------------------------------------------------------

    @staticmethod
    def _read_csv(filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [dict(r) for r in reader]

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def normalize_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lat = self._parse_float(row.get("latitude"))
        lon = self._parse_float(row.get("longitude"))
        has_gps = lat is not None and lon is not None

        accident_date = self._parse_date(row.get("accident_date"), row.get("year"))
        if accident_date is None:
            return None

        severity = self._infer_severity(
            raw=row.get("severity"),
            fatalities=row.get("fatalities"),
            injuries=row.get("injuries"),
        )

        year_val = self._parse_int(row.get("year")) or accident_date.year

        confidence = self._compute_confidence(
            has_gps=has_gps,
            has_severity=bool(row.get("severity")),
            has_collision_type=bool(row.get("collision_type")),
        )

        accident_id = (row.get("accident_id") or "").strip()

        return {
            "black_spot_id": None,
            "latitude": lat if has_gps else None,
            "longitude": lon if has_gps else None,
            "accident_date": accident_date,
            "severity": severity,
            "fatalities": self._parse_int(row.get("fatalities")) or 0,
            "injuries": self._parse_int(row.get("injuries")) or 0,
            "vehicles_involved": self._parse_int(row.get("vehicles_involved")) or 1,
            "road_name": (row.get("road_name") or "").strip() or None,
            "weather_condition": (row.get("weather_condition") or "").strip() or None,
            "time_of_day": (row.get("time_of_day") or "").strip() or None,
            "description": (row.get("description") or "").strip()[:500] or None,
            "source": (row.get("source") or "").strip() or "MoRTH",
            "created_at": datetime.utcnow(),
            "state": (row.get("state") or "").strip() or None,
            "district": (row.get("district") or "").strip() or None,
            "city": (row.get("city") or "").strip() or None,
            "year": year_val,
            "collision_type": (row.get("collision_type") or "").strip() or None,
            "violation_type": (row.get("violation_type") or "").strip() or None,
            "road_user_type": (row.get("road_user_type") or "").strip() or None,
            "vehicle_type": (row.get("vehicle_type") or "").strip() or None,
            "road_class": (row.get("road_class") or "").strip() or None,
            "source_name": (row.get("source_name") or "").strip() or self.source_name,
            "aggregation_level": self._normalize_agg_level(row.get("aggregation_level")),
            "accident_id": accident_id or None,
        }

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_float(val) -> Optional[float]:
        if val is None:
            return None
        try:
            v = float(val)
            return v if v == v else None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_int(val) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_date(date_val: Optional[str], year_val: Optional[str]) -> Optional[datetime]:
        if date_val:
            cleaned = str(date_val).strip()
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(cleaned, fmt)
                except ValueError:
                    continue
        if year_val:
            try:
                y = int(float(year_val))
                if 2000 <= y <= 2030:
                    return datetime(y, 1, 1)
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def _infer_severity(raw: Optional[str], fatalities, injuries) -> AccidentSeverity:
        if raw:
            key = str(raw).strip().lower()
            mapped = SEVERITY_MAP.get(key)
            if mapped is not None:
                return mapped
        f = None
        try:
            f = int(float(fatalities)) if fatalities else 0
        except (ValueError, TypeError):
            pass
        i = None
        try:
            i = int(float(injuries)) if injuries else 0
        except (ValueError, TypeError):
            pass
        if f and f > 0:
            return AccidentSeverity.FATAL
        if i and i > 0:
            return AccidentSeverity.GRIEVOUS
        return AccidentSeverity.SIMPLE

    @staticmethod
    def _normalize_agg_level(raw: Optional[str]) -> str:
        if not raw:
            return "unknown"
        cleaned = str(raw).strip().lower().replace(" ", "_")
        if cleaned in AGGREGATION_LEVELS:
            return cleaned
        return "unknown"

    @staticmethod
    def _compute_confidence(
        has_gps: bool,
        has_severity: bool,
        has_collision_type: bool,
    ) -> float:
        score = 0.0
        if has_gps:
            score += 0.35 * 1.0
        else:
            score += 0.35 * 0.1
        if has_severity:
            score += 0.25 * 1.0
        else:
            score += 0.25 * 0.5
        if has_collision_type:
            score += 0.20 * 1.0
        else:
            score += 0.20 * 0.3
        score += 0.10 * 0.9
        score += 0.10 * 0.9
        return min(round(score, 4), 1.0)

    # ------------------------------------------------------------------
    # Model override: accident_id is dedup-only, not a model column
    # ------------------------------------------------------------------

    def model_to_instance(self, normalized):
        return self.target_model(**{k: v for k, v in normalized.items() if k != "accident_id"})
