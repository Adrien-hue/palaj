from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .agent_day_assignment import AgentDayAssignment

class AgentDay(Base):
    __tablename__ = "agent_days"
    __table_args__ = (
        UniqueConstraint("agent_id", "day_date", name="uq_agent_days_agent_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)

    day_date: Mapped[date] = mapped_column(Date, nullable=False)
    day_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_off_shift: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    assignments: Mapped[List[AgentDayAssignment]] = relationship(
        back_populates="agent_day",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )
