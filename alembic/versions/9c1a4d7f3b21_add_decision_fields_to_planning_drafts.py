"""add decision fields to planning drafts

Revision ID: 9c1a4d7f3b21
Revises: 5fc5e82706d6
Create Date: 2026-03-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1a4d7f3b21'
down_revision: Union[str, Sequence[str], None] = '5fc5e82706d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('planning_drafts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('accepted_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('rejected_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('planning_drafts', schema=None) as batch_op:
        batch_op.drop_column('rejected_at')
        batch_op.drop_column('accepted_at')
