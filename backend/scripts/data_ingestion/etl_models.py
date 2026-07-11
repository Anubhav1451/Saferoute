from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import os

ETL_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(ETL_DB_DIR, exist_ok=True)
ETL_DB_PATH = os.path.join(ETL_DB_DIR, "etl_metadata.db")

EtlBase = declarative_base()


class EtlBatch(EtlBase):
    __tablename__ = "etl_batches"

    id = Column(Integer, primary_key=True)
    source_name = Column(String(100), nullable=False, index=True)
    source_file = Column(String(500), nullable=True)
    source_hash = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="RUNNING")
    total_records = Column(Integer, default=0)
    inserted = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    quarantined = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(String(1000), nullable=True)
    metadata_json = Column(Text, nullable=True)

    records = relationship("EtlRecord", backref="batch", lazy="dynamic")
    error_rows = relationship("EtlError", backref="batch", lazy="dynamic")


class EtlRecord(EtlBase):
    __tablename__ = "etl_records"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("etl_batches.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=True)
    official_id = Column(String(200), nullable=True, index=True)
    action = Column(String(20), nullable=False)
    target_model = Column(String(100), nullable=True)
    target_id = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EtlError(EtlBase):
    __tablename__ = "etl_errors"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("etl_batches.id"), nullable=False, index=True)
    row_index = Column(Integer, nullable=True)
    raw_data_json = Column(Text, nullable=True)
    error_type = Column(String(50), nullable=False)
    error_message = Column(String(500), nullable=False)
    field_errors_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    resolved = Column(Boolean, default=False)


def init_etl_db():
    engine = create_engine(f"sqlite:///{ETL_DB_PATH}", connect_args={"check_same_thread": False})
    EtlBase.metadata.create_all(engine)
    return engine
