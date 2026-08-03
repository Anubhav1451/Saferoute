# app/core/config.py
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import List, Any
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SafeRoute AI API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    # CORS
    BACKEND_CORS_ORIGINS: Any = ["http://localhost:3000", "http://localhost:3001"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [i.strip() for i in v if i.strip()]
        else:
            # Try to interpret as JSON list? but we don't expect that
            raise ValueError(f"Invalid type for BACKEND_CORS_ORIGINS: {type(v)}")

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_database_url(cls, v: str) -> str:
        """
        Resolve DATABASE_URL from the environment and make relative SQLite
        paths absolute so runtime and tests always use the same DB location
        regardless of the process working directory.

        sqlite:///relative.db -> sqlite:///{BASE_DIR}/relative.db
        sqlite:////abs/path.db (4 slashes) is already absolute and left untouched.
        """
        if isinstance(v, str) and v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
            relative = v[len("sqlite:///"):]
            if relative and not Path(relative).is_absolute():
                return f"sqlite:///{(BASE_DIR / relative).resolve().as_posix()}"
        return v

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

    # Road Segment Risk Penalty (pre-computed from accident data)
    SEGMENT_RISK_BASE_PENALTY: float = 500.0     # Per-segment penalty multiplier × risk_score
    SEGMENT_RISK_SEARCH_RADIUS_M: float = 200.0  # Max distance from segment start to apply penalty

    # Safety Scoring
    SAFETY_SCORE_MAX_PENALTY: float = 2500.0  # Used for normalization

    # Routing Algorithm Parameters
    DEFAULT_SEARCH_RADIUS_METERS: float = 2000.0  # Default radius for nearby safety data
    BASE_SEARCH_RADIUS_METERS: float = 5000.0    # Base radius for route search area
    DEFAULT_INTERPOLATION_POINTS: int = 20       # Number of points for path interpolation
    PATH_VARIATION_COUNT: int = 5                # Number of path variations to test

    # Graph-based Routing Parameters
    GRAPH_NEIGHBOR_COUNT: int = 30               # K for K-nearest neighbors in graph building
    RISK_FACTOR_SAFETY: float = 3.0              # Influence of (1-safety_score) on risk
    RISK_FACTOR_LIGHTING: float = 4.0            # Influence of low lighting on risk
    RISK_FACTOR_CROWD: float = 1.5               # Influence of sparse crowd on risk
    ROUTE_COST_ALPHA: float = 50.0               # Multiplier for risk in safest route cost

    # Mapbox API Configuration
    MAPBOX_DIRECTIONS_TIMEOUT_SEC: int = 15      # Timeout for Mapbox Directions API calls
    MAPBOX_TOKEN: str = ""                       # Mapbox access token (optional, no longer required for startup)

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    RATE_LIMIT_PER_METHOD: bool = True  # Apply limits per HTTP method
    RATE_LIMIT_MAX_CLIENTS: int = 10000  # Cap on in-memory token buckets (DoS bound)
    RATE_LIMIT_EXEMPT_PATHS: list = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/debug/env"]

    # Request Size Limits
    REQUEST_SIZE_LIMIT_ENABLED: bool = False
    REQUEST_SIZE_LIMIT_BYTES: int = 5 * 1024 * 1024  # 5MB default
    REQUEST_SIZE_LIMIT_EXEMPT_PATHS: list = ["/", "/health", "/docs", "/redoc", "/openapi.json", "/debug/env"]

    # Timeout Handling
    REQUEST_TIMEOUT_ENABLED: bool = False
    REQUEST_TIMEOUT_SECONDS: int = 30
    DB_QUERY_TIMEOUT_SECONDS: int = 10

    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    STRICT_TRANSPORT_SECURITY_MAX_AGE: int = 31536000  # 1 year
    CONTENT_SECURITY_POLICY: str = "default-src 'self'"

    # Trusted Proxy
    TRUSTED_PROXY_ENABLED: bool = False
    TRUSTED_PROXY_COUNT: int = 1  # Number of trusted proxy hops

    # Slow Request Logging
    SLOW_REQUEST_THRESHOLD: float = 1.0  # Seconds
    SLOW_REQUEST_LOG_ENABLED: bool = True

    # API Key Authentication
    API_KEY_REQUIRED: bool = False
    API_KEYS: list = []

    @property
    def api_keys_set(self) -> bool:
        """Check if API keys have been configured."""
        return bool(self.API_KEYS)

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """
        Fail fast on misconfigured production secrets.

        When API key auth is enabled (API_KEY_REQUIRED=True) but no keys are
        configured, every protected endpoint would reject all requests with 401.
        Raise at startup instead of failing silently in production.
        """
        if not self.DEBUG and self.API_KEY_REQUIRED and not self.api_keys_set:
            raise ValueError(
                "API_KEY_REQUIRED is True but no API_KEYS are configured. "
                "Set API_KEYS (comma-separated) for production."
            )
        return self

    # Weather Cache Configuration
    WEATHER_CACHE_MAX_SIZE: int = 1000
    WEATHER_CACHE_TTL_SECONDS: int = 300

    # OSM Importer Configuration
    OSM_DRIVABLE_HIGHWAYS: list = [
        "motorway", "trunk", "primary", "secondary", "tertiary",
        "unclassified", "residential", "service", "living_street",
        "pedestrian", "track", "footway", "cycleway", "path"
    ]

    # File paths
    BASE_DIR: Path = BASE_DIR

    model_config = {
        "env_file": BASE_DIR / ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Create global settings instance
settings = Settings()