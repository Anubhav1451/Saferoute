from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Enum as SQLEnum, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class LightingLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CrowdDensity(enum.Enum):
    SPARSE = "SPARSE"
    NORMAL = "NORMAL"
    DENSE = "DENSE"


class SeverityLevel(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SafetyNode(Base):
    __tablename__ = "safety_nodes"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    safety_score = Column(Float, nullable=False)  # 0.0 to 1.0, higher is safer
    lighting_level = Column(SQLEnum(LightingLevel), nullable=False, index=True)
    crowd_density = Column(SQLEnum(CrowdDensity), nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Composite index for spatial queries (latitude, longitude)
    __table_args__ = (Index('ix_safety_nodes_lat_lon', 'latitude', 'longitude'),)


class CrimeHotspot(Base):
    __tablename__ = "crime_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    radius = Column(Float, nullable=False)  # in meters
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    description = Column(String(500))
    # Composite index for spatial queries
    __table_args__ = (Index('ix_crime_hotspots_lat_lon', 'latitude', 'longitude'),)


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    report_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)
    # Composite index for spatial queries
    __table_args__ = (Index('ix_user_reports_lat_lon', 'latitude', 'longitude'),)