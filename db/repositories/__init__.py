# db/repositories/__init__.py
from db.repositories.agent_repo import AgentRepository
from db.repositories.agent_day_repo import AgentDayRepository
from db.repositories.poste_repo import PosteRepository
from db.repositories.tranche_repo import TrancheRepository
from db.repositories.regime_repo import RegimeRepository
from db.repositories.affectation_repo import AffectationRepository
from db.repositories.etat_jour_agent_repo import EtatJourAgentRepository
from db.repositories.qualification_repo import QualificationRepository

agent_repo = AgentRepository()
agent_day_repo = AgentDayRepository()
poste_repo = PosteRepository()
tranche_repo = TrancheRepository()
regime_repo = RegimeRepository()
affectation_repo = AffectationRepository()
etat_jour_agent_repo = EtatJourAgentRepository()
qualification_repo = QualificationRepository()

__all__ = [
    "agent_repo",
    "agent_day_repo",
    "poste_repo",
    "tranche_repo",
    "regime_repo",
    "affectation_repo",
    "etat_jour_agent_repo",
    "qualification_repo",
]