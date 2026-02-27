from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PlanningDraftAssignment(Base):
    __tablename__ = "planning_draft_assignments"
    __table_args__ = (
        UniqueConstraint("draft_agent_day_id", "tranche_id", name="uq_planning_draft_assignment_day_tranche"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_agent_day_id: Mapped[int] = mapped_column(
        ForeignKey("planning_draft_agent_days.id", ondelete="CASCADE"),
        nullable=False,
    )
    tranche_id: Mapped[int] = mapped_column(ForeignKey("tranches.id", ondelete="RESTRICT"), nullable=False)
