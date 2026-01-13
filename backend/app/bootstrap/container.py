# backend/app/bootstrap/container.py
from core.application.config.rh_rules_config import build_default_rh_engine

from core.application.services import (
    AffectationService,
    AgentPlanningValidatorService,
    AgentService,
    EtatJourAgentService,
    AgentPlanningFactory,
    PlanningBuilderService,
    PlanningDayAssembler,
    PosteService,
    QualificationService,
    RegimeService,
    TrancheService,
)

from db.repositories import (
    agent_repo,
    agent_day_repo,
    affectation_repo,
    etat_jour_agent_repo,
    poste_repo,
    qualification_repo,
    regime_repo,
    tranche_repo,
)

from backend.app.settings import settings

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
# RH / Validation
# ---------------------------------------------------------
rh_rules_engine = build_default_rh_engine()
agent_planning_validator_service = AgentPlanningValidatorService(
    rh_rules_engine=rh_rules_engine
)

# ---------------------------------------------------------
# Planning
# ---------------------------------------------------------
planning_day_assembler = PlanningDayAssembler(
    agent_day_repo=agent_day_repo,
    tranche_repo=tranche_repo,
)

agent_planning_factory = AgentPlanningFactory(
    agent_service=agent_service,
    planning_day_assembler=planning_day_assembler,
)

planning_builder_service = PlanningBuilderService(
    affectation_service=affectation_service,
    agent_service=agent_service,
    etat_service=etat_jour_agent_service,
    poste_service=poste_service,
    tranche_service=tranche_service,
    planning_day_assembler=planning_day_assembler,
    enable_agent_day_db_read=settings.FEATURE_AGENT_DAY_READ_DB,
)

__all__ = [
    "affectation_service",
    "agent_service",
    "etat_jour_agent_service",
    "poste_service",
    "qualification_service",
    "regime_service",
    "tranche_service",
    "rh_rules_engine",
    "agent_planning_validator_service",
    "planning_builder_service",
]
