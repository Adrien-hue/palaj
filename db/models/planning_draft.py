from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from core.domain.enums.planning_draft_status import PlanningDraftStatus
from .base import Base


class PlanningDraft(Base):
    __tablename__ = "planning_drafts"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)

    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_limit_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    result_stats: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    @validates("status")
    def validate_status(self, key: str, value: str) -> str:
        _ = key
        return PlanningDraftStatus(value).value
