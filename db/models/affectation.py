# db/models/affectation.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .agent import Agent
    from .tranche import Tranche


class Affectation(Base):
    __tablename__ = "affectations"
    __table_args__ = (UniqueConstraint("agent_id", "jour", "tranche_id", name="_affectation_uc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    tranche_id: Mapped[int] = mapped_column(ForeignKey("tranches.id"), nullable=False)
    jour: Mapped[Date] = mapped_column(Date, nullable=False)

    agent: Mapped[Agent] = relationship("Agent", back_populates="affectations")
    tranche: Mapped[Tranche] = relationship("Tranche", back_populates="affectations")

    def __repr__(self) -> str:
        return f"<Affectation agent={self.agent_id} tranche={self.tranche_id} jour={self.jour}>"
