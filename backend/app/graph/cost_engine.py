"""
Route Cost Engine for SafeRoute AI.
Calculates traversal costs for graph edges based on multiple factors.
Does NOT perform pathfinding or graph traversal - only computes edge-level costs.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..db.models import GraphEdge, GraphNode, RoadSegmentRisk, TrafficFlow, TrafficIncident, RoadClosure, ConstructionZone
from .cost_config import CostWeightConfig, load_cost_config_from_app
from .cost_models import CostComponents, EdgeCostOutput


class RouteCostEngine:
    """
    Engine for calculating traversal costs for individual graph edges.
    Computes cost components: distance, risk, elevation, road class, surface, turn, weather, traffic.
    Does NOT perform pathfinding or graph traversal (as per requirements).
    """

    def __init__(
        self,
        session: Session,
        cost_config: Optional[CostWeightConfig] = None
    ):
        """
        Initialize the route cost engine.

        Args:
            session: SQLAlchemy database session
            cost_config: Configuration for cost weights (loads from app config if None)
        """
        self.session = session
        self.cost_config = cost_config or load_cost_config_from_app()
        # Per-instance memoization of computed edge costs. A single route
        # request evaluates the same edge many times (A* explores both
        # endpoints of an edge, and find_safest_route runs two searches).
        # Within one request the underlying data is read-only, so cached
        # results are identical to a recomputation. The engine is created
        # per request (SafetyRoutingService), so the cache is request-scoped.
        self._cost_cache: dict[int, EdgeCostOutput] = {}
        # Lazy caches for data that is constant for the lifetime of one
        # engine instance (one route request). Active road closures and
        # construction zones do not depend on edge_id, so the same rows
        # are loaded for every edge cost computation - fetch once.
        self._active_closures: Optional[list] = None
        self._active_construction: Optional[list] = None
        # Set to True once we confirm none of the traffic tables have any
        # rows. When all traffic tables are empty, every edge has zero
        # traffic cost, so per-edge traffic queries can be skipped entirely.
        self._traffic_tables_empty: Optional[bool] = None

    def clear_cost_cache(self) -> None:
        """Clear the per-instance edge cost cache."""
        self._cost_cache.clear()
        self._active_closures = None
        self._active_construction = None
        self._traffic_tables_empty = None

    def compute_edge_cost(self, edge_id: int) -> EdgeCostOutput:
        """
        Compute the total traversal cost for a single graph edge.
        Returns ONLY cost components - no pathfinding or routing decisions.

        Args:
            edge_id: The ID of the graph edge to process

        Returns:
            EdgeCostOutput containing all cost components
        """
        # Return memoized cost if this edge was already computed in this
        # engine instance. The single-path cost semantics are preserved
        # exactly - this is pure memoization, not a different calculation.
        cached = self._cost_cache.get(edge_id)
        if cached is not None:
            return cached

        # Get the graph edge. Use Session.get() so an edge already loaded
        # into this session's identity map (e.g. by _get_neighbors) is
        # returned without re-issuing a SELECT.
        edge = self.session.get(GraphEdge, edge_id)
        if not edge:
            raise ValueError(f"GraphEdge with id {edge_id} not found")

        # Get risk metadata for this edge (if available)
        risk_data = self._get_edge_risk_data(edge_id)

        # Get traffic data for this edge (reuse the already-loaded edge
        # object to avoid a redundant GraphEdge SELECT).
        traffic_data = self._get_edge_traffic_data(edge_id, edge=edge)

        # Calculate individual cost components
        components = self._calculate_cost_components(edge, risk_data, traffic_data)

        # Create and return the output object
        output = EdgeCostOutput(
            distance_cost=components.distance,
            risk_cost=components.risk,
            elevation_cost=components.elevation,
            road_class_cost=components.road_class,
            surface_cost=components.surface,
            turn_cost=components.turn,  # Placeholder
            weather_cost=components.weather,  # Placeholder
            traffic_cost=components.traffic,  # NEW: Traffic cost
            total_cost=components.total(),
            edge_id=edge.id,
            computation_timestamp=datetime.utcnow()
        )
        self._cost_cache[edge_id] = output
        return output

    def compute_batch_edge_costs(
        self,
        edge_ids: list[int],
        batch_size: int = 100
    ) -> dict[int, EdgeCostOutput]:
        """
        Compute costs for multiple edges in batches.

        Args:
            edge_ids: List of graph edge IDs to process
            batch_size: Number of edges to process in each batch

        Returns:
            Dictionary mapping edge_id to its EdgeCostOutput
        """
        result = {}

        # Process in batches for efficiency
        for i in range(0, len(edge_ids), batch_size):
            batch = edge_ids[i:i + batch_size]
            batch_results = self._compute_edge_cost_batch(batch)
            result.update(batch_results)

        return result

    def _compute_edge_cost_batch(self, edge_ids: list[int]) -> dict[int, EdgeCostOutput]:
        """Compute costs for a batch of edges."""
        result = {}

        # Get all edges in this batch
        edges = self.session.query(GraphEdge).filter(
            GraphEdge.id.in_(edge_ids)
        ).all()
        edge_dict = {edge.id: edge for edge in edges}

        # Get risk data for all edges in this batch
        risk_data_dict = self._get_batch_risk_data(edge_ids)

        # Get traffic data for all edges in this batch
        traffic_data_dict = self._get_batch_traffic_data(edge_ids)

        # Process each edge
        for edge_id in edge_ids:
            edge = edge_dict.get(edge_id)
            if not edge:
                # Skip missing edges
                continue

            risk_data = risk_data_dict.get(edge_id)
            traffic_data = traffic_data_dict.get(edge_id)
            components = self._calculate_cost_components(edge, risk_data, traffic_data)

            result[edge_id] = EdgeCostOutput(
                distance_cost=components.distance,
                risk_cost=components.risk,
                elevation_cost=components.elevation,
                road_class_cost=components.road_class,
                surface_cost=components.surface,
                turn_cost=components.turn,  # Placeholder
                weather_cost=components.weather,  # Placeholder
                traffic_cost=components.traffic,
                total_cost=components.total(),
                edge_id=edge.id,
                computation_timestamp=datetime.utcnow()
            )

        return result

    def _get_edge_traffic_data(self, edge_id: int, edge: Optional[GraphEdge] = None) -> Optional[dict]:
        """
        Retrieve traffic metadata for a specific edge.

        Args:
            edge_id: The ID of the graph edge
            edge: The already-loaded GraphEdge object (avoids a redundant
                SELECT). If None, the edge is fetched from the session.

        Returns:
            Dictionary containing traffic data or None if not found
        """
        now = datetime.utcnow()

        # If none of the traffic tables contain any rows, then every edge
        # has no flow/incident/closure/construction data and traffic cost is
        # zero. Check once per engine instance and skip the per-edge traffic
        # queries entirely. (When tables are non-empty, this is skipped and
        # behavior is unchanged.)
        if self._traffic_tables_empty is None:
            self._traffic_tables_empty = all(
                self.session.query(model_cls).first() is None
                for model_cls in (TrafficFlow, TrafficIncident, RoadClosure, ConstructionZone)
            )
        if self._traffic_tables_empty:
            return None

        # Get the edge to access its node coordinates (reuse if provided)
        if edge is None:
            edge = self.session.query(GraphEdge).filter(GraphEdge.id == edge_id).first()
        if not edge:
            return None

        # 1. Get latest traffic flow for this edge
        flow = self.session.query(TrafficFlow).filter(
            TrafficFlow.edge_id == edge_id,
            (TrafficFlow.expires_at.is_(None)) | (TrafficFlow.expires_at > now)
        ).order_by(TrafficFlow.measured_at.desc()).first()

        # 2. Get active incidents near this edge (using proximity to edge geometry)
        # Since TrafficIncident doesn't have edge_id, we query by lat/lon proximity
        # We'll need the edge's source/dest node coordinates for this
        edge_nodes = self.session.query(GraphNode).filter(
            GraphNode.id.in_([edge.source_node_id, edge.dest_node_id])
        ).all()
        if edge_nodes:
            # Get mid-point of edge for proximity query
            lats = [n.latitude for n in edge_nodes if n.latitude is not None]
            lons = [n.longitude for n in edge_nodes if n.longitude is not None]
            if lats and lons:
                mid_lat = sum(lats) / len(lats)
                mid_lon = sum(lons) / len(lons)
                # Query incidents within ~500m of edge midpoint
                deg_per_m = 1 / 111000
                delta = 500 * deg_per_m
                incidents = self.session.query(TrafficIncident).filter(
                    TrafficIncident.latitude.between(mid_lat - delta, mid_lat + delta),
                    TrafficIncident.longitude.between(mid_lon - delta, mid_lon + delta),
                    (TrafficIncident.cleared_at.is_(None)) | (TrafficIncident.cleared_at > now),
                    (TrafficIncident.expires_at.is_(None)) | (TrafficIncident.expires_at > now)
                ).all()
            else:
                incidents = []
        else:
            incidents = []

        # 3. Get active closures affecting this edge.
        # RoadClosure has affected_edges as JSON array. The active-closures
        # set is identical for every edge in this request, so fetch it once
        # per engine instance and reuse it.
        import json
        if self._active_closures is None:
            self._active_closures = self.session.query(RoadClosure).filter(
                RoadClosure.starts_at <= now,
                (RoadClosure.ends_at.is_(None)) | (RoadClosure.ends_at > now)
            ).all()
        closures = self._active_closures
        # Filter by affected_edges in Python since it's JSON
        closure_list = []
        for clo in closures:
            try:
                affected = json.loads(clo.affected_edges) if clo.affected_edges else []
                if edge_id in affected:
                    closure_list.append(clo)
            except:
                pass

        # 4. Get active construction zones affecting this edge.
        # Same caching rationale as closures.
        if self._active_construction is None:
            self._active_construction = self.session.query(ConstructionZone).filter(
                (ConstructionZone.actual_end.is_(None)) | (ConstructionZone.actual_end > now),
                or_(
                    ConstructionZone.planned_end.is_(None),
                    ConstructionZone.planned_end > now
                )
            ).all()
        construction = self._active_construction
        construction_list = []
        for con in construction:
            try:
                affected = json.loads(con.affected_edges) if con.affected_edges else []
                if edge_id in affected:
                    construction_list.append(con)
            except:
                # Fallback: check proximity to construction zone
                if con.start_latitude and con.start_longitude and edge_nodes:
                    mid_lat = sum(n.latitude for n in edge_nodes if n.latitude) / max(1, sum(1 for n in edge_nodes if n.latitude))
                    mid_lon = sum(n.longitude for n in edge_nodes if n.longitude) / max(1, sum(1 for n in edge_nodes if n.longitude))
                    deg_per_m = 1 / 111000
                    delta = 1000 * deg_per_m  # 1km radius
                    if (con.start_latitude and con.start_longitude and
                        mid_lat and mid_lon and
                        abs(con.start_latitude - mid_lat) < delta and
                        abs(con.start_longitude - mid_lon) < delta):
                        construction_list.append(con)

        if not flow and not incidents and not closure_list and not construction_list:
            return None

        # Build traffic data dict
        flow_data = None
        if flow:
            flow_data = {
                'speed_kmh': flow.speed_kmh,
                'free_flow_speed_kmh': flow.free_flow_speed_kmh,
                'congestion_level': flow.congestion_level,
                'jam_factor': flow.jam_factor,
                'travel_time_seconds': flow.travel_time_seconds,
                'free_flow_travel_time_seconds': flow.free_flow_travel_time_seconds,
                'delay_seconds': flow.delay_seconds,
                # Congestion ratio as free_flow_speed / current_speed (unclamped,
                # >1.0 = congestion, 1.0 = free flow). Same units as the batch
                # path and as _calculate_traffic_cost's congestion branch expects.
                # The model's congestion_ratio property (speed/free_flow, clamped
                # to <=1.0) is the inverse and would make that branch dead code.
                'congestion_ratio': (flow.free_flow_speed_kmh / flow.speed_kmh)
                    if flow.speed_kmh and flow.free_flow_speed_kmh and flow.speed_kmh > 0 else None,
                'delay_factor': flow.delay_factor,
                'confidence': flow.confidence,
                'measured_at': flow.measured_at
            }

        incidents_data = []
        for inc in incidents:
            incidents_data.append({
                'incident_type': inc.incident_type,
                'severity': inc.severity,
                'delay_minutes': inc.delay_minutes,
                'lanes_affected': inc.lanes_affected,
                'total_lanes': inc.total_lanes,
                'closure_type': inc.closure_type,
                'confidence': inc.confidence
            })

        closures_data = []
        for clo in closure_list:
            closures_data.append({
                'closure_type': clo.closure_type,
                'direction': clo.direction,
                'lanes_closed': clo.lanes_closed,
                'total_lanes': clo.total_lanes,
                'confidence': clo.confidence
            })

        construction_data = []
        for con in construction_list:
            construction_data.append({
                'zone_type': con.zone_type,
                'impact_level': con.impact_level,
                'lanes_affected': con.lanes_affected,
                'lanes_remaining': con.lanes_remaining,
                'contraflow': con.contraflow,
                'speed_limit_kmh': con.speed_limit_kmh,
                'confidence': con.confidence
            })

        return {
            'flow': flow_data,
            'incidents': incidents_data,
            'closures': closures_data,
            'construction': construction_data
        }

    def _get_batch_traffic_data(self, edge_ids: list[int]) -> dict[int, dict]:
        """
        Retrieve traffic metadata for multiple edges efficiently.

        Args:
            edge_ids: List of graph edge IDs

        Returns:
            Dictionary mapping edge_id to traffic data
        """
        if not edge_ids:
            return {}

        now = datetime.utcnow()

        # 1. Get latest flow for all edges
        flow_subq = self.session.query(
            TrafficFlow.edge_id,
            TrafficFlow.speed_kmh,
            TrafficFlow.free_flow_speed_kmh,
            TrafficFlow.congestion_level,
            TrafficFlow.jam_factor,
            TrafficFlow.travel_time_seconds,
            TrafficFlow.free_flow_travel_time_seconds,
            TrafficFlow.delay_seconds,
            TrafficFlow.confidence,
            TrafficFlow.measured_at
        ).filter(
            TrafficFlow.edge_id.in_(edge_ids),
            (TrafficFlow.expires_at.is_(None)) | (TrafficFlow.expires_at > now)
        ).order_by(
            TrafficFlow.edge_id,
            TrafficFlow.measured_at.desc()
        ).distinct(TrafficFlow.edge_id).all()

        flows = {}
        for f in flow_subq:
            flows[f.edge_id] = {
                'speed_kmh': f.speed_kmh,
                'free_flow_speed_kmh': f.free_flow_speed_kmh,
                'congestion_level': f.congestion_level,
                'jam_factor': f.jam_factor,
                'travel_time_seconds': f.travel_time_seconds,
                'free_flow_travel_time_seconds': f.free_flow_travel_time_seconds,
                'delay_seconds': f.delay_seconds,
                'congestion_ratio': (f.free_flow_speed_kmh / f.speed_kmh) if f.speed_kmh and f.free_flow_speed_kmh and f.speed_kmh > 0 else None,
                'delay_factor': (f.travel_time_seconds / f.free_flow_travel_time_seconds) if f.travel_time_seconds and f.free_flow_travel_time_seconds and f.free_flow_travel_time_seconds > 0 else None,
                'confidence': f.confidence,
                'measured_at': f.measured_at
            }

        # 2. Get all edges to check proximity for incidents/construction
        edges = self.session.query(GraphEdge).filter(GraphEdge.id.in_(edge_ids)).all()
        edge_nodes_map = {}
        for edge in edges:
            nodes = self.session.query(GraphNode).filter(
                GraphNode.id.in_([edge.source_node_id, edge.dest_node_id])
            ).all()
            if nodes:
                lats = [n.latitude for n in nodes if n.latitude is not None]
                lons = [n.longitude for n in nodes if n.longitude is not None]
                if lats and lons:
                    edge_nodes_map[edge.id] = (sum(lats)/len(lats), sum(lons)/len(lons))

        # 3. Get incidents near edges
        # We'll query by proximity to edge midpoints
        incidents_by_edge = {}
        if edge_nodes_map:
            # Get all incidents that are active
            all_incidents = self.session.query(TrafficIncident).filter(
                (TrafficIncident.cleared_at.is_(None)) | (TrafficIncident.cleared_at > now),
                (TrafficIncident.expires_at.is_(None)) | (TrafficIncident.expires_at > now)
            ).all()

            for inc in all_incidents:
                # Check proximity to each edge midpoint
                deg_per_m = 1 / 111000
                delta = 500 * deg_per_m  # 500m radius
                for edge_id, (mid_lat, mid_lon) in edge_nodes_map.items():
                    if (mid_lat - delta <= inc.latitude <= mid_lat + delta and
                        mid_lon - delta <= inc.longitude <= mid_lon + delta):
                        if edge_id not in incidents_by_edge:
                            incidents_by_edge[edge_id] = []
                        incidents_by_edge[edge_id].append({
                            'incident_type': inc.incident_type,
                            'severity': inc.severity,
                            'delay_minutes': inc.delay_minutes,
                            'lanes_affected': inc.lanes_affected,
                            'total_lanes': inc.total_lanes,
                            'closure_type': inc.closure_type,
                            'confidence': inc.confidence
                        })

        # 4. Get closures
        import json
        closures = self.session.query(RoadClosure).filter(
            RoadClosure.starts_at <= now,
            (RoadClosure.ends_at.is_(None)) | (RoadClosure.ends_at > now)
        ).all()

        closures_by_edge = {}
        for clo in closures:
            try:
                affected = json.loads(clo.affected_edges) if clo.affected_edges else []
                for eid in affected:
                    if eid in edge_ids:
                        if eid not in closures_by_edge:
                            closures_by_edge[eid] = []
                        closures_by_edge[eid].append({
                            'closure_type': clo.closure_type,
                            'direction': clo.direction,
                            'lanes_closed': clo.lanes_closed,
                            'total_lanes': clo.total_lanes,
                            'confidence': clo.confidence
                        })
            except:
                pass

        # 5. Get construction zones
        construction_zones = self.session.query(ConstructionZone).filter(
            (ConstructionZone.actual_end.is_(None)) | (ConstructionZone.actual_end > now),
            or_(
                ConstructionZone.planned_end.is_(None),
                ConstructionZone.planned_end > now
            )
        ).all()

        construction_by_edge = {}
        for con in construction_zones:
            try:
                affected = json.loads(con.affected_edges) if con.affected_edges else []
                for eid in affected:
                    if eid in edge_ids:
                        if eid not in construction_by_edge:
                            construction_by_edge[eid] = []
                        construction_by_edge[eid].append({
                            'zone_type': con.zone_type,
                            'impact_level': con.impact_level,
                            'lanes_affected': con.lanes_affected,
                            'lanes_remaining': con.lanes_remaining,
                            'contraflow': con.contraflow,
                            'speed_limit_kmh': con.speed_limit_kmh,
                            'confidence': con.confidence
                        })
            except:
                # Fallback: check proximity
                if con.start_latitude and con.start_longitude:
                    for edge_id, (mid_lat, mid_lon) in edge_nodes_map.items():
                        deg_per_m = 1 / 111000
                        delta = 1000 * deg_per_m  # 1km
                        if (abs(con.start_latitude - mid_lat) < delta and
                            abs(con.start_longitude - mid_lon) < delta):
                            if edge_id not in construction_by_edge:
                                construction_by_edge[edge_id] = []
                            construction_by_edge[edge_id].append({
                                'zone_type': con.zone_type,
                                'impact_level': con.impact_level,
                                'lanes_affected': con.lanes_affected,
                                'lanes_remaining': con.lanes_remaining,
                                'contraflow': con.contraflow,
                                'speed_limit_kmh': con.speed_limit_kmh,
                                'confidence': con.confidence
                            })

        # Build result dict
        result = {}
        for edge_id in edge_ids:
            flow = flows.get(edge_id)
            incs = incidents_by_edge.get(edge_id, [])
            cls = closures_by_edge.get(edge_id, [])
            cons = construction_by_edge.get(edge_id, [])

            if not flow and not incs and not cls and not cons:
                continue

            flow_data = None
            if flow:
                flow_data = {
                    'speed_kmh': flow['speed_kmh'],
                    'free_flow_speed_kmh': flow['free_flow_speed_kmh'],
                    'congestion_level': flow['congestion_level'],
                    'jam_factor': flow['jam_factor'],
                    'travel_time_seconds': flow['travel_time_seconds'],
                    'free_flow_travel_time_seconds': flow['free_flow_travel_time_seconds'],
                    'delay_seconds': flow['delay_seconds'],
                    'congestion_ratio': flow['congestion_ratio'],
                    'delay_factor': flow['delay_factor'],
                    'confidence': flow['confidence'],
                    'measured_at': flow['measured_at']
                }

            incidents_data = incs
            closures_data = cls
            construction_data = cons

            result[edge_id] = {
                'flow': flow_data,
                'incidents': incidents_data,
                'closures': closures_data,
                'construction': construction_data
            }

        return result

    def _get_edge_risk_data(self, edge_id: int) -> Optional[dict]:
        """
        Retrieve risk metadata for a specific edge.

        Args:
            edge_id: The ID of the graph edge

        Returns:
            Dictionary containing risk data or None if not found
        """
        risk_record = self.session.get(RoadSegmentRisk, edge_id)

        if not risk_record:
            return None

        # Extract relevant risk data
        return {
            'risk_score': risk_record.risk_score,
            'accident_frequency': risk_record.accident_frequency,
            'severity_distribution': risk_record.severity_distribution,
            'record_count': risk_record.record_count,
            'data_source': risk_record.data_source
        }

    def _get_batch_risk_data(self, edge_ids: list[int]) -> dict[int, dict]:
        """
        Retrieve risk metadata for multiple edges.

        Args:
            edge_ids: List of graph edge IDs

        Returns:
            Dictionary mapping edge_id to its risk data
        """
        if not edge_ids:
            return {}

        risk_records = self.session.query(RoadSegmentRisk).filter(
            RoadSegmentRisk.id.in_(edge_ids)
        ).all()

        result = {}
        for record in risk_records:
            result[record.id] = {
                'risk_score': record.risk_score,
                'accident_frequency': record.accident_frequency,
                'severity_distribution': record.severity_distribution,
                'record_count': record.record_count,
                'data_source': record.data_source
            }

        return result

    def _calculate_cost_components(
        self,
        edge: GraphEdge,
        risk_data: Optional[dict],
        traffic_data: Optional[dict]
    ) -> CostComponents:
        """
        Calculate all cost components for an edge.

        Args:
            edge: The GraphEdge object
            risk_data: Risk metadata for the edge (may be None)
            traffic_data: Traffic metadata for the edge (may be None)

        Returns:
            CostComponents object with all calculated costs
        """
        components = CostComponents()

        # 1. Distance cost (always enabled)
        components.distance = edge.length * self.cost_config.distance_per_meter * self.cost_config.distance_weight

        # 2. Risk cost (based on RoadSegmentRisk metadata)
        if risk_data and risk_data.get('risk_score') is not None:
            # Normalize risk score (0-1 range assumed) and apply multiplier
            risk_component = risk_data['risk_score'] * self.cost_config.risk_score_multiplier
            components.risk = risk_component * self.cost_config.risk_weight
        else:
            # No risk data available - minimal risk cost
            components.risk = 0.0

        # 3. Elevation cost (placeholder - would need elevation data)
        if self.cost_config.enable_elevation:
            # In a real implementation, we would calculate elevation change
            # For now, we'll use a placeholder based on road characteristics
            elevation_factor = getattr(edge, 'elevation_change', 0.0)
            components.elevation = abs(elevation_factor) * self.cost_config.elevation_cost_per_meter
        # Else remains 0.0

        # 4. Road class cost
        if self.cost_config.enable_road_class and edge.road_class:
            base_cost = 1.0  # Base cost for unknown road class
            # Apply specific weight if available, otherwise use default
            class_weight = self.cost_config.road_class_weights.get(
                edge.road_class,
                self.cost_config.road_class_weight
            )
            components.road_class = base_cost * class_weight

        # 5. Surface cost
        if self.cost_config.enable_surface and edge.surface:
            base_cost = 1.0  # Base cost for unknown surface
            # Apply specific weight if available, otherwise use default
            surface_weight = self.cost_config.surface_weights.get(
                edge.surface,
                self.cost_config.surface_weight
            )
            components.surface = base_cost * surface_weight

        # 6. Turn cost (placeholder - would require sequence of edges)
        if self.cost_config.enable_turn:
            # Turn cost would depend on the angle between consecutive edges
            # Since we only process single edges, this is always 0 for standalone calculation
            # In a pathfinding context, this would be calculated based on direction changes
            components.turn = 0.0

        # 7. Weather cost (placeholder - would require weather data)
        if self.cost_config.enable_weather:
            # Weather cost would depend on current weather conditions
            # For now, we'll use a placeholder
            components.weather = 0.0

        # 8. Traffic cost (NEW - real-time traffic integration)
        if self.cost_config.enable_traffic and traffic_data:
            components.traffic = self._calculate_traffic_cost(edge, traffic_data)
        else:
            components.traffic = 0.0

        return components

    def _calculate_traffic_cost(self, edge: GraphEdge, traffic_data: dict) -> float:
        """
        Calculate traffic-based cost component.

        Args:
            edge: The GraphEdge object
            traffic_data: Traffic metadata including flow, incidents, closures, construction

        Returns:
            Traffic cost value
        """
        cost = 0.0
        base_penalty = getattr(self.cost_config, 'traffic_base_penalty', 10.0)

        # 8a. Congestion cost from flow data
        flow = traffic_data.get('flow')
        if flow:
            # Use congestion ratio (free_flow_speed / current_speed)
            # congestion_ratio of 1.0 = free flow, > 1.0 = congestion
            congestion_ratio = flow.get('congestion_ratio')
            if congestion_ratio and congestion_ratio > 1.0:
                # Exponential penalty for congestion
                # At 1.5x (50% slower): moderate penalty
                # At 2.0x (2x slower): high penalty
                # At 3.0x+: severe penalty
                congestion_penalty = base_penalty * (congestion_ratio - 1.0) ** 2
                cost += congestion_penalty

            # Also consider jam_factor (0-10 scale)
            jam_factor = flow.get('jam_factor')
            if jam_factor:
                jam_penalty = base_penalty * (jam_factor / 10.0)
                cost += jam_penalty

            # Direct delay
            delay_seconds = flow.get('delay_seconds')
            if delay_seconds and delay_seconds > 0:
                delay_penalty = base_penalty * (delay_seconds / 60.0)  # Convert to minutes
                cost += delay_penalty

        # 8b. Incident penalties
        incidents = traffic_data.get('incidents', [])
        for incident in incidents:
            inc_cost = self._calculate_incident_cost(incident)
            cost += inc_cost

        # 8c. Road closure penalties (very high)
        closures = traffic_data.get('closures', [])
        if closures:
            cost += self.cost_config.traffic_closure_penalty

        # 8d. Construction zone penalties
        construction = traffic_data.get('construction', [])
        for zone in construction:
            zone_cost = self._calculate_construction_cost(zone)
            cost += zone_cost

        return cost * self.cost_config.traffic_weight

    def _calculate_incident_cost(self, incident: dict) -> float:
        """
        Calculate cost for a single incident.

        Args:
            incident: Incident data dictionary

        Returns:
            Incident cost value
        """
        cost = 0.0
        base_penalty = getattr(self.cost_config, 'traffic_base_penalty', 10.0)

        # Base cost by severity
        severity_costs = {
            'LOW': 1.0,
            'MEDIUM': 5.0,
            'HIGH': 20.0,
            'CRITICAL': 50.0
        }
        cost += severity_costs.get(incident.get('severity', 'MEDIUM'), 5.0)

        # Additional cost for lane closures
        lanes_affected = incident.get('lanes_affected')
        total_lanes = incident.get('total_lanes')
        if lanes_affected and total_lanes and total_lanes > 0:
            closure_ratio = lanes_affected / total_lanes
            cost += closure_ratio * 10.0

        # Additional cost for delay
        delay_minutes = incident.get('delay_minutes')
        if delay_minutes:
            cost += delay_minutes * 0.5  # 0.5 cost per minute of delay

        # Closure type modifier
        closure_type = incident.get('closure_type')
        if closure_type == 'FULL':
            cost *= 2.0
        elif closure_type == 'PARTIAL':
            cost *= 1.5

        return cost * incident.get('confidence', 0.8)

    def _calculate_construction_cost(self, construction: dict) -> float:
        """
        Calculate cost for a construction zone.

        Args:
            construction: Construction zone data dictionary

        Returns:
            Construction cost value
        """
        cost = 0.0
        base_penalty = getattr(self.cost_config, 'traffic_base_penalty', 10.0)

        # Base cost by impact level
        impact_costs = {
            'LOW': 2.0,
            'MODERATE': 5.0,
            'HIGH': 15.0,
            'SEVERE': 30.0
        }
        cost += impact_costs.get(construction.get('impact_level', 'MODERATE'), 5.0)

        # Lane reduction penalty
        lanes_affected = construction.get('lanes_affected')
        lanes_remaining = construction.get('lanes_remaining')
        if lanes_affected and lanes_remaining is not None:
            total = lanes_affected + lanes_remaining
            if total > 0:
                reduction = lanes_affected / total
                cost += reduction * 10.0

        # Contraflow penalty
        if construction.get('contraflow'):
            cost += 5.0

        # Speed limit reduction penalty
        speed_limit = construction.get('speed_limit_kmh')
        if speed_limit and speed_limit < 50:
            # Penalty increases as speed limit decreases from free flow
            speed_penalty = base_penalty * (1.0 - min(speed_limit / 80.0, 1.0))
            cost += speed_penalty

        return cost * construction.get('confidence', 0.9)