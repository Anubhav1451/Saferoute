"""
Shared helpers for routing service tests.

Builds a small in-memory GIS graph (GraphNode/GraphEdge/RoadSegmentRisk)
so tests exercise the current production routing implementation
(SafetyRoutingService.find_safest_route) without mocking it.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, GraphNode, GraphEdge, RoadSegmentRisk
from app.schemas.routing import Coordinate


# Well-known coordinates used by all routing tests (Delhi region, within India bounds)
SOURCE_LAT, SOURCE_LON = 28.6315, 77.2167      # Near node 1
MID_LAT, MID_LON = 28.6325, 77.2177            # Node 2
DEST_LAT, DEST_LON = 28.6335, 77.2187          # Near node 3


def create_graph_session():
    """
    Create an in-memory SQLite session with a small linear graph:
    node1 -- edge1 -- node2 -- edge2 -- node3.
    Each edge has a RoadSegmentRisk record.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    n1 = GraphNode(id=1, osm_node_id=101, latitude=28.6315, longitude=77.2167)
    n2 = GraphNode(id=2, osm_node_id=102, latitude=28.6325, longitude=77.2177)
    n3 = GraphNode(id=3, osm_node_id=103, latitude=28.6335, longitude=77.2187)
    db.add_all([n1, n2, n3])
    db.flush()

    e1 = GraphEdge(
        id=1, source_node_id=1, dest_node_id=2, osm_way_id=None,
        length=200.0, direction="BIDIRECTIONAL", highway="residential",
        travel_time=20.0, road_class="residential",
    )
    e2 = GraphEdge(
        id=2, source_node_id=2, dest_node_id=3, osm_way_id=None,
        length=200.0, direction="BIDIRECTIONAL", highway="residential",
        travel_time=20.0, road_class="residential",
    )
    db.add_all([e1, e2])
    db.flush()

    r1 = RoadSegmentRisk(
        id=1, start_latitude=28.632, start_longitude=77.217,
        end_latitude=28.632, end_longitude=77.217,
        road_name="test", segment_length_m=200.0, risk_score=0.2,
    )
    r2 = RoadSegmentRisk(
        id=2, start_latitude=28.633, start_longitude=77.218,
        end_latitude=28.633, end_longitude=77.218,
        road_name="test", segment_length_m=200.0, risk_score=0.5,
    )
    db.add_all([r1, r2])
    db.commit()
    return db


def default_source() -> Coordinate:
    """Source near node 1."""
    return Coordinate(latitude=SOURCE_LAT, longitude=SOURCE_LON)


def default_destination() -> Coordinate:
    """Destination near node 3."""
    return Coordinate(latitude=DEST_LAT, longitude=DEST_LON)


def assert_valid_route_result(result):
    """Assert a routing result matches the current production response contract."""
    assert isinstance(result, dict)
    for key in ("safest_route", "fastest_route", "safest_distance", "fastest_distance",
                "safest_safety_score", "fastest_safety_score", "route_segments"):
        assert key in result, f"missing key {key} in routing result"

    for route_key in ("safest_route", "fastest_route"):
        route = result[route_key]
        assert len(route) >= 2
        for coord in route:
            assert hasattr(coord, "latitude")
            assert hasattr(coord, "longitude")
            assert isinstance(coord.latitude, float)
            assert isinstance(coord.longitude, float)

    assert result["safest_distance"] >= 0
    assert result["fastest_distance"] >= 0
    assert 0.0 <= result["safest_safety_score"] <= 1.0
    assert 0.0 <= result["fastest_safety_score"] <= 1.0

    segments = result["route_segments"]
    assert isinstance(segments, list)
    assert len(segments) >= 1
    for seg in segments:
        assert isinstance(seg, dict)
        assert "from_coord" in seg and "to_coord" in seg
        assert "distance" in seg and "safety_score" in seg and "penalty" in seg
        assert seg["distance"] >= 0
        assert 0.0 <= seg["safety_score"] <= 1.0
