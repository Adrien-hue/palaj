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

# =====================================================
#   État jour agent
# =====================================================
class EtatJourAgent(Base):
    __tablename__ = "etat_jour_agent"
    __table_args__ = (UniqueConstraint("agent_id", "jour", name="_etat_jour_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    jour = Column(Date, nullable=False)
    type_jour = Column(
        SAEnum(
            TypeJour,
            values_callable=lambda enum: [e.value for e in enum],  # stock "conge" plutôt que "TypeJour.CONGE"
            name="type_jour_enum"
        ), 
        nullable=False
    )
    description = Column(Text, nullable=True)

    agent = relationship("Agent", back_populates="etats")

    def __repr__(self):
        return f"<EtatJourAgent agent={self.agent_id} jour={self.jour} type={self.type_jour}>"