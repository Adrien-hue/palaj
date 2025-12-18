# backend/app/bootstrap/container.py
from core.application.services import (
    AffectationService,
    AgentService,
    EtatJourAgentService,
    PlanningBuilderService,
    PosteService,
    QualificationService,
    RegimeService,
    TrancheService,
)

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
affectation_service = AffectationService(
    affectation_repo=affectation_repo, 
    agent_repo=agent_repo, 
    tranche_repo=tranche_repo
)

agent_service = AgentService(
    affectation_repo=affectation_repo,
    agent_repo=agent_repo,
    etat_jour_agent_repo=etat_jour_agent_repo,
    qualification_repo=qualification_repo,
    regime_repo=regime_repo,
)

etat_jour_agent_service = EtatJourAgentService(
    affectation_repo=affectation_repo, 
    agent_repo=agent_repo,
    etat_jour_agent_repo=etat_jour_agent_repo, 
)

poste_service = PosteService(
    poste_repo=poste_repo,
    qualification_repo=qualification_repo,
    tranche_repo=tranche_repo,
)

qualification_service = QualificationService(
    agent_repo=agent_repo,
    poste_repo=poste_repo,
    qualification_repo=qualification_repo,
)

regime_service = RegimeService(
    agent_repo=agent_repo,
    regime_repo=regime_repo,
)

tranche_service = TrancheService(
    poste_repo=poste_repo,
    tranche_repo=tranche_repo,
)

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
