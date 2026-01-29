# db/models/tranche.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .poste_coverage_requirement import PosteCoverageRequirement
    from .poste import Poste


class Tranche(Base):
    __tablename__ = "tranches"
    __table_args__ = (
        UniqueConstraint("nom", "poste_id", name="_tranche_unique_per_poste"),
        UniqueConstraint("poste_id", "id", name="uq_tranche_poste_id_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    heure_debut: Mapped[Time] = mapped_column(Time, nullable=False)
    heure_fin: Mapped[Time] = mapped_column(Time, nullable=False)
    poste_id: Mapped[int] = mapped_column(ForeignKey("postes.id"), nullable=False)

    poste: Mapped[Poste] = relationship("Poste", back_populates="tranches")

    coverage_requirements: Mapped[list["PosteCoverageRequirement"]] = relationship(
        "PosteCoverageRequirement",
        back_populates="tranche",
        cascade="all, delete-orphan",
    )


    def __repr__(self) -> str:
        return (
            f"<Tranche {self.nom} "
            f"({self.heure_debut}-{self.heure_fin}) "
            f"Poste={self.poste_id}>"
        )
