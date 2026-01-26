# db/models/agent.py
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .regime import Regime
    from .qualification import Qualification
    from .team import Team


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    code_personnel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    regime_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regimes.id"), nullable=True)

    regime: Mapped[Optional[Regime]] = relationship("Regime", back_populates="agents")

    qualifications: Mapped[list[Qualification]] = relationship(
        "Qualification",
        back_populates="agent",
        cascade="all, delete-orphan",
    )

    teams: Mapped[list["Team"]] = relationship(
        "Team",
        secondary="agent_teams",
        back_populates="agents",
        lazy="selectin",
    )


    def __repr__(self) -> str:
        return f"<Agent {self.prenom} {self.nom}>"
