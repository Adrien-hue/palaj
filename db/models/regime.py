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

    min_rp_annuels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_rp_dimanches: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    min_rpsd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_rp_2plus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    min_rp_semestre: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    avg_service_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_tolerance_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="regime")

    def __repr__(self) -> str:
        return f"<Regime {self.nom}>"
