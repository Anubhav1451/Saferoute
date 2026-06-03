from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Enum as SQLEnum
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
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    safety_score = Column(Float, nullable=False)  # 0.0 to 1.0, higher is safer
    lighting_level = Column(SQLEnum(LightingLevel), nullable=False)
    crowd_density = Column(SQLEnum(CrowdDensity), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrimeHotspot(Base):
    __tablename__ = "crime_hotspots"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, nullable=False)  # in meters
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    description = Column(String(500))


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    report_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
