from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated, List, Tuple

from backend.app.api.deps import get_agent_planning_factory, get_agent_planning_validator_service, get_qualification_service
from backend.app.dto.rh.rh_request import RHValidateAgentRequestDTO, RHValidatePosteDayRequestDTO, RHValidatePosteRequestDTO
from backend.app.dto.rh.rh_validation_day_details import RhValidationPosteDayDetailsDTO
from backend.app.dto.rh.rh_validation_result import RhValidationAgentResultDTO
from backend.app.dto.rh.rh_validation_summary import RhValidationPosteSummaryDTO
from backend.app.mappers.rh.rh_validation_day_details import to_poste_day_details_dto
from backend.app.mappers.rh.rh_validation_summary import to_poste_summary_dto
from backend.app.mappers.rh.rh_validation_result import rh_validation_result_to_dto

from core.application.config.rh_rules_config import RhEngineProfile
from core.application.services.planning.agent_planning_factory import AgentPlanningFactory
from core.application.services.agent_planning_validator_service import AgentPlanningValidatorService
from core.application.services.qualification_service import QualificationService
from core.rh_rules.models.rule_result import RuleResult

router = APIRouter(prefix="/rh", tags=["RH"])

@router.post("/validate/agent", response_model=RhValidationAgentResultDTO)
def validate_agent(
    payload: RHValidateAgentRequestDTO,
    profile: Annotated[RhEngineProfile, Query()] = RhEngineProfile.FULL,
    agent_planning_factory: AgentPlanningFactory = Depends(get_agent_planning_factory),
    validator: AgentPlanningValidatorService = Depends(get_agent_planning_validator_service),
) -> RhValidationAgentResultDTO:

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

    # le validator injecté doit utiliser le profile de la requête
    result = validator.validate(planning)

    return rh_validation_result_to_dto(result)

@router.post("/validate/poste/day", response_model=RhValidationPosteDayDetailsDTO)
def validate_poste_day(
    payload: RHValidatePosteDayRequestDTO,
    profile: Annotated[RhEngineProfile, Query()] = RhEngineProfile.FAST,
    include_info: Annotated[bool, Query()] = False,
    agent_planning_factory: AgentPlanningFactory = Depends(get_agent_planning_factory),
    validator: AgentPlanningValidatorService = Depends(get_agent_planning_validator_service),
    qualification_service: QualificationService = Depends(get_qualification_service),
) -> RhValidationPosteDayDetailsDTO:
    if payload.date_debut > payload.date_fin:
        raise HTTPException(status_code=422, detail="date_debut must be <= date_fin")

    if not (payload.date_debut <= payload.day <= payload.date_fin):
        raise HTTPException(status_code=422, detail="day must be within [date_debut, date_fin]")

    qualifications = qualification_service.search(poste_id=payload.poste_id)
    qualified_agent_ids = [q.agent_id for q in qualifications]

    # padding backend-only
    pad = timedelta(days=31)
    window_start = payload.date_debut - pad
    window_end = payload.date_fin + pad

    per_agent_results: List[Tuple[int, RuleResult]] = []

    for agent_id in qualified_agent_ids:
        planning = agent_planning_factory.build(
            agent_id=agent_id,
            start_date=payload.date_debut,
            end_date=payload.date_fin,
        )
        result = validator.validate(planning, window_start=window_start, window_end=window_end)
        per_agent_results.append((agent_id, result))

    return to_poste_day_details_dto(
        poste_id=payload.poste_id,
        day=payload.day,
        profile=profile,
        qualified_agent_ids=qualified_agent_ids,
        per_agent_results=per_agent_results,
        include_info=include_info,
    )


@router.post("/validate/poste/summary", response_model=RhValidationPosteSummaryDTO)
def validate_poste_summary(
    payload: RHValidatePosteRequestDTO,
    profile: Annotated[RhEngineProfile, Query()] = RhEngineProfile.FULL,
    agent_planning_factory: AgentPlanningFactory = Depends(get_agent_planning_factory),
    validator: AgentPlanningValidatorService = Depends(get_agent_planning_validator_service),
    qualification_service: QualificationService = Depends(get_qualification_service),
) -> RhValidationPosteSummaryDTO:
    if payload.date_debut > payload.date_fin:
        raise HTTPException(status_code=422, detail="date_debut must be <= date_fin")

    qualifications = qualification_service.search(poste_id=payload.poste_id)
    qualified_agent_ids = [q.agent_id for q in qualifications]

    if not qualified_agent_ids:
        return to_poste_summary_dto(
            poste_id=payload.poste_id,
            start=payload.date_debut,
            end=payload.date_fin,
            profile=profile,
            qualified_agent_ids=[],
            per_agent_results=[],
        )

    per_agent_results: List[Tuple[int, RuleResult]] = []

    pad = timedelta(days=31)
    window_start = payload.date_debut - pad
    window_end = payload.date_fin + pad

    for agent_id in qualified_agent_ids:
        planning = agent_planning_factory.build(
            agent_id=agent_id,
            start_date=payload.date_debut,
            end_date=payload.date_fin,
        )

        result = validator.validate(planning, window_start=window_start, window_end=window_end)
        per_agent_results.append((agent_id, result))

    return to_poste_summary_dto(
        poste_id=payload.poste_id,
        start=payload.date_debut,
        end=payload.date_fin,
        profile=profile,
        qualified_agent_ids=qualified_agent_ids,
        per_agent_results=per_agent_results,
    )