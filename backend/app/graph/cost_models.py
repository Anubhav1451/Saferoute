"""
Cost Models for Route Cost Engine.
Defines data structures for cost computation outputs.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EdgeCostOutput(BaseModel):
    """
    Output model for edge cost computation.
    Contains only the cost components as specified in requirements.
    """
    distance_cost: float
    risk_cost: float
    elevation_cost: float
    road_class_cost: float
    surface_cost: float
    turn_cost: float  # Placeholder
    weather_cost: float  # Placeholder
    traffic_cost: float  # NEW: Traffic cost component
    total_cost: float

    # Additional metadata for debugging/tracing (not part of core cost)
    edge_id: Optional[int] = None
    computation_timestamp: Optional[datetime] = None

    class Config:
        # Allow creation from ORM objects
        from_attributes = True


class CostComponents(BaseModel):
    """
    Individual cost components before aggregation.
    """
    distance: float = 0.0
    risk: float = 0.0
    elevation: float = 0.0
    road_class: float = 0.0
    surface: float = 0.0
    turn: float = 0.0  # Placeholder
    weather: float = 0.0  # Placeholder
    traffic: float = 0.0  # NEW: Traffic component

    def total(self) -> float:
        """Calculate total cost from components."""
        return (
            self.distance + self.risk + self.elevation +
            self.road_class + self.surface + self.turn + self.weather + self.traffic
        )