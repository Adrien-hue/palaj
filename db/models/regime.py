# db/models/regime.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base

class Regime(Base):
    __tablename__ = "regimes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(50), nullable=False, unique=True)
    desc = Column(Text, nullable=True)
    duree_moyenne_journee_service_min = Column(Integer, nullable=False)
    repos_periodiques_annuels = Column(Integer, nullable=True)

    agents = relationship("Agent", back_populates="regime")

    def __repr__(self):
        return f"<Regime {self.nom}>"
