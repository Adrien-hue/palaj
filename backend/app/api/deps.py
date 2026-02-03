# backend/app/api/deps.py
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from db import db
from db.models import User

from backend.app.bootstrap.container import (
    agent_day_service,
    agent_service,
    agent_planning_validator_service,
    agent_planning_factory,
    agent_team_service,
    planning_day_assembler,
    poste_coverage_requirement_service,
    poste_planning_factory,
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
    PosteCoverageRequirementService,
    PosteService,
    QualificationService,
    RegimeService,
    TeamPlanningFactory,
    TeamService,
    TrancheService,
)

from backend.app.security.jwt import decode_token
from backend.app.settings import settings


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

def get_agent_planning_validator_service() -> AgentPlanningValidatorService:
    return agent_planning_validator_service

def get_planning_day_assembler() -> PlanningDayAssembler:
    return planning_day_assembler

def get_poste_planning_factory() -> PostePlanningFactory:
    return poste_planning_factory

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

def current_user(request: Request, session: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = session.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_role(*roles: str):
    def guard(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user
    return guard
