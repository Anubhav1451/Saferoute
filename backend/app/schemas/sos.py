# app/schemas/sos.py
from pydantic import BaseModel
from datetime import datetime


class SOSRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime