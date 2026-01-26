from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AgentTeam(Base):
    __tablename__ = "agent_teams"
    __table_args__ = (
        Index("ix_agent_teams_agent_id", "agent_id"),
        Index("ix_agent_teams_team_id", "team_id"),
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AgentTeam agent_id={self.agent_id} team_id={self.team_id}>"
