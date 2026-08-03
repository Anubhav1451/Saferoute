"""add_route_monitor_and_offline_tables

Revision ID: rc91_add_route_monitor_and_offline_tables
Revises: 520e30f0c181
Create Date: 2026-08-03 16:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'rc91_add_route_monitor_and_offline_tables'
down_revision: Union[str, Sequence[str], None] = '520e30f0c181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create route_monitor table
    op.create_table(
        'route_monitor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.String(length=255), nullable=False),
        sa.Column('start_location', sa.String(length=255), nullable=False),
        sa.Column('end_location', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_monitor_id'), 'route_monitor', ['id'], unique=False)
    op.create_index(op.f('ix_route_monitor_route_id'), 'route_monitor', ['route_id'], unique=False)

    # Create offline_maps table
    op.create_table(
        'offline_maps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('bounds_north', sa.Float(), nullable=False),
        sa.Column('bounds_south', sa.Float(), nullable=False),
        sa.Column('bounds_east', sa.Float(), nullable=False),
        sa.Column('bounds_west', sa.Float(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offline_maps_id'), 'offline_maps', ['id'], unique=False)
    op.create_index(op.f('ix_offline_maps_name'), 'offline_maps', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_offline_maps_name'), table_name='offline_maps')
    op.drop_index(op.f('ix_offline_maps_id'), table_name='offline_maps')
    op.drop_table('offline_maps')
    op.drop_index(op.f('ix_route_monitor_route_id'), table_name='route_monitor')
    op.drop_index(op.f('ix_route_monitor_id'), table_name='route_monitor')
    op.drop_table('route_monitor')