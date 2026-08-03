"""merge heads for release

Revision ID: 8b9838ddd5a9
Revises: 58b83ebd3f6e, rc91_add_route_monitor_and_offline_tables
Create Date: 2026-08-03 21:13:21.197546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9838ddd5a9'
down_revision: Union[str, Sequence[str], None] = ('58b83ebd3f6e', 'rc91_add_route_monitor_and_offline_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass