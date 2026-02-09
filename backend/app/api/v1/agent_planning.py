from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status

from backend.app.api.deps import (
    get_agent_day_service,
    get_agent_planning_factory,
    get_planning_day_assembler,
)
from backend.app.api.http_exceptions import bad_request
from backend.app.dto.planning import AgentPlanningResponseDTO
from backend.app.dto.planning_day import (
    AgentPlanningDayBulkPutDTO,
    AgentPlanningDayBulkPutResponseDTO,
    AgentsPlanningDayRequestDTO,
    AgentsPlanningDaysBatchResponseDTO,
    BulkFailedItem,
    PlanningDayDTO,
    PlanningDayPutDTO,
)
from backend.app.mappers.planning import to_agent_planning_response
from backend.app.mappers.planning_day import to_agent_planning_day_dto, to_planning_day_dto
from core.application.services import AgentDayService, AgentPlanningFactory, PlanningDayAssembler

router = APIRouter(prefix="/agents", tags=["Agent planning"])


@router.post("/planning/days/batch", response_model=AgentsPlanningDaysBatchResponseDTO)
def get_planning_days_for_agents(
    payload: AgentsPlanningDayRequestDTO,
    planning_day_assembler: PlanningDayAssembler = Depends(get_planning_day_assembler),
):
    by_agent = planning_day_assembler.build_for_agents_day(
        agent_ids=payload.agent_ids,
        day_date=payload.day_date,
    )

    # garder l'ordre d'entrée
    items = [
        to_agent_planning_day_dto(aid, by_agent[aid])
        for aid in payload.agent_ids
        if aid in by_agent
    ]

    return AgentsPlanningDaysBatchResponseDTO(day_date=payload.day_date, items=items)


@router.get("/{agent_id}/planning", response_model=AgentPlanningResponseDTO)
def get_agent_planning(
    agent_id: int,
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date: date = Query(..., description="YYYY-MM-DD"),
    agent_planning_factory: AgentPlanningFactory = Depends(get_agent_planning_factory),
):
    try:
        planning = agent_planning_factory.build(agent_id=agent_id, start_date=start_date, end_date=end_date)
        return to_agent_planning_response(planning)
    except ValueError as e:
        bad_request(str(e))


@router.put("/{agent_id}/planning/days/{day_date}", response_model=PlanningDayDTO)
def upsert_agent_planning_day(
    agent_id: int,
    day_date: date,
    payload: PlanningDayPutDTO,
    agent_day_service: AgentDayService = Depends(get_agent_day_service),
    planning_day_assembler: PlanningDayAssembler = Depends(get_planning_day_assembler),
):
    try:
        agent_day_service.upsert_day(
            agent_id=agent_id,
            day_date=day_date,
            day_type=payload.day_type,
            tranche_id=payload.tranche_id,
            description=payload.description,
        )

        planning_day = planning_day_assembler.build_one_for_agent(agent_id=agent_id, day_date=day_date)
        return to_planning_day_dto(planning_day)
    except ValueError as e:
        bad_request(str(e))


@router.delete("/{agent_id}/planning/days/{day_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_planning_day(
    agent_id: int,
    day_date: date,
    agent_day_service: AgentDayService = Depends(get_agent_day_service),
):
    try:
        agent_day_service.delete_day(agent_id=agent_id, day_date=day_date)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        bad_request(str(e))


@router.put("/{agent_id}/planning/days:bulk", response_model=AgentPlanningDayBulkPutResponseDTO)
def bulk_upsert_agent_planning_days(
    agent_id: int,
    payload: AgentPlanningDayBulkPutDTO,
    agent_day_service: AgentDayService = Depends(get_agent_day_service),
    planning_day_assembler: PlanningDayAssembler = Depends(get_planning_day_assembler),
):
    updated = []
    failed = []

    for day_date in payload.day_dates:
        try:
            agent_day_service.upsert_day(
                agent_id=agent_id,
                day_date=day_date,
                day_type=payload.day_type,
                tranche_id=payload.tranche_id,
                description=payload.description,
            )

            planning_day = planning_day_assembler.build_one_for_agent(agent_id=agent_id, day_date=day_date)
            updated.append(to_planning_day_dto(planning_day))

        except ValueError as e:
            failed.append(BulkFailedItem(day_date=day_date, code="VALIDATION_ERROR", message=str(e)))
        except Exception as e:
            failed.append(BulkFailedItem(day_date=day_date, code="UNEXPECTED_ERROR", message=str(e)))

    return AgentPlanningDayBulkPutResponseDTO(updated=updated, failed=failed)
