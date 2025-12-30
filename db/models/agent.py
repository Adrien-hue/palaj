# db/models/agent.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    code_personnel = Column(String(50), nullable=True)
    regime_id = Column(Integer, ForeignKey("regimes.id"), nullable=True)

    regime = relationship("Regime", back_populates="agents")
    affectations = relationship("Affectation", back_populates="agent", cascade="all, delete-orphan")
    etats = relationship("EtatJourAgent", back_populates="agent", cascade="all, delete-orphan")
    qualifications = relationship("Qualification", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent {self.prenom} {self.nom}>"
