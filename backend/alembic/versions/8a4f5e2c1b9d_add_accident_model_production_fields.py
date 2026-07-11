"""add_accident_model_production_fields

Revision ID: 8a4f5e2c1b9d
Revises: 6fc9b1c4c063
Create Date: 2026-06-27 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8a4f5e2c1b9d'
down_revision: Union[str, Sequence[str], None] = '6fc9b1c4c063'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === HighwayBlackSpot ===
    op.add_column('highway_black_spots', sa.Column('state', sa.String(50), nullable=True))
    op.add_column('highway_black_spots', sa.Column('district', sa.String(100), nullable=True))
    op.add_column('highway_black_spots', sa.Column('highway_number', sa.String(50), nullable=True))
    op.add_column('highway_black_spots', sa.Column('managed_by', sa.String(100), nullable=True))
    op.add_column('highway_black_spots', sa.Column('official_id', sa.String(100), nullable=True))
    op.add_column('highway_black_spots', sa.Column('chainage_start_km', sa.Float(), nullable=True))
    op.add_column('highway_black_spots', sa.Column('chainage_end_km', sa.Float(), nullable=True))
    op.add_column('highway_black_spots', sa.Column('location_text', sa.String(500), nullable=True))
    op.add_column('highway_black_spots', sa.Column('geometry_resolution', sa.String(50), nullable=True))
    op.add_column('highway_black_spots', sa.Column('source_name', sa.String(100), nullable=True))
    op.add_column('highway_black_spots', sa.Column('source_url', sa.String(500), nullable=True))
    op.add_column('highway_black_spots', sa.Column('confidence_score', sa.Float(), nullable=True))

    op.create_index(op.f('ix_highway_black_spots_state'), 'highway_black_spots', ['state'], unique=False)
    op.create_index(op.f('ix_highway_black_spots_district'), 'highway_black_spots', ['district'], unique=False)
    op.create_index(op.f('ix_highway_black_spots_highway_number'), 'highway_black_spots', ['highway_number'], unique=False)
    op.create_index(op.f('ix_highway_black_spots_official_id'), 'highway_black_spots', ['official_id'], unique=False)
    op.create_index('ix_highway_black_spots_state_district', 'highway_black_spots', ['state', 'district'], unique=False)
    op.create_index('ix_highway_black_spots_hwy_chainage', 'highway_black_spots', ['highway_number', 'chainage_start_km'], unique=False)

    # === AccidentRecord ===
    op.add_column('accident_records', sa.Column('state', sa.String(50), nullable=True))
    op.add_column('accident_records', sa.Column('district', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('city', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('year', sa.Integer(), nullable=True))
    op.add_column('accident_records', sa.Column('collision_type', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('violation_type', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('road_user_type', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('vehicle_type', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('road_class', sa.String(50), nullable=True))
    op.add_column('accident_records', sa.Column('source_name', sa.String(100), nullable=True))
    op.add_column('accident_records', sa.Column('aggregation_level', sa.String(50), nullable=True))

    op.create_index(op.f('ix_accident_records_state'), 'accident_records', ['state'], unique=False)
    op.create_index(op.f('ix_accident_records_district'), 'accident_records', ['district'], unique=False)
    op.create_index(op.f('ix_accident_records_city'), 'accident_records', ['city'], unique=False)
    op.create_index(op.f('ix_accident_records_year'), 'accident_records', ['year'], unique=False)
    op.create_index(op.f('ix_accident_records_collision_type'), 'accident_records', ['collision_type'], unique=False)
    op.create_index(op.f('ix_accident_records_violation_type'), 'accident_records', ['violation_type'], unique=False)
    op.create_index(op.f('ix_accident_records_road_class'), 'accident_records', ['road_class'], unique=False)
    op.create_index(op.f('ix_accident_records_aggregation_level'), 'accident_records', ['aggregation_level'], unique=False)
    op.create_index('ix_accident_records_state_year', 'accident_records', ['state', 'year'], unique=False)
    op.create_index('ix_accident_records_date_aggregation', 'accident_records', ['accident_date', 'aggregation_level'], unique=False)

    # === RoadSegmentRisk ===
    op.add_column('road_segment_risks', sa.Column('segment_length_km', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('highway_number', sa.String(50), nullable=True))
    op.add_column('road_segment_risks', sa.Column('road_class', sa.String(50), nullable=True))
    op.add_column('road_segment_risks', sa.Column('exposure_factor', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('accident_density', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('fatality_weight', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('blackspot_weight', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('road_segment_risks', sa.Column('last_updated', sa.DateTime(), nullable=True))

    op.create_index(op.f('ix_road_segment_risks_highway_number'), 'road_segment_risks', ['highway_number'], unique=False)
    op.create_index(op.f('ix_road_segment_risks_road_class'), 'road_segment_risks', ['road_class'], unique=False)
    op.create_index('ix_road_segment_risks_hwy_class', 'road_segment_risks', ['highway_number', 'road_class'], unique=False)


def downgrade() -> None:
    # === RoadSegmentRisk ===
    op.drop_index('ix_road_segment_risks_hwy_class', table_name='road_segment_risks')
    op.drop_index(op.f('ix_road_segment_risks_road_class'), table_name='road_segment_risks')
    op.drop_index(op.f('ix_road_segment_risks_highway_number'), table_name='road_segment_risks')
    op.drop_column('road_segment_risks', 'last_updated')
    op.drop_column('road_segment_risks', 'confidence_score')
    op.drop_column('road_segment_risks', 'blackspot_weight')
    op.drop_column('road_segment_risks', 'fatality_weight')
    op.drop_column('road_segment_risks', 'accident_density')
    op.drop_column('road_segment_risks', 'exposure_factor')
    op.drop_column('road_segment_risks', 'road_class')
    op.drop_column('road_segment_risks', 'highway_number')
    op.drop_column('road_segment_risks', 'segment_length_km')

    # === AccidentRecord ===
    op.drop_index('ix_accident_records_date_aggregation', table_name='accident_records')
    op.drop_index('ix_accident_records_state_year', table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_aggregation_level'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_road_class'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_violation_type'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_collision_type'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_year'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_city'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_district'), table_name='accident_records')
    op.drop_index(op.f('ix_accident_records_state'), table_name='accident_records')
    op.drop_column('accident_records', 'aggregation_level')
    op.drop_column('accident_records', 'source_name')
    op.drop_column('accident_records', 'road_class')
    op.drop_column('accident_records', 'vehicle_type')
    op.drop_column('accident_records', 'road_user_type')
    op.drop_column('accident_records', 'violation_type')
    op.drop_column('accident_records', 'collision_type')
    op.drop_column('accident_records', 'year')
    op.drop_column('accident_records', 'city')
    op.drop_column('accident_records', 'district')
    op.drop_column('accident_records', 'state')

    # === HighwayBlackSpot ===
    op.drop_index('ix_highway_black_spots_hwy_chainage', table_name='highway_black_spots')
    op.drop_index('ix_highway_black_spots_state_district', table_name='highway_black_spots')
    op.drop_index(op.f('ix_highway_black_spots_official_id'), table_name='highway_black_spots')
    op.drop_index(op.f('ix_highway_black_spots_highway_number'), table_name='highway_black_spots')
    op.drop_index(op.f('ix_highway_black_spots_district'), table_name='highway_black_spots')
    op.drop_index(op.f('ix_highway_black_spots_state'), table_name='highway_black_spots')
    op.drop_column('highway_black_spots', 'confidence_score')
    op.drop_column('highway_black_spots', 'source_url')
    op.drop_column('highway_black_spots', 'source_name')
    op.drop_column('highway_black_spots', 'geometry_resolution')
    op.drop_column('highway_black_spots', 'location_text')
    op.drop_column('highway_black_spots', 'chainage_end_km')
    op.drop_column('highway_black_spots', 'chainage_start_km')
    op.drop_column('highway_black_spots', 'official_id')
    op.drop_column('highway_black_spots', 'managed_by')
    op.drop_column('highway_black_spots', 'highway_number')
    op.drop_column('highway_black_spots', 'district')
    op.drop_column('highway_black_spots', 'state')
