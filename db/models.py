from sqlalchemy import (
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
from sqlalchemy.orm import relationship

from db.base import Base

from core.domain.entities.etat_jour_agent import TypeJour


# =====================================================
#   Agent
# =====================================================
class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
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
#   Poste
# =====================================================
class Poste(Base):
    __tablename__ = "postes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nom = Column(String(100), nullable=False, unique=True)

    tranches = relationship("Tranche", back_populates="poste", cascade="all, delete-orphan")
    qualifications = relationship("Qualification", back_populates="poste", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poste {self.nom}>"


# =====================================================
#   Tranche horaire
# =====================================================
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


# =====================================================
#   Affectation
# =====================================================
class Affectation(Base):
    __tablename__ = "affectations"
    __table_args__ = (UniqueConstraint("agent_id", "jour", "tranche_id", name="_affectation_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    tranche_id = Column(Integer, ForeignKey("tranches.id"), nullable=False)
    jour = Column(Date, nullable=False)

    agent = relationship("Agent", back_populates="affectations")
    tranche = relationship("Tranche", back_populates="affectations")

    def __repr__(self):
        return f"<Affectation agent={self.agent_id} tranche={self.tranche_id} jour={self.jour}>"


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


# =====================================================
#   Qualification
# =====================================================
class Qualification(Base):
    __tablename__ = "qualifications"
    __table_args__ = (UniqueConstraint("agent_id", "poste_id", name="_qualification_uc"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    poste_id = Column(Integer, ForeignKey("postes.id"), nullable=False)
    date_qualification = Column(Date, nullable=True)

    agent = relationship("Agent", back_populates="qualifications")
    poste = relationship("Poste", back_populates="qualifications")

    def __repr__(self):
        return f"<Qualification agent={self.agent_id} poste={self.poste_id}>"


# =====================================================
#   Régime
# =====================================================
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
