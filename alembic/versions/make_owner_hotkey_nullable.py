"""make owner_hotkey nullable in coupon_ownerships

Revision ID: f2e3d4c5b6a7
Revises: e1b2c3d4a5f6
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2e3d4c5b6a7'
down_revision: Union[str, Sequence[str], None] = 'e1b2c3d4a5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Make owner_hotkey nullable in coupon_ownerships table
    op.alter_column('coupon_ownerships', 'owner_hotkey',
                    existing_type=sa.String(),
                    nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make owner_hotkey non-nullable again
    op.alter_column('coupon_ownerships', 'owner_hotkey',
                    existing_type=sa.String(),
                    nullable=False)
