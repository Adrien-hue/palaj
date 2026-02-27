"""add index on planning drafts job id

Revision ID: b91d2e46f031
Revises: 8d4c0c9f6b2a
Create Date: 2026-02-26 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b91d2e46f031'
down_revision: Union[str, Sequence[str], None] = '8d4c0c9f6b2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_planning_drafts_job_id', 'planning_drafts', ['job_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_planning_drafts_job_id', table_name='planning_drafts')
