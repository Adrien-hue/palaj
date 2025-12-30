# db/models/tranche.py
from sqlalchemy import Column, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base


class Tranche(Base):
    __tablename__ = "tranches"
    __table_args__ = (UniqueConstraint("nom", "poste_id", name="_tranche_unique_per_poste"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    heure_debut = Column(Time, nullable=False)
    heure_fin = Column(Time, nullable=False)
    poste_id = Column(Integer, ForeignKey("postes.id"), nullable=False)

    poste = relationship("Poste", back_populates="tranches")
    affectations = relationship("Affectation", back_populates="tranche", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tranche {self.nom} ({self.heure_debut}-{self.heure_fin}) Poste={self.poste_id}>"
