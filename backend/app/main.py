# app/main.py
import os
import sys
import logging

# Add backend directory to sys.path to allow imports from app package
_backend_path = os.path.join(os.path.dirname(__file__), '..')
if _backend_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_path))

# Must load .env BEFORE any app imports that trigger Settings() instantiation
def load_env_file(env_path=".env"):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"\'')
                # SEC-16 (T2): deployment environment variables always win.
                # Only populate a key from .env when it is NOT already set in
                # the real environment; never overwrite an existing value.
                if key not in os.environ:
                    os.environ[key] = value

load_env_file()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.api.v1 import api_router as v1_router
from app.api.exceptions import (
    http_exception_handler,
    general_exception_handler
)
from app.db.session import get_db
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("saferoute.main")


# SEC-16 (T5): expose interactive docs (/docs, /redoc) and the raw OpenAPI
# schema only in development. When DEBUG=false (production) they are disabled
# entirely — no Swagger UI, no schema endpoint.
app = FastAPI(
    title="SafeRoute AI API",
    description="Smart navigation API with safety scores, crime data, and environmental factors",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# Configure CORS from settings
# SEC-15: methods/headers are explicit (not "*"). The API only serves
# GET/POST plus CORS preflight OPTIONS, and only accepts the JSON content
# type plus the two API-key auth headers. Origins remain env-driven.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-KEY", "Authorization", "Accept"],
)

# Add exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Add authentication middleware
from app.api.middleware.auth import AuthMiddleware
app.add_middleware(AuthMiddleware)

# Add security middleware
from app.api.middleware.timeout import TimeoutMiddleware
from app.api.middleware.request_size import RequestSizeLimitMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(TimeoutMiddleware)

# Include API routes
app.include_router(v1_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SafeRoute AI API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check endpoint with dependency verification"""
    health_status = {
        "status": "healthy",
        "service": "saferoute-ai-api",
        "timestamp": time.time(),
        "checks": {}
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception:
        # SEC-16 (T3): log the real exception server-side; never echo it to
        # clients. Response schema is unchanged.
        logger.exception("Health check: database connection failed")
        health_status["status"] = "degraded"  # Not fully unhealthy since API might still work
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": "Database connection failed"
        }

    # Overall status based on critical checks
    if any(check.get("status") == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Return basic system metrics for the current process."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)
        return {
            "cpu_percent": cpu_percent,
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_vms_mb": memory_info.vms / 1024 / 1024,
            "open_files": len(process.open_files()),
            "num_threads": process.num_threads(),
            "timestamp": time.time()
        }
    except Exception:
        # SEC-16 (T3): log the real exception server-side; return a generic
        # message. Response schema is unchanged.
        logger.exception("Metrics collection failed")
        return {
            "error": "Metrics collection failed",
            "timestamp": time.time()
        }

@app.get("/debug/env", tags=["debug"])
async def debug_env():
    """Debug endpoint — only served when DEBUG=True. Never exposes secret values."""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "debug_mode": settings.DEBUG,
        "cors_origins_count": len(settings.BACKEND_CORS_ORIGINS),
    }