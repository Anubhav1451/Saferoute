from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type
from sqlalchemy.orm import Session


@dataclass
class DedupResult:
    action: str
    existing_record: Optional[Any] = None
    reason: str = ""


class BaseDedupStrategy(ABC):
    @abstractmethod
    def find(self, session: Session, row: Dict[str, Any]) -> Optional[DedupResult]:
        pass


class ByIdStrategy(BaseDedupStrategy):
    def __init__(self, model: Type, id_field: str = "official_id",
                 status_field: Optional[str] = None,
                 skip_statuses: Optional[List[str]] = None):
        self._model = model
        self._id_field = id_field
        self._status_field = status_field
        self._skip_statuses = skip_statuses or []

    def find(self, session: Session, row: Dict[str, Any]) -> Optional[DedupResult]:
        value = row.get(self._id_field)
        if not value:
            return None
        existing = session.query(self._model).filter(
            getattr(self._model, self._id_field) == value
        ).first()
        if existing is None:
            return None
        if self._status_field and self._skip_statuses:
            status = getattr(existing, self._status_field, None)
            if status in self._skip_statuses:
                return DedupResult(action="SKIP", existing_record=existing,
                                   reason=f"existing record has status={status}")
        return DedupResult(action="UPDATE", existing_record=existing,
                           reason=f"found existing {self._id_field}={value}")


class ByCoordinateStrategy(BaseDedupStrategy):
    def __init__(self, model: Type, lat_field: str = "latitude",
                 lon_field: str = "longitude", tolerance_deg: float = 0.001):
        self._model = model
        self._lat_field = lat_field
        self._lon_field = lon_field
        self._tolerance = tolerance_deg

    def find(self, session: Session, row: Dict[str, Any]) -> Optional[DedupResult]:
        lat = row.get(self._lat_field)
        lon = row.get(self._lon_field)
        if lat is None or lon is None:
            return None
        existing = session.query(self._model).filter(
            getattr(self._model, self._lat_field).between(
                float(lat) - self._tolerance, float(lat) + self._tolerance
            ),
            getattr(self._model, self._lon_field).between(
                float(lon) - self._tolerance, float(lon) + self._tolerance
            ),
        ).first()
        if existing:
            return DedupResult(action="UPDATE", existing_record=existing,
                               reason=f"found existing at ({lat}, {lon}) ±{self._tolerance}°")
        return None


class ByHighwayChainageStrategy(BaseDedupStrategy):
    def __init__(self, model: Type, highway_field: str = "highway_number",
                 chainage_field: str = "chainage_start_km",
                 tolerance_km: float = 0.1):
        self._model = model
        self._highway_field = highway_field
        self._chainage_field = chainage_field
        self._tolerance = tolerance_km

    def find(self, session: Session, row: Dict[str, Any]) -> Optional[DedupResult]:
        highway = row.get(self._highway_field)
        chainage = row.get(self._chainage_field)
        if not highway or chainage is None:
            return None
        existing = session.query(self._model).filter(
            getattr(self._model, self._highway_field) == highway,
            getattr(self._model, self._chainage_field).between(
                float(chainage) - self._tolerance,
                float(chainage) + self._tolerance,
            ),
        ).first()
        if existing:
            return DedupResult(action="UPDATE", existing_record=existing,
                               reason=f"found existing {highway} at chainage {chainage}±{self._tolerance}km")
        return None


class CompositeStrategy(BaseDedupStrategy):
    def __init__(self, strategies: List[BaseDedupStrategy]):
        self._strategies = strategies

    def find(self, session: Session, row: Dict[str, Any]) -> Optional[DedupResult]:
        for strategy in self._strategies:
            result = strategy.find(session, row)
            if result is not None:
                return result
        return None


class FreshnessResolver:
    def __init__(self, timestamp_field: str = "updated_at"):
        self._timestamp_field = timestamp_field

    def should_update(self, existing: Any, incoming_ts) -> bool:
        existing_ts = getattr(existing, self._timestamp_field, None)
        if existing_ts is None:
            return True
        if incoming_ts is None:
            return False
        return incoming_ts > existing_ts

    def resolve(self, existing: Any, row: Dict[str, Any],
                ts_field: Optional[str] = None) -> DedupResult:
        field = ts_field or self._timestamp_field
        incoming_ts = row.get(field)
        if self.should_update(existing, incoming_ts):
            return DedupResult(action="UPDATE", existing_record=existing,
                               reason=f"incoming is fresher ({incoming_ts} > {getattr(existing, field, None)})")
        return DedupResult(action="SKIP", existing_record=existing,
                           reason=f"existing is fresher or equal ({getattr(existing, field, None)} >= {incoming_ts})")
