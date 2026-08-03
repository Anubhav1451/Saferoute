"""add production graph osm and traffic tables

Creates the eight production tables that are referenced by the routing,
traffic, and OSM pipeline code but were never added to the migration chain:

    osm_ways, osm_way_nodes, graph_nodes, graph_edges,
    traffic_incidents, traffic_flow, road_closures, construction_zones

The schema is taken directly from the existing SQLAlchemy models in
app/db/models.py via Base.metadata, so the created tables always match the
ORM definitions used by the application.

Revision ID: 58b83ebd3f6e
Revises: 520e30f0c181
Create Date: 2026-08-03 15:48:54.359658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.models import Base


# revision identifiers, used by Alembic.
revision: str = '58b83ebd3f6e'
down_revision: Union[str, Sequence[str], None] = '520e30f0c181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Production tables defined in app/db/models.py that are missing from
# the migration chain. create_all/drop_all sort them by foreign-key
# dependency order, so graph_edges is created after graph_nodes/osm_ways
# and traffic_flow is created after graph_edges/osm_ways.
PRODUCTION_TABLES = [
    'osm_ways',
    'osm_way_nodes',
    'graph_nodes',
    'graph_edges',
    'traffic_incidents',
    'traffic_flow',
    'road_closures',
    'construction_zones',
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in PRODUCTION_TABLES]
    Base.metadata.create_all(bind=bind, tables=tables)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the tables explicitly, dependents first, so PostgreSQL foreign-key
    # constraints do not block the drops. (Base.metadata.drop_all cannot be
    # used here: on PostgreSQL it also tries to drop the enum types of *other*
    # tables in the metadata, e.g. safety_nodes.lighting_level, which still
    # depend on those types.)
    op.drop_table('traffic_flow')
    op.drop_table('graph_edges')
    op.drop_table('osm_way_nodes')
    op.drop_table('traffic_incidents')
    op.drop_table('construction_zones')
    op.drop_table('road_closures')
    op.drop_table('graph_nodes')
    op.drop_table('osm_ways')
