from fastapi import APIRouter, Depends, HTTPException
from typing import List

from backend.app.api.deps import get_agent_planning_factory, get_agent_planning_validator_service
from backend.app.dto.rh import RHValidateAgentRequestDTO
from backend.app.dto.rh_validation_result import RhValidationResultDTO
from backend.app.mappers.rh_validation_result import rh_validation_result_to_dto

from core.application.services.planning.agent_planning_factory import AgentPlanningFactory
from core.application.services.agent_planning_validator_service import AgentPlanningValidatorService

router = APIRouter(prefix="/rh", tags=["RH"])

@router.post("/validate/agent", response_model=RhValidationResultDTO)
def validate_agent(
    payload: RHValidateAgentRequestDTO,
    agent_planning_factory: AgentPlanningFactory = Depends(get_agent_planning_factory),
    validator: AgentPlanningValidatorService = Depends(get_agent_planning_validator_service),
) -> RhValidationResultDTO:

    if payload.date_debut > payload.date_fin:
        raise HTTPException(status_code=422, detail="date_debut must be <= date_fin")

    try:
        planning = agent_planning_factory.build(
            agent_id=payload.agent_id,
            start_date=payload.date_debut,
            end_date=payload.date_fin,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = validator.validate(planning)

    return rh_validation_result_to_dto(result)
