"""add planning drafts tables

Revision ID: 8d4c0c9f6b2a
Revises: 3d0d31e433ce
Create Date: 2026-02-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d4c0c9f6b2a'
down_revision: Union[str, Sequence[str], None] = '3d0d31e433ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'planning_drafts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('seed', sa.Integer(), nullable=True),
        sa.Column('time_limit_seconds', sa.Integer(), nullable=False),
        sa.Column('result_stats', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], name=op.f('fk_planning_drafts_team_id_teams'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_planning_drafts')),
        sa.UniqueConstraint('job_id', name=op.f('uq_planning_drafts_job_id')),
    )

    op.create_table(
        'planning_draft_agent_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('draft_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('day_date', sa.Date(), nullable=False),
        sa.Column('day_type', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_off_shift', sa.Boolean(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], name=op.f('fk_planning_draft_agent_days_agent_id_agents'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['planning_drafts.id'], name=op.f('fk_planning_draft_agent_days_draft_id_planning_drafts'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_planning_draft_agent_days')),
        sa.UniqueConstraint('draft_id', 'agent_id', 'day_date', name='uq_planning_draft_agent_day'),
    )

    op.create_table(
        'planning_draft_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('draft_agent_day_id', sa.Integer(), nullable=False),
        sa.Column('tranche_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['draft_agent_day_id'], ['planning_draft_agent_days.id'], name=op.f('fk_planning_draft_assignments_draft_agent_day_id_planning_draft_agent_days'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tranche_id'], ['tranches.id'], name=op.f('fk_planning_draft_assignments_tranche_id_tranches'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_planning_draft_assignments')),
        sa.UniqueConstraint('draft_agent_day_id', 'tranche_id', name='uq_planning_draft_assignment_day_tranche'),
    )


def downgrade() -> None:
    op.drop_table('planning_draft_assignments')
    op.drop_table('planning_draft_agent_days')
    op.drop_table('planning_drafts')
