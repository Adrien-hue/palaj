from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Date,
    Time,
    ForeignKey,
    Enum as SAEnum,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base

from core.domain.entities.etat_jour_agent import TypeJour


# =====================================================
#   Agent
# =====================================================
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
