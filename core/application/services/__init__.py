# core/application/services/__init__.py
from core.application.config.rh_rules_config import build_default_rh_engine

from core.application.services.affectation_service import AffectationService
from core.application.services.agent_service import AgentService
from core.application.services.agent_planning_validator_service import AgentPlanningValidatorService
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

rh_engine = build_default_rh_engine()

affectation_service = AffectationService(affectation_repo, agent_repo, tranche_repo)
agent_service = AgentService(agent_repo, affectation_repo, etat_jour_agent_repo, regime_repo, qualification_repo)
agent_planning_validator_service = AgentPlanningValidatorService(rh_engine)
etat_jour_agent_service = EtatJourAgentService(etat_jour_agent_repo, affectation_repo, agent_repo)
planning_builder_service = PlanningBuilderService(agent_repo, affectation_repo, etat_jour_agent_repo, tranche_repo)
poste_service = PosteService(poste_repo, tranche_repo, qualification_repo)
qualification_service = QualificationService(qualification_repo, agent_repo, poste_repo)
regime_service = RegimeService(agent_repo, regime_repo)
tranche_service = TrancheService(tranche_repo, poste_repo)


__all__ = [
    "affectation_service",
    "agent_service",
    "agent_planning_validator_service",
    "etat_jour_agent_service",
    "planning_builder_service",
    "poste_service",
    "qualification_service",
    "regime_service",
    "tranche_service",
]