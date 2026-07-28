# app/api/v1/ai.py
import sys
import os

# Ensure backend/ is on sys.path so ml.safety_model resolves regardless of CWD
_backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
if _backend_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_backend_path))

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.db.session import get_db
from ml.safety_model import predict_safety_score

router = APIRouter(prefix="/ai", tags=["ai-safety"])

@router.get("/safety-score")
def get_safety_score(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude coordinate"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude coordinate"),
    timestamp: Optional[str] = Query(None, description="ISO format timestamp (defaults to now)"),
    radius: int = Query(1000, ge=100, le=50000, description="Radius in meters for feature calculation"),
    db: Session = Depends(get_db)
):
    """
    Get AI-predicted safety score for a specific location and time.

    Returns a safety score between 0.0 (least safe) and 1.0 (safest).
    """
    try:
        # Parse timestamp if provided
        dt = None
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid timestamp format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
                )

        # Get AI-predicted safety score
        safety_score = predict_safety_score(
            latitude=latitude,
            longitude=longitude,
            timestamp=dt,
            radius_meters=radius,
            db=db
        )

        return {
            "success": True,
            "data": {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": dt.isoformat() if dt else datetime.utcnow().isoformat(),
                "safety_score": safety_score,
                "radius_meters": radius,
                "method": "ai_prediction"
            },
            "message": "Safety score retrieved successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate safety score: {str(e)}"
        )