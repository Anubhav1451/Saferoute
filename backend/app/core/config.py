# app/core/config.py
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets
import os
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SafeRoute AI API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./saferoute.db")
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # Routing Engine Configuration
    SAFETY_WEIGHT_DEFAULT: float = 0.7
    SAFETY_WEIGHT_MIN: float = 0.0
    SAFETY_WEIGHT_MAX: float = 1.0
    DEFAULT_SAFETY_WEIGHT: float = 0.7

    # Penalty Configuration (making previously hardcoded values configurable)
    CRIME_HOTSPOT_HIGH_PENALTY_BASE: float = 2500.0
    CRIME_HOTSPOT_MEDIUM_PENALTY: float = 500.0
    CRIME_HOTSPOT_LOW_PENALTY: float = 100.0
    SAFETY_NODE_LOW_LIGHTING_PENALTY: float = 50.0
    SAFETY_NODE_SPARSE_CROWD_PENALTY: float = 30.0
    USER_REPORT_BASE_PENALTY: float = 100.0
    HIGH_RISK_SEGMENT_MULTIPLIER: float = 3.0
    HIGH_RISK_SEGMENT_ADDITIONAL_FACTOR: float = 0.5

    # Safety Scoring
    SAFETY_SCORE_MAX_PENALTY: float = 2500.0  # Used for normalization

    # Routing Algorithm Parameters
    DEFAULT_SEARCH_RADIUS_METERS: float = 2000.0  # Default radius for nearby safety data
    BASE_SEARCH_RADIUS_METERS: float = 5000.0    # Base radius for route search area
    DEFAULT_INTERPOLATION_POINTS: int = 20       # Number of points for path interpolation
    PATH_VARIATION_COUNT: int = 5                # Number of path variations to test

    # Rate Limiting (placeholder for future implementation)
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # File paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Create global settings instance
settings = Settings()