# app/schemas/sos.py
from pydantic import BaseModel, Field
from datetime import datetime


class SOSRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    timestamp: datetime