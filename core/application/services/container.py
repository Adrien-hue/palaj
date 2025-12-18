# core/application/services/container.py

from core.application.services.affectation_service import AffectationService
from core.application.services.agent_service import AgentService
from core.application.services.etat_jour_agent_service import EtatJourAgentService
from core.application.services.planning.planning_builder_service import PlanningBuilderService
from core.application.services.poste_service import PosteService
from core.application.services.qualification_service import QualificationService
from core.application.services.regime_service import RegimeService
from core.application.services.tranche_service import TrancheService

from db.repositories import (
    agent_repo,
    affectation_repo,
    etat_jour_agent_repo,
    poste_repo,
    qualification_repo,
    regime_repo,
    tranche_repo,
)

# ---------------------------------------------------------
# Repositories -> Services
# ---------------------------------------------------------
affectation_service = AffectationService(affectation_repo, agent_repo, tranche_repo)
agent_service = AgentService(agent_repo, affectation_repo, etat_jour_agent_repo, regime_repo, qualification_repo)
etat_jour_agent_service = EtatJourAgentService(etat_jour_agent_repo, affectation_repo, agent_repo)
poste_service = PosteService(poste_repo, tranche_repo, qualification_repo)
qualification_service = QualificationService(qualification_repo, agent_repo, poste_repo)
regime_service = RegimeService(agent_repo, regime_repo)
tranche_service = TrancheService(tranche_repo, poste_repo)

# ---------------------------------------------------------
# Services -> Services
# ---------------------------------------------------------
planning_builder_service = PlanningBuilderService(
    affectation_service=affectation_service,
    agent_service=agent_service,
    etat_service=etat_jour_agent_service,
    poste_service=poste_service,
    tranche_service=tranche_service,
)

__all__ = [
    "affectation_service",
    "agent_service",
    "etat_jour_agent_service",
    "poste_service",
    "qualification_service",
    "regime_service",
    "tranche_service",
    "planning_builder_service",
]
