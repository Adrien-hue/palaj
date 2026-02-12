# backend/app/api/deps.py
from collections.abc import Generator
from typing import Annotated

from fastapi.params import Depends, Query
from sqlalchemy.orm import Session

from core.application.config.rh_rules_config import RhEngineProfile, build_rh_engine
from core.rh_rules.rh_rules_engine import RHRulesEngine
from db import db

from backend.app.bootstrap.container import (
    agent_day_service,
    agent_service,
    agent_planning_factory,
    agent_team_service,
    planning_day_assembler,
    poste_coverage_requirement_service,
    poste_planning_factory,
    poste_planning_day_assembler,
    poste_planning_day_service,
    poste_service,
    qualification_service,
    regime_service,
    team_service,
    team_planning_factory,
    tranche_service,
)
from core.application.services import (
    AgentDayService,
    AgentService,
    AgentTeamService,
    AgentPlanningFactory,
    AgentPlanningValidatorService,
    PlanningDayAssembler,
    PostePlanningFactory,
    PostePlanningDayAssembler,
    PostePlanningDayService,
    PosteCoverageRequirementService,
    PosteService,
    QualificationService,
    RegimeService,
    TeamPlanningFactory,
    TeamService,
    TrancheService,
)

def get_db() -> Generator[Session, None, None]:
    # Une session par requête HTTP, commit/rollback gérés automatiquement
    with db.session_scope() as session:
        yield session

def get_agent_day_service() -> AgentDayService:
    return agent_day_service

def get_agent_service() -> AgentService:
    return agent_service

def get_agent_team_service() -> AgentTeamService:
    return agent_team_service

def get_agent_planning_factory() -> AgentPlanningFactory:
    return agent_planning_factory

def get_rh_profile(
    profile: Annotated[RhEngineProfile, Query()] = RhEngineProfile.FULL
) -> RhEngineProfile:
    try:
        return RhEngineProfile(profile)
    except ValueError:
        return RhEngineProfile.FULL

def get_rh_rules_engine(
    profile: Annotated[RhEngineProfile, Query()] = RhEngineProfile.FULL,
) -> RHRulesEngine:
    return build_rh_engine(profile.value)

def get_agent_planning_validator_service(
    engine: Annotated[RHRulesEngine, Depends(get_rh_rules_engine)],
) -> AgentPlanningValidatorService:
    return AgentPlanningValidatorService(rh_rules_engine=engine)

def get_planning_day_assembler() -> PlanningDayAssembler:
    return planning_day_assembler

def get_poste_planning_factory() -> PostePlanningFactory:
    return poste_planning_factory

def get_poste_planning_day_assembler() -> PostePlanningDayAssembler:
    return poste_planning_day_assembler

def get_poste_planning_day_service() -> PostePlanningDayService:
    return poste_planning_day_service

def get_poste_service() -> PosteService:
    return poste_service

def get_poste_coverage_requirement_service() -> PosteCoverageRequirementService:
    return poste_coverage_requirement_service

def get_qualification_service() -> QualificationService:
    return qualification_service

def get_regime_service() -> RegimeService:
    return regime_service

def get_team_service() -> TeamService:
    return team_service

def get_team_planning_factory() -> TeamPlanningFactory:
    return team_planning_factory

def get_tranche_service() -> TrancheService:
    return tranche_service