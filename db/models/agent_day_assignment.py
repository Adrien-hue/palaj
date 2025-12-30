from __future__ import annotations

from typing  import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .agent_day import AgentDay
    from .tranche import Tranche

class AgentDayAssignment(Base):
    __tablename__ = "agent_day_assignments"
    __table_args__ = (
        UniqueConstraint("agent_day_id", "tranche_id", name="uq_agent_day_assignments_day_tranche"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_day_id: Mapped[int] = mapped_column(ForeignKey("agent_days.id", ondelete="CASCADE"), nullable=False)
    tranche_id: Mapped[int] = mapped_column(ForeignKey("tranches.id", ondelete="RESTRICT"), nullable=False)

    agent_day: Mapped[AgentDay] = relationship(back_populates="assignments", lazy="selectin")
    tranche: Mapped[Tranche] = relationship(lazy="selectin")
