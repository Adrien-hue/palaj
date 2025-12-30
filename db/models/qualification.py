# db/models/qualification.py
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .agent import Agent
    from .poste import Poste


class Qualification(Base):
    __tablename__ = "qualifications"
    __table_args__ = (UniqueConstraint("agent_id", "poste_id", name="_qualification_uc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    poste_id: Mapped[int] = mapped_column(ForeignKey("postes.id"), nullable=False)
    date_qualification: Mapped[Optional[Date]] = mapped_column(Date, nullable=True)

    agent: Mapped[Agent] = relationship("Agent", back_populates="qualifications")
    poste: Mapped[Poste] = relationship("Poste", back_populates="qualifications")

    def __repr__(self) -> str:
        return f"<Qualification agent={self.agent_id} poste={self.poste_id}>"
