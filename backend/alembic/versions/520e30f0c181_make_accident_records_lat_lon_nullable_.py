"""make accident_records lat/lon nullable for incomplete records

Revision ID: 520e30f0c181
Revises: fcc643765f4f
Create Date: 2026-06-27 23:27:36.530062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '520e30f0c181'
down_revision: Union[str, Sequence[str], None] = 'fcc643765f4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('accident_records') as batch_op:
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=True)
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('accident_records') as batch_op:
        batch_op.alter_column('latitude', existing_type=sa.FLOAT(), nullable=False)
        batch_op.alter_column('longitude', existing_type=sa.FLOAT(), nullable=False)
