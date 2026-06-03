from pydantic import BaseModel, Field
from typing import List, Optional


class Coordinate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class RouteRequest(BaseModel):
    source: Coordinate = Field(..., description="Starting point coordinates")
    destination: Coordinate = Field(..., description="Destination coordinates")
    safety_weight: float = Field(default=0.7, ge=0, le=1, description="Weight for safety vs distance (0 = fastest, 1 = safest)")


class RouteSegment(BaseModel):
    from_coord: Coordinate
    to_coord: Coordinate
    distance: float
    safety_score: float
    penalty: float


class RouteResponse(BaseModel):
    safest_route: List[Coordinate] = Field(..., description="Safest route coordinates")
    fastest_route: List[Coordinate] = Field(..., description="Fastest route coordinates")
    safest_distance: float = Field(..., description="Total distance of safest route in meters")
    fastest_distance: float = Field(..., description="Total distance of fastest route in meters")
    safest_safety_score: float = Field(..., description="Average safety score of safest route")
    fastest_safety_score: float = Field(..., description="Average safety score of fastest route")
    route_segments: Optional[List[RouteSegment]] = Field(None, description="Detailed route segments")
