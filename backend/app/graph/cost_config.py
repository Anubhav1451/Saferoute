"""
Cost Configuration for Route Cost Engine.
Defines configurable weighting factors for different cost components.
"""
import json
import logging
from typing import Dict

from pydantic import BaseModel, Field


class CostWeightConfig(BaseModel):
    """
    Configuration for cost computation weights.
    All weights are multipliers that can be adjusted based on routing preferences.
    """

    # Base weights for different cost components
    distance_weight: float = Field(default=1.0, description="Base weight for distance cost")
    risk_weight: float = Field(default=1.0, description="Base weight for risk cost")
    elevation_weight: float = Field(default=0.0, description="Base weight for elevation cost")
    road_class_weight: float = Field(default=0.0, description="Base weight for road class cost")
    surface_weight: float = Field(default=0.0, description="Base weight for surface cost")
    turn_weight: float = Field(default=0.0, description="Base weight for turn cost (placeholder)")
    weather_weight: float = Field(default=0.0, description="Base weight for weather cost (placeholder)")
    traffic_weight: float = Field(default=1.0, description="Base weight for traffic cost (NEW)")

    # Road class specific weights (can be overridden per road type)
    road_class_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights for specific road classes (e.g., {'motorway': 1.0, 'residential': 0.8})"
    )

    # Surface type specific weights (can be overridden per surface type)
    surface_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Weights for specific surface types (e.g., {'paved': 1.0, 'unpaved': 1.5})"
    )

    # Distance cost parameters
    distance_per_meter: float = Field(
        default=0.001,
        description="Cost per meter of distance (adjusts scaling)"
    )

    # Risk cost parameters
    risk_score_multiplier: float = Field(
        default=100.0,
        description="Multiplier to convert risk score (0-1) to cost units"
    )

    # Elevation cost parameters
    elevation_cost_per_meter: float = Field(
        default=0.01,
        description="Additional cost per meter of elevation change"
    )

    # Traffic cost parameters (NEW)
    traffic_congestion_multiplier: float = Field(
        default=50.0,
        description="Multiplier for congestion ratio to cost"
    )
    traffic_closure_penalty: float = Field(
        default=10000.0,
        description="Penalty cost for road closures (effectively blocks route)"
    )
    traffic_base_penalty: float = Field(
        default=10.0,
        description="Base penalty for traffic incidents"
    )

    # Features toggles
    enable_elevation: bool = Field(default=False, description="Whether to compute elevation cost")
    enable_road_class: bool = Field(default=False, description="Whether to compute road class cost")
    enable_surface: bool = Field(default=False, description="Whether to compute surface cost")
    enable_turn: bool = Field(default=False, description="Whether to compute turn cost (placeholder)")
    enable_weather: bool = Field(default=False, description="Whether to compute weather cost (placeholder)")
    enable_traffic: bool = Field(default=True, description="Whether to compute traffic cost (NEW)")


def load_cost_config_from_app() -> CostWeightConfig:
    """
    Load cost weights from application configuration if available.
    Falls back to default configuration if not found.
    """
    try:
        from ..core.config import settings

        # Check if cost configuration exists in settings
        if hasattr(settings, 'COST_WEIGHT_CONFIG'):
            config_dict = settings.COST_WEIGHT_CONFIG
            if isinstance(config_dict, dict):
                return CostWeightConfig(**config_dict)
    except ImportError:
        # Core config not available
        pass
    except Exception:
        # Error parsing config, fall back to defaults
        pass

    # Return default configuration
    return CostWeightConfig()


def load_cost_config_from_file(file_path: str) -> CostWeightConfig:
    """
    Load cost weights from a JSON file.

    Args:
        file_path: Path to JSON configuration file

    Returns:
        CostWeightConfig instance
    """
    try:
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return CostWeightConfig(**config_dict)
    except FileNotFoundError:
        # File doesn't exist, return defaults
        return CostWeightConfig()
    except Exception as e:
        # Error reading/parsing file, return defaults
        logger = logging.getLogger(__name__)
        logger.warning("Could not load cost config from %s: %s", file_path, e)
        return CostWeightConfig()


def get_default_cost_config() -> CostWeightConfig:
    """
    Get the default cost weight configuration.

    Returns:
        CostWeightConfig with default values
    """
    return CostWeightConfig()


# Predefined cost profiles for different routing preferences
COST_PROFILES = {
    "fastest": CostWeightConfig(
        distance_weight=1.0,
        risk_weight=0.1,  # Minimize time, avoid major risks only
        elevation_weight=0.0,
        road_class_weight=0.5,  # Prefer highways
        surface_weight=0.0,
        enable_road_class=True,
        traffic_weight=1.5,  # Strongly consider traffic for fastest route
        enable_traffic=True
    ),
    "safest": CostWeightConfig(
        distance_weight=0.1,  # Willing to take longer for safety
        risk_weight=2.0,      # Strongly avoid risk
        elevation_weight=0.0,
        road_class_weight=0.0,
        surface_weight=0.0,
        traffic_weight=1.0
    ),
    "balanced": CostWeightConfig(
        distance_weight=1.0,
        risk_weight=1.0,      # Balance distance and risk
        elevation_weight=0.0,
        road_class_weight=0.0,
        surface_weight=0.0,
        traffic_weight=1.0
    ),
    "eco": CostWeightConfig(
        distance_weight=1.0,
        risk_weight=0.5,
        elevation_weight=0.5,  # Avoid steep hills for fuel efficiency
        road_class_weight=0.3,
        surface_weight=0.0,
        enable_elevation=True,
        enable_road_class=True,
        traffic_weight=0.5  # Less emphasis on traffic for eco routing
    )
}


def get_cost_profile(profile_name: str) -> CostWeightConfig:
    """
    Get a predefined cost profile.

    Args:
        profile_name: Name of the profile ("fastest", "safest", "balanced", "eco")

    Returns:
        CostWeightConfig instance
    """
    return COST_PROFILES.get(profile_name.lower(), CostWeightConfig())