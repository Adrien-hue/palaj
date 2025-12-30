# db/models/regime.py
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .agent import Agent


class Regime(Base):
    __tablename__ = "regimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duree_moyenne_journee_service_min: Mapped[int] = mapped_column(Integer, nullable=False)
    repos_periodiques_annuels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    agents: Mapped[list[Agent]] = relationship("Agent", back_populates="regime")

    def __repr__(self) -> str:
        return f"<Regime {self.nom}>"
