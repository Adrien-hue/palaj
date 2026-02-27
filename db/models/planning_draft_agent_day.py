from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PlanningDraftAgentDay(Base):
    __tablename__ = "planning_draft_agent_days"
    __table_args__ = (
        UniqueConstraint("draft_id", "agent_id", "day_date", name="uq_planning_draft_agent_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("planning_drafts.id", ondelete="CASCADE"), nullable=False)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)

    day_date: Mapped[date] = mapped_column(Date, nullable=False)
    day_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_off_shift: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")
