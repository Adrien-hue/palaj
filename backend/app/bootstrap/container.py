# backend/app/bootstrap/container.py
from core.application.config.rh_rules_config import build_default_rh_engine

from core.application.services import (
    AgentPlanningValidatorService,
    AgentService,
    AgentPlanningFactory,
    PlanningDayAssembler,
    PostePlanningFactory,
    PostePlanningDayAssembler,
    PosteService,
    QualificationService,
    RegimeService,
    TrancheService,
)

from db.repositories import (
    agent_repo,
    agent_day_repo,
    agent_day_assignment_repo,
    affectation_repo,
    poste_repo,
    qualification_repo,
    regime_repo,
    tranche_repo,
)

from backend.app.settings import settings

# ---------------------------------------------------------
# Repositories -> Services
# ---------------------------------------------------------

agent_service = AgentService(
    affectation_repo=affectation_repo,
    agent_repo=agent_repo,
    agent_day_repo=agent_day_repo,
    qualification_repo=qualification_repo,
    regime_repo=regime_repo,
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
    agent_day_assignment_repo=agent_day_assignment_repo
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

poste_planning_day_assembler = PostePlanningDayAssembler()

agent_planning_factory = AgentPlanningFactory(
    agent_service=agent_service,
    planning_day_assembler=planning_day_assembler,
)

poste_planning_factory = PostePlanningFactory(
    poste_repo=poste_repo,
    tranche_repo=tranche_repo,
    agent_repo=agent_repo,
    agent_day_repo=agent_day_repo,
    day_assembler=poste_planning_day_assembler
)

__all__ = [
    "agent_service",
    "poste_service",
    "qualification_service",
    "regime_service",
    "tranche_service",
    "rh_rules_engine",
    "agent_planning_validator_service",
    "agent_planning_factory",
    "poste_planning_factory",
]
