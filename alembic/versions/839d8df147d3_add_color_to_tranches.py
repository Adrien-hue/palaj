"""add color to tranches

Revision ID: 839d8df147d3
Revises: ce65695fb1c5
Create Date: 2026-02-02 11:14:19.451978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "839d8df147d3"
down_revision: Union[str, Sequence[str], None] = "ce65695fb1c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tranches", schema=None) as batch_op:
        batch_op.add_column(sa.Column("color", sa.String(length=7), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tranches", schema=None) as batch_op:
        batch_op.drop_column("color")
