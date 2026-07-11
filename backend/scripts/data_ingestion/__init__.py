# Data ingestion package for SafeRoute AI.
# Handles MoRTH/NHAI black spot data, e-DAR accident records,
# and derived road segment risk computation.

from .etl_logger import EtlLogger
from .etl_models import EtlBatch, EtlRecord, EtlError, init_etl_db
from .validators import (
    ValidatorRegistry, ValidationResult, BaseValidator,
    NotNullValidator, RangeValidator, RegexValidator,
    ChoiceValidator, ConditionalValidator,
)
from .dedup import (
    BaseDedupStrategy, DedupResult, ByIdStrategy,
    ByCoordinateStrategy, ByHighwayChainageStrategy,
    CompositeStrategy, FreshnessResolver,
)
from .base_importer import BaseImporter, BaseAccidentImporter
from .morth_blackspots_importer import MoRTHBlackSpotImporter
from .morth_accidents_importer import AccidentRecordImporter
from .compute_segment_risk import RoadSegmentRiskBuilder

__all__ = [
    "EtlLogger",
    "EtlBatch", "EtlRecord", "EtlError", "init_etl_db",
    "ValidatorRegistry", "ValidationResult", "BaseValidator",
    "NotNullValidator", "RangeValidator", "RegexValidator",
    "ChoiceValidator", "ConditionalValidator",
    "BaseDedupStrategy", "DedupResult", "ByIdStrategy",
    "ByCoordinateStrategy", "ByHighwayChainageStrategy",
    "CompositeStrategy", "FreshnessResolver",
    "BaseImporter", "BaseAccidentImporter",
    "MoRTHBlackSpotImporter",
    "AccidentRecordImporter",
    "RoadSegmentRiskBuilder",
]
