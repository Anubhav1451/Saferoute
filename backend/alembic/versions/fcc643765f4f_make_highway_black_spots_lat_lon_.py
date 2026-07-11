"""make highway_black_spots lat/lon nullable for PENDING resolution

Revision ID: fcc643765f4f
Revises: 8a4f5e2c1b9d
Create Date: 2026-06-27 23:21:24.363424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'fcc643765f4f'
down_revision: Union[str, Sequence[str], None] = '8a4f5e2c1b9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('highway_black_spots') as batch_op:
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('highway_black_spots') as batch_op:
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=False)
