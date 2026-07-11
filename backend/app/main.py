# app/main.py
import os
import logging
from pathlib import Path

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
                os.environ[key] = value

load_env_file()

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from app.api.v1 import api_router as v1_router
from app.api.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.db.session import get_db

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Debug: check if MAPBOX_TOKEN is loaded
token = os.getenv("MAPBOX_TOKEN")
if token:
    print(f"DEBUG: MAPBOX_TOKEN loaded from .env: {token[:10]}...")
else:
    print("DEBUG: MAPBOX_TOKEN not found in .env")


app = FastAPI(
    title="SafeRoute AI API",
    description="Smart navigation API with safety scores, crime data, and environmental factors",
    version="0.1.0"
)


# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004", "http://localhost:3005", "http://localhost:3006"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(Exception, general_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

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
    except Exception as e:
        health_status["status"] = "degraded"  # Not fully unhealthy since API might still work
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }

    # Overall status based on critical checks
    if any(check.get("status") == "unhealthy" for check in health_status["checks"].values()):
        health_status["status"] = "degraded"

    return health_status

@app.get("/debug/env", tags=["debug"])
async def debug_env():
    token = os.getenv("MAPBOX_TOKEN")
    if token:
        return {"masked_token": token[:4] + "..." + token[-4:] if len(token) > 8 else "too_short"}
    else:
        return {"token_set": false}