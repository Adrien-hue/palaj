# db/models/poste.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Poste(Base):
    __tablename__ = "postes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False, unique=True)

    tranches = relationship("Tranche", back_populates="poste", cascade="all, delete-orphan")
    qualifications = relationship("Qualification", back_populates="poste", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poste {self.nom}>"
