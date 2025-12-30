# db/models/etat_jour_agent.py
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TypeJourDB

if TYPE_CHECKING:
    from .agent import Agent


class EtatJourAgent(Base):
    __tablename__ = "etat_jour_agent"
    __table_args__ = (UniqueConstraint("agent_id", "jour", name="_etat_jour_uc"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    jour: Mapped[Date] = mapped_column(Date, nullable=False)

    type_jour: Mapped[TypeJourDB] = mapped_column(
        SAEnum(
            TypeJourDB,
            values_callable=lambda enum: [e.value for e in enum],  # store "conge" not "TypeJourDB.CONGE"
            name="type_jour_enum",
        ),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    agent: Mapped[Agent] = relationship("Agent", back_populates="etats")

    def __repr__(self) -> str:
        return f"<EtatJourAgent agent={self.agent_id} jour={self.jour} type={self.type_jour}>"
