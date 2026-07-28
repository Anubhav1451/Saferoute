import sys
import os
import re
import csv
import json
import time
import hashlib
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any, Type, Generator
from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.db.session import engine as app_engine
from app.db.models import (
    Base, HighwayBlackSpot, AccidentRecord, RoadSegmentRisk,
    BlackSpotSeverity, AccidentSeverity,
)

# Handle both `python -m` (relative) and direct execution (absolute)
try:
    from .etl_models import EtlBatch, EtlRecord, EtlError, init_etl_db
    from .etl_logger import EtlLogger
    from .validators import ValidatorRegistry, ValidationResult
    from .dedup import BaseDedupStrategy, DedupResult, FreshnessResolver
except ImportError:
    PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, PACKAGE_DIR)
    from etl_models import EtlBatch, EtlRecord, EtlError, init_etl_db
    from etl_logger import EtlLogger
    from validators import ValidatorRegistry, ValidationResult
    from dedup import BaseDedupStrategy, DedupResult, FreshnessResolver


class BaseImporter:
    source_name: str = "unknown"
    batch_size: int = 500
    target_model: Optional[Type] = None

    def __init__(self, source_name: Optional[str] = None):
        self.source_name = source_name or self.__class__.source_name
        self.batch_size = self.__class__.batch_size
        self._app_session: Optional[Session] = None
        self._etl_session: Optional[Session] = None
        self._batch: Optional[EtlBatch] = None
        self._etl_engine = None

        self.validators = ValidatorRegistry()
        self.dedup_strategy: Optional[BaseDedupStrategy] = None
        self.freshness_resolver: Optional[FreshnessResolver] = None

        self.logger = EtlLogger(self.source_name)
        self._counters: Dict[str, int] = defaultdict(int)
        self._start_time: Optional[float] = None
        self._record_buffer: List[Any] = []
        self._quarantine_buffer: List[Any] = []
        self._flush_interval: int = 200

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def get_session(self) -> Session:
        if self._app_session is None:
            self._app_session = sessionmaker(bind=app_engine)()
        return self._app_session

    def get_etl_session(self) -> Session:
        if self._etl_session is None:
            if self._etl_engine is None:
                self._etl_engine = init_etl_db()
            self._etl_session = sessionmaker(bind=self._etl_engine)()
        return self._etl_session

    def close_session(self, session: Session) -> None:
        if session is not None:
            session.close()

    def close_all(self):
        self._flush_buffers()
        if self._app_session:
            self._app_session.close()
            self._app_session = None
        if self._etl_session:
            self._etl_session.close()
            self._etl_session = None

    # ------------------------------------------------------------------
    # Transaction management
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    @contextmanager
    def etl_transaction(self) -> Generator[Session, None, None]:
        session = self.get_etl_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    @contextmanager
    def savepoint(self, session: Session, name: str = "sp") -> Generator[None, None, None]:
        begin = session.begin_nested()
        try:
            yield
            begin.commit()
        except Exception:
            begin.rollback()
            raise

    # ------------------------------------------------------------------
    # Batch lifecycle
    # ------------------------------------------------------------------

    def start_batch(self, source_file: Optional[str] = None,
                    total_records: int = 0, metadata: Optional[dict] = None) -> int:
        source_hash = None
        if source_file and os.path.exists(source_file):
            h = hashlib.sha256()
            with open(source_file, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            source_hash = h.hexdigest()[:16]

        etl_session = self.get_etl_session()
        batch = EtlBatch(
            source_name=self.source_name,
            source_file=source_file,
            source_hash=source_hash,
            status="RUNNING",
            total_records=total_records,
            started_at=datetime.utcnow(),
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        etl_session.add(batch)
        etl_session.commit()
        etl_session.refresh(batch)

        self._batch = batch
        self._start_time = time.time()
        self._counters.clear()
        self.logger.set_batch(batch.id)
        self.logger.info(f"Batch started: source={self.source_name} file={source_file} records={total_records}",
                         total=total_records)
        return batch.id

    def end_batch(self, status: str = "COMPLETED", error_message: Optional[str] = None):
        if self._batch is None:
            return
        duration = time.time() - self._start_time if self._start_time else 0.0
        etl_session = self.get_etl_session()
        self._batch.status = status
        self._batch.inserted = self._counters.get("inserted", 0)
        self._batch.updated = self._counters.get("updated", 0)
        self._batch.skipped = self._counters.get("skipped", 0)
        self._batch.errors = self._counters.get("errors", 0)
        self._batch.quarantined = self._counters.get("quarantined", 0)
        self._batch.completed_at = datetime.utcnow()
        self._batch.duration_seconds = round(duration, 3)
        if error_message:
            self._batch.error_message = error_message[:1000]
        etl_session.commit()
        self.logger.info(f"Batch {status.lower()}: {self._batch.inserted} inserted, "
                         f"{self._batch.updated} updated, {self._batch.skipped} skipped, "
                         f"{self._batch.errors} errors in {duration:.1f}s",
                         inserted=self._batch.inserted, updated=self._batch.updated,
                         skipped=self._batch.skipped, errors=self._batch.errors)
        self.logger.clear_batch()

    # ------------------------------------------------------------------
    # Record tracking
    # ------------------------------------------------------------------

    def track_record(self, row_index: int, action: str,
                     official_id: Optional[str] = None,
                     target_id: Optional[int] = None,
                     confidence: Optional[float] = None,
                     error_message: Optional[str] = None):
        if self._batch is None:
            return
        etl_session = self.get_etl_session()
        rec = EtlRecord(
            batch_id=self._batch.id,
            row_index=row_index,
            official_id=official_id,
            action=action,
            target_model=self.target_model.__name__ if self.target_model else None,
            target_id=target_id,
            confidence_score=confidence,
            error_message=error_message,
        )
        self._record_buffer.append(rec)
        if len(self._record_buffer) >= self._flush_interval:
            self._flush_buffers()

    # ------------------------------------------------------------------
    # Quarantine
    # ------------------------------------------------------------------

    def quarantine(self, row: Dict[str, Any], row_index: int,
                   error_type: str, message: str,
                   field_errors: Optional[Dict[str, List[str]]] = None):
        if self._batch is None:
            return
        etl_session = self.get_etl_session()
        sanitized = {k: str(v)[:500] for k, v in row.items()}
        err = EtlError(
            batch_id=self._batch.id,
            row_index=row_index,
            raw_data_json=json.dumps(sanitized, default=str),
            error_type=error_type,
            error_message=str(message)[:500],
            field_errors_json=json.dumps(field_errors) if field_errors else None,
        )
        self._quarantine_buffer.append(err)
        self._counters["quarantined"] += 1
        self.logger.warn(f"Quarantined row {row_index}: [{error_type}] {message}",
                         row=row_index, error=error_type)
        if len(self._quarantine_buffer) >= self._flush_interval:
            self._flush_buffers()

    def _flush_buffers(self):
        """Flush buffered ETL records and quarantine entries to the database."""
        etl_session = self.get_etl_session()
        if self._record_buffer:
            etl_session.add_all(self._record_buffer)
            etl_session.commit()
            self._record_buffer.clear()
        if self._quarantine_buffer:
            etl_session.add_all(self._quarantine_buffer)
            etl_session.commit()
            self._quarantine_buffer.clear()

    # ------------------------------------------------------------------
    # Validation hook
    # ------------------------------------------------------------------

    def validate_row(self, row: Dict[str, Any]) -> ValidationResult:
        return self.validators.validate(row)

    # ------------------------------------------------------------------
    # Dedup hook
    # ------------------------------------------------------------------

    def resolve_dedup(self, session: Session, row: Dict[str, Any]) -> DedupResult:
        if self.dedup_strategy:
            result = self.dedup_strategy.find(session, row)
            if result is not None:
                return result
        return DedupResult(action="INSERT")

    # ------------------------------------------------------------------
    # Core row processing pipeline
    # ------------------------------------------------------------------

    def process_row(self, session: Session, row: Dict[str, Any],
                    row_index: int) -> str:
        validation = self.validate_row(row)
        if not validation.is_valid:
            self.quarantine(row, row_index, "VALIDATION",
                            "; ".join(validation.errors[:3]),
                            validation.field_errors)
            self._counters["errors"] += 1
            self.track_record(row_index, "ERROR", error_message=validation.errors[0])
            return "ERROR"

        normalized = self.normalize_row(row)
        if normalized is None:
            self._counters["skipped"] += 1
            self.logger.row_summary(row_index, "SKIP", reason="normalize_row returned None")
            self.track_record(row_index, "SKIP")
            return "SKIP"

        dedup = self.resolve_dedup(session, normalized)

        if dedup.action == "INSERT":
            obj = self.model_to_instance(normalized)
            session.add(obj)
            session.flush()
            target_id = obj.id if hasattr(obj, "id") else None
            self._counters["inserted"] += 1
            self.logger.row_summary(row_index, "INSERT",
                                    model=self.target_model.__name__ if self.target_model else None,
                                    official_id=normalized.get("official_id"))
            self.track_record(row_index, "INSERT",
                              official_id=normalized.get("official_id"),
                              target_id=target_id,
                              confidence=normalized.get("confidence_score"))
            return "INSERT"

        if dedup.action == "UPDATE":
            if self.freshness_resolver:
                resolution = self.freshness_resolver.resolve(dedup.existing_record, normalized)
                if resolution.action == "SKIP":
                    self._counters["skipped"] += 1
                    self.logger.row_summary(row_index, "SKIP",
                                            reason=resolution.reason,
                                            official_id=normalized.get("official_id"))
                    self.track_record(row_index, "SKIP",
                                      official_id=normalized.get("official_id"))
                    return "SKIP"
            self.update_instance(dedup.existing_record, normalized)
            session.flush()
            self._counters["updated"] += 1
            self.logger.row_summary(row_index, "UPDATE",
                                    model=self.target_model.__name__ if self.target_model else None,
                                    official_id=normalized.get("official_id"))
            self.track_record(row_index, "UPDATE",
                              official_id=normalized.get("official_id"),
                              confidence=normalized.get("confidence_score"))
            return "UPDATE"

        if dedup.action == "SKIP":
            self._counters["skipped"] += 1
            self.logger.row_summary(row_index, "SKIP", reason=dedup.reason,
                                    official_id=normalized.get("official_id"))
            self.track_record(row_index, "SKIP", official_id=normalized.get("official_id"))
            return "SKIP"

        return "ERROR"

    # ------------------------------------------------------------------
    # Subclass hooks (must override)
    # ------------------------------------------------------------------

    def normalize_row(self, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Subclasses must implement normalize_row()")

    def model_to_instance(self, normalized: Dict[str, Any]) -> Any:
        if self.target_model is None:
            raise NotImplementedError("Subclasses must set target_model or override model_to_instance()")
        return self.target_model(**normalized)

    def update_instance(self, instance: Any, normalized: Dict[str, Any]) -> None:
        for key, value in normalized.items():
            if hasattr(instance, key) and key not in ("id", "created_at"):
                setattr(instance, key, value)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self, filepath: Optional[str] = None, dry_run: bool = False,
            rows: Optional[List[Dict[str, Any]]] = None,
            metadata: Optional[dict] = None) -> Dict[str, Any]:
        if dry_run:
            self.logger.info(f"DRY RUN mode: no records will be written")
            return {"dry_run": True, "source": self.source_name}

        session = self.get_session()
        try:
            total = len(rows) if rows else 0
            batch_meta = metadata or {}
            batch_meta["dry_run"] = dry_run
            self.start_batch(source_file=filepath, total_records=total,
                             metadata=batch_meta)

            if rows:
                for i, row in enumerate(rows):
                    try:
                        with self.savepoint(session, f"row_{i}"):
                            self.process_row(session, row, i)
                    except Exception as e:
                        self._counters["errors"] += 1
                        self.quarantine(row, i, "EXCEPTION", str(e))
                        self.logger.exception(f"Row {i} failed", row=i)
                        self.track_record(i, "ERROR", error_message=str(e)[:500])

            session.commit()
            self.end_batch("COMPLETED")
        except Exception as e:
            session.rollback()
            self.end_batch("FAILED", error_message=str(e))
            self.logger.exception(f"Batch failed: {e}")
            raise
        finally:
            self.close_all()

        return {
            "source": self.source_name,
            "batch_id": self._batch.id if self._batch else None,
            "status": self._batch.status if self._batch else "FAILED",
            "total_records": self._counters.get("total", 0),
            "inserted": self._counters.get("inserted", 0),
            "updated": self._counters.get("updated", 0),
            "skipped": self._counters.get("skipped", 0),
            "errors": self._counters.get("errors", 0),
            "quarantined": self._counters.get("quarantined", 0),
            "duration_seconds": self._batch.duration_seconds if self._batch else 0.0,
        }

    # ------------------------------------------------------------------
    # Chainage parsing (kept from original)
    # ------------------------------------------------------------------

    @staticmethod
    def parse_chainage(chainage_str: str) -> Optional[Tuple[float, float]]:
        def _to_km(km_part: str, sub_part: str) -> float:
            km = float(km_part)
            val = float(sub_part)
            if len(sub_part) <= 2:
                km += val / 10.0
            else:
                km += val / 1000.0
            return km

        if not chainage_str:
            return None

        cleaned = re.sub(r'([+./])\.', r'\1', chainage_str)

        m = re.search(
            r'(\d+)\s*[+./]\s*(\d+)\s*to\s*(\d+)\s*[+./]\s*(\d+)',
            cleaned, re.IGNORECASE
        )
        if m:
            start_km = _to_km(m.group(1), m.group(2))
            end_km = _to_km(m.group(3), m.group(4))
            return (start_km, end_km)

        m = re.search(r'(\d+\.?\d*)\s*to\s*(\d+\.?\d*)', cleaned)
        if m:
            return (float(m.group(1)), float(m.group(2)))

        return None

    # ------------------------------------------------------------------
    # Shared CSV/numeric utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        try:
            v = float(val)
            if v != v:
                return None
            return v
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _read_csv(filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [dict(r) for r in reader]


class BaseAccidentImporter(BaseImporter):
    pass
