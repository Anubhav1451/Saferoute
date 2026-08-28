"""
Risk Computation Engine for SafeRoute AI.
Orchestrates the collection, normalization, and aggregation of risk features
to produce normalized edge risk metadata (without routing penalties or pathfinding).
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .risk_models import FeatureAttachment
from .risk_normalizer import RiskNormalizer
from .risk_weights import RiskWeightConfig, load_risk_weights_from_config
from ..db.models import GraphEdge, RoadSegmentRisk
from .risk_repository import FeatureAttachmentRepository
from ..graph.chainage import (
    project_point_to_nearest_edge,
    get_chainage_from_coordinates,
    get_coordinates_from_chainage
)
from ..graph.projection import haversine_distance


class RiskComputationEngine:
    """
    Main engine for computing risk metadata from feature attachments.
    Orchestrates the pipeline: feature collection → normalization → aggregation → metadata output.
    Does NOT compute routing penalties or perform pathfinding (as per requirements).
    """

    def __init__(
        self,
        session: Session,
        weight_config: Optional[RiskWeightConfig] = None,
        normalizer: Optional[RiskNormalizer] = None
    ):
        """
        Initialize the risk computation engine.

        Args:
            session: SQLAlchemy database session
            weight_config: Configuration for weighting factors (loads from config if None)
            normalizer: RiskNormalizer instance (creates default if None)
        """
        self.session = session
        self.weight_config = weight_config or load_risk_weights_from_config()
        self.normalizer = normalizer or RiskNormalizer(self.weight_config)
        self.attachment_repo = FeatureAttachmentRepository(session)

    def compute_edge_risk_metadata(
        self,
        edge_id: int,
        reference_time: Optional[datetime] = None,
        feature_types: Optional[List[str]] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Compute normalized risk metadata for a single graph edge.
        Does NOT compute routing penalties or perform pathfinding.

        Args:
            edge_id: The ID of the graph edge to process
            reference_time: Reference time for temporal calculations (defaults to now)
            feature_types: Optional list of feature types to include (None = all)
            active_only: If True, consider only active attachments

        Returns:
            Dictionary containing normalized edge risk metadata suitable for
            storage in RoadSegmentRisk model (but does not persist it)
        """
        if reference_time is None:
            reference_time = datetime.utcnow()

        # Get the graph edge to verify it exists and get spatial properties
        edge = self.session.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
        if not edge:
            raise ValueError(f"GraphEdge with id {edge_id} not found")

        # Get attachments for this edge
        attachments = self.attachment_repo.get_by_edge_id(
            edge_id, active_only=active_only
        )

        # Filter by feature types if specified
        if feature_types:
            attachments = [
                att for att in attachments
                if att.feature_type in feature_types
            ]

        # If no attachments, return baseline metadata
        if not attachments:
            return self._get_baseline_metadata(edge, reference_time)

        # Normalize all features
        normalized_features = self.normalizer.normalize_feature_batch(
            attachments, reference_time
        )

        # Calculate feature weights
        weighted_features = []
        for feature, normalized in zip(attachments, normalized_features):
            weight = self.normalizer.get_feature_weight(feature, normalized)
            weighted_features.append({
                'feature': feature,
                'normalized': normalized,
                'weight': weight
            })

        # Aggregate the weighted features into edge metadata
        metadata = self._aggregate_weighted_features(
            edge, weighted_features, reference_time
        )

        return metadata

    def compute_batch_edge_risk_metadata(
        self,
        edge_ids: List[int],
        reference_time: Optional[datetime] = None,
        feature_types: Optional[List[str]] = None,
        active_only: bool = True,
        batch_size: int = 100
    ) -> Dict[int, Dict[str, Any]]:
        """
        Compute risk metadata for multiple edges in batches.

        Args:
            edge_ids: List of graph edge IDs to process
            reference_time: Reference time for temporal calculations
            feature_types: Optional list of feature types to include
            active_only: If True, consider only active attachments
            batch_size: Number of edges to process in each batch

        Returns:
            Dictionary mapping edge_id to its risk metadata
        """
        if reference_time is None:
            reference_time = datetime.utcnow()

        result = {}

        # Process in batches for efficiency
        for i in range(0, len(edge_ids), batch_size):
            batch = edge_ids[i:i + batch_size]
            batch_results = self._compute_edge_batch(
                batch, reference_time, feature_types, active_only
            )
            result.update(batch_results)

        return result

    def _compute_edge_batch(
        self,
        edge_ids: List[int],
        reference_time: datetime,
        feature_types: Optional[List[str]],
        active_only: bool
    ) -> Dict[int, Dict[str, Any]]:
        """Compute risk metadata for a batch of edges."""
        result = {}

        # Get all edges in this batch
        edges = self.session.query(GraphEdge).filter(
            GraphEdge.id.in_(edge_ids)
        ).all()
        edge_dict = {edge.id: edge for edge in edges}

        # Get all attachments for these edges in one query
        attachments_query = self.session.query(FeatureAttachment).filter(
            FeatureAttachment.edge_id.in_(edge_ids)
        )
        if active_only:
            attachments_query = attachments_query.filter(
                FeatureAttachment.is_active == True
            )
        if feature_types:
            attachments_query = attachments_query.filter(
                FeatureAttachment.feature_type.in_(feature_types)
            )

        attachments = attachments_query.all()

        # Group attachments by edge_id
        attachments_by_edge = {}
        for att in attachments:
            if att.edge_id not in attachments_by_edge:
                attachments_by_edge[att.edge_id] = []
            attachments_by_edge[att.edge_id].append(att)

        # Process each edge
        for edge_id in edge_ids:
            edge = edge_dict.get(edge_id)
            if not edge:
                # Edge not found, skip
                continue

            attachments_for_edge = attachments_by_edge.get(edge_id, [])

            if not attachments_for_edge:
                result[edge_id] = self._get_baseline_metadata(edge, reference_time)
                continue

            # Normalize features
            normalized_features = self.normalizer.normalize_feature_batch(
                attachments_for_edge, reference_time
            )

            # Calculate weights
            weighted_features = []
            for feature, normalized in zip(attachments_for_edge, normalized_features):
                weight = self.normalizer.get_feature_weight(feature, normalized)
                weighted_features.append({
                    'feature': feature,
                    'normalized': normalized,
                    'weight': weight
                })

            # Aggregate into metadata
            result[edge_id] = self._aggregate_weighted_features(
                edge, weighted_features, reference_time
            )

        return result

    def _get_baseline_metadata(self, edge: GraphEdge, reference_time: datetime) -> Dict[str, Any]:
        """
        Get baseline metadata for an edge with no attachments.

        Args:
            edge: The GraphEdge object
            reference_time: Reference time for temporal calculations

        Returns:
            Baseline metadata dictionary
        """
        return {
            'edge_id': edge.id,
            'edge_properties': {
                'length': edge.length,
                'highway': edge.highway,
                'road_class': edge.road_class,
                'maxspeed': edge.maxspeed,
                'travel_time': edge.travel_time,
                'direction': edge.direction,
                'mid_lat': edge.mid_lat,
                'mid_lon': edge.mid_lon,
                'bbox': {
                    'min_lat': edge.bbox_min_lat,
                    'min_lon': edge.bbox_min_lon,
                    'max_lat': edge.bbox_max_lat,
                    'max_lon': edge.bbox_max_lon
                } if all(v is not None for v in [edge.bbox_min_lat, edge.bbox_min_lon, edge.bbox_max_lat, edge.bbox_max_lon]) else None
            },
            'feature_counts': {
                'total': 0,
                'by_type': {},
                'by_source': {}
            },
            'temporal_info': {
                'feature_count': 0,
                'date_range': None,
                'newest_feature_age_hours': None,
                'oldest_feature_age_hours': None
            },
            'aggregated_weights': {
                'total_weight': 0.0,
                'weight_by_type': {},
                'weight_by_source': {},
                'average_weight': 0.0,
                'max_weight': 0.0
            },
            'feature_types_present': [],
            'sources_present': [],
            'has_features': False,
            'computation_metadata': {
                'computed_at': reference_time.isoformat(),
                'reference_time': reference_time.isoformat(),
                'weight_config_used': self.weight_config.dict()
            }
        }

    def _aggregate_weighted_features(
        self,
        edge: GraphEdge,
        weighted_features: List[Dict[str, Any]],
        reference_time: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate weighted features into edge metadata.

        Args:
            edge: The GraphEdge object
            weighted_features: List of dicts containing feature, normalized data, and weight
            reference_time: Reference time for temporal calculations

        Returns:
            Aggregated metadata dictionary
        """
        # Initialize aggregations
        total_weight = 0.0
        weight_by_type = {}
        weight_by_source = {}
        weights_list = []

        type_counts = {}
        source_counts = {}

        # For temporal analysis
        feature_timestamps = []
        feature_ages_hours = []

        # For feature type and source tracking
        feature_types_present = set()
        sources_present = set()

        # Process each weighted feature
        for wf in weighted_features:
            feature = wf['feature']
            normalized = wf['normalized']
            weight = wf['weight']

            # Accumulate weights
            total_weight += weight
            weights_list.append(weight)

            # By type
            ftype = feature.feature_type
            weight_by_type[ftype] = weight_by_type.get(ftype, 0.0) + weight
            type_counts[ftype] = type_counts.get(ftype, 0) + 1
            feature_types_present.add(ftype)

            # By source
            source = feature.source or 'unknown'
            weight_by_source[source] = weight_by_source.get(source, 0.0) + weight
            source_counts[source] = source_counts.get(source, 0) + 1
            sources_present.add(source)

            # Temporal data
            feature_time = feature.updated_at or feature.created_at
            if feature_time:
                feature_timestamps.append(feature_time)
                age_hours = (reference_time - feature_time).total_seconds() / 3600
                feature_ages_hours.append(max(0, age_hours))  # Ensure non-negative

        # Calculate temporal statistics
        date_range = None
        newest_feature_age_hours = None
        oldest_feature_age_hours = None

        if feature_timestamps:
            min_time = min(feature_timestamps)
            max_time = max(feature_timestamps)
            date_range = {
                'start': min_time.isoformat(),
                'end': max_time.isoformat()
            }
            newest_feature_age_hours = min(feature_ages_hours) if feature_ages_hours else None
            oldest_feature_age_hours = max(feature_ages_hours) if feature_ages_hours else None

        # Prepare the metadata dictionary
        metadata = {
            'edge_id': edge.id,
            'edge_properties': {
                'length': edge.length,
                'highway': edge.highway,
                'road_class': edge.road_class,
                'maxspeed': edge.maxspeed,
                'travel_time': edge.travel_time,
                'direction': edge.direction,
                'mid_lat': edge.mid_lat,
                'mid_lon': edge.mid_lon,
                'bbox': {
                    'min_lat': edge.bbox_min_lat,
                    'min_lon': edge.bbox_min_lon,
                    'max_lat': edge.bbox_max_lat,
                    'max_lon': edge.bbox_max_lon
                } if all(v is not None for v in [edge.bbox_min_lat, edge.bbox_min_lon, edge.bbox_max_lat, edge.bbox_max_lon]) else None
            },
            'feature_counts': {
                'total': len(weighted_features),
                'by_type': type_counts,
                'by_source': source_counts
            },
            'temporal_info': {
                'feature_count': len(feature_timestamps),
                'date_range': date_range,
                'newest_feature_age_hours': newest_feature_age_hours,
                'oldest_feature_age_hours': oldest_feature_age_hours
            },
            'aggregated_weights': {
                'total_weight': total_weight,
                'weight_by_type': weight_by_type,
                'weight_by_source': weight_by_source,
                'average_weight': total_weight / len(weighted_features) if weighted_features else 0.0,
                'max_weight': max(weights_list) if weights_list else 0.0,
                'weight_sum_by_type': weight_by_type,  # Duplicate for clarity in some contexts
                'weight_sum_by_source': weight_by_source
            },
            'feature_types_present': sorted(list(feature_types_present)),
            'sources_present': sorted(list(sources_present)),
            'has_features': len(weighted_features) > 0,
            'computation_metadata': {
                'computed_at': datetime.utcnow().isoformat(),
                'reference_time': reference_time.isoformat(),
                'weight_config_used': self.weight_config.dict(),
                'normalization_applied': True
            }
        }

        return metadata

    def persist_edge_risk_metadata(
        self,
        edge_id: int,
        metadata: Dict[str, Any],
        commit: bool = True
    ) -> Optional[RoadSegmentRisk]:
        """
        Persist computed risk metadata to the RoadSegmentRisk table.
        Note: This stores metadata ONLY, not risk scores for routing (per requirements).

        Args:
            edge_id: The ID of the graph edge
            metadata: The computed risk metadata dictionary
            commit: Whether to commit the transaction immediately

        Returns:
            The created RoadSegmentRisk instance or None if failed
        """
        try:
            # Get the edge to verify it exists and get spatial data
            edge = self.session.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
            if not edge:
                raise ValueError(f"GraphEdge with id {edge_id} not found")

            # Create or update RoadSegmentRisk record
            risk_record = self.session.query(RoadSegmentRisk).filter(
                RoadSegmentRisk.id == edge_id  # Assuming we might link by edge_id in future
            ).first()

            # For now, we'll create a new record. In a full implementation,
            # we might want to link this to the edge_id via a foreign key.
            # But based on the existing RoadSegmentRisk model, it doesn't have an edge_id FK.
            # So we'll store the metadata in the available fields and note the edge_id in computation metadata.

            # Extract relevant data for RoadSegmentRisk fields (metadata only, no risk scores)
            # Note: RoadSegmentRisk currently seems focused on accident-specific data.
            # We'll store our metadata in the available text/numeric fields appropriately.

            risk_record = RoadSegmentRisk(
                start_latitude=edge.mid_lat if edge.mid_lat is not None else 0.0,
                start_longitude=edge.mid_lon if edge.mid_lon is not None else 0.0,
                end_latitude=edge.mid_lat if edge.mid_lat is not None else 0.0,  # Simplified - would need actual end coords
                end_longitude=edge.mid_lon if edge.mid_lon is not None else 0.0,
                road_name=edge.highway,  # Using highway as road name approximation
                segment_length_m=edge.length,
                risk_score=0.0,  # Set to 0.0 as per requirements - we do NOT compute risk scores for routing
                accident_frequency=float(len(
                    [f for f in metadata.get('feature_counts', {}).get('by_type', {}).keys()
                     if f in ['accident', 'crash', 'collision']]
                )) if metadata.get('feature_counts', {}).get('by_type') else 0.0,
                severity_distribution=str(metadata.get('aggregated_weights', {}).get('weight_by_type', {})),
                record_count=metadata.get('feature_counts', {}).get('total', 0),
                last_accident_date=None,  # Would need to extract from temporal info if available
                data_source=f"RiskComputationEngine_{len(metadata.get('sources_present', []))}_sources",
                computed_at=datetime.utcnow(),
                # Store additional metadata in available fields
                highway_number=str(metadata.get('edge_properties', {}).get('highway', 'unknown')),
                road_class=metadata.get('edge_properties', {}).get('road_class'),
                # Note: These fields don't exist in the current model, so we'll skip them for now
                # exposure_factor, accident_density, fatality_weight, blackspot_weight, confidence_score, last_updated
            )

            self.session.add(risk_record)
            self.session.flush()

            if commit:
                self.session.commit()

            return risk_record

        except Exception as e:
            self.session.rollback()
            raise e

    def compute_and_persist_edge_risk(
        self,
        edge_id: int,
        reference_time: Optional[datetime] = None,
        feature_types: Optional[List[str]] = None,
        active_only: bool = True,
        commit: bool = True
    ) -> Optional[RoadSegmentRisk]:
        """
        Convenience method that computes risk metadata and persists it in one operation.

        Args:
            edge_id: The ID of the graph edge to process
            reference_time: Reference time for temporal calculations
            feature_types: Optional list of feature types to include
            active_only: If True, consider only active attachments
            commit: Whether to commit the transaction immediately

        Returns:
            The created RoadSegmentRisk instance or None if failed
        """
        metadata = self.compute_edge_risk_metadata(
            edge_id, reference_time, feature_types, active_only
        )
        return self.persist_edge_risk_metadata(edge_id, metadata, commit)

    def compute_and_persist_batch_edge_risk(
        self,
        edge_ids: List[int],
        reference_time: Optional[datetime] = None,
        feature_types: Optional[List[str]] = None,
        active_only: bool = True,
        commit: bool = True,
        batch_size: int = 100
    ) -> Dict[int, Optional[RoadSegmentRisk]]:
        """
        Compute and persist risk metadata for multiple edges.

        Args:
            edge_ids: List of graph edge IDs to process
            reference_time: Reference time for temporal calculations
            feature_types: Optional list of feature types to include
            active_only: If True, consider only active attachments
            commit: Whether to commit the transaction immediately
            batch_size: Number of edges to process in each batch

        Returns:
            Dictionary mapping edge_id to its RoadSegmentRisk instance (or None if failed)
        """
        metadata_dict = self.compute_batch_edge_risk_metadata(
            edge_ids, reference_time, feature_types, active_only, batch_size
        )

        results = {}
        for edge_id, metadata in metadata_dict.items():
            try:
                risk_record = self.persist_edge_risk_metadata(
                    edge_id, metadata, commit=False  # Delay commit until the end
                )
                results[edge_id] = risk_record
            except Exception:
                results[edge_id] = None
                # Continue processing other edges even if one fails

        if commit:
            self.session.commit()

        return results