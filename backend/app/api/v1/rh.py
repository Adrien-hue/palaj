from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.app.api.deps import get_planning_builder_service, get_agent_planning_validator_service
from backend.app.dto.rh import RHValidateAgentRequestDTO
from backend.app.dto.common.alerts import DomainAlertDTO
from backend.app.mappers.common.alerts import to_domain_alert_dto

from core.application.services.planning.planning_builder_service import PlanningBuilderService
from core.application.services.agent_planning_validator_service import AgentPlanningValidatorService

router = APIRouter(prefix="/rh", tags=["RH"])

@router.post("/validate/agent", response_model=List[DomainAlertDTO])
def validate_agent(
    payload: RHValidateAgentRequestDTO,
    planning_builder: PlanningBuilderService = Depends(get_planning_builder_service),
    validator: AgentPlanningValidatorService = Depends(get_agent_planning_validator_service),
) -> List[DomainAlertDTO]:

    if payload.date_debut > payload.date_fin:
        raise HTTPException(status_code=422, detail="date_debut must be <= date_fin")

    try:
        planning = planning_builder.build_agent_planning(
            agent_id=payload.agent_id,
            start_date=payload.date_debut,
            end_date=payload.date_fin,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    _, alerts = validator.validate(planning)

    return [to_domain_alert_dto(a) for a in alerts]
