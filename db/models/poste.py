# db/models/poste.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .qualification import Qualification
    from .tranche import Tranche


class Poste(Base):
    __tablename__ = "postes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    tranches: Mapped[list[Tranche]] = relationship(
        "Tranche",
        back_populates="poste",
        cascade="all, delete-orphan",
    )
    qualifications: Mapped[list[Qualification]] = relationship(
        "Qualification",
        back_populates="poste",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Poste {self.nom}>"
