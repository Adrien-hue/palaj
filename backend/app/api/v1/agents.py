from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from backend.app.api.deps import get_agent_day_service, get_agent_service, get_agent_planning_factory, get_planning_day_assembler
from backend.app.dto.agents import AgentCreateDTO, AgentDTO, AgentDetailDTO, AgentUpdateDTO
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.planning import AgentPlanningResponseDTO
from backend.app.dto.planning_day import AgentPlanningDayBulkPutResponseDTO, PlanningDayDTO, PlanningDayPutDTO, AgentPlanningDayBulkPutDTO, BulkFailedItem, AgentsPlanningDayRequestDTO, AgentsPlanningDaysBatchResponseDTO
from backend.app.mappers.agents_light import to_agent_dto
from backend.app.mappers.agents import to_agent_detail_dto
from backend.app.mappers.planning import to_agent_planning_response
from backend.app.mappers.planning_day import to_agent_planning_day_dto, to_planning_day_dto

from core.application.services import (
    AgentDayService,
    AgentPlanningFactory,
    AgentService,
    PlanningDayAssembler,
)

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.patch("/{agent_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
def activate_agent(agent_id: int, agent_service: AgentService = Depends(get_agent_service)):
    ok = agent_service.activate(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None

@router.post("/", response_model=AgentDTO, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreateDTO, agent_service: AgentService = Depends(get_agent_service)):
    agent = agent_service.create(**payload.model_dump())
    return to_agent_dto(agent)

@router.patch("/{agent_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_agent(agent_id: int, agent_service: AgentService = Depends(get_agent_service)):
    ok = agent_service.deactivate(agent_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agent not found")
    return None

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: int, agent_service: AgentService = Depends(get_agent_service)):
    try:
        ok = agent_service.delete(agent_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Agent not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{agent_id}", response_model=AgentDetailDTO)
def get_agent(agent_id: int, agent_service: AgentService = Depends(get_agent_service)) -> AgentDetailDTO:
    agent = agent_service.get_agent_complet(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return to_agent_detail_dto(agent)

@router.get("/", response_model=Page[AgentDTO])
def list_agents(
    agent_service: AgentService = Depends(get_agent_service),
    p: PaginationParams = Depends(pagination_params)
):
    items = agent_service.list(limit=p.limit, offset=p.offset)
    total = agent_service.count()
    return build_page(items=items, total=total, p=p)

@router.patch("/{agent_id}", response_model=AgentDTO)
def update_agent(agent_id: int, payload: AgentUpdateDTO, agent_service: AgentService = Depends(get_agent_service)):
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")

    agent = agent_service.update(agent_id, **changes)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return to_agent_dto(agent)

# Planning-related endpoints

@router.post(
    "/planning/days/batch",
    response_model=AgentsPlanningDaysBatchResponseDTO,
    status_code=status.HTTP_200_OK,
)
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

    return AgentsPlanningDaysBatchResponseDTO(
        day_date=payload.day_date,
        items=items,
    )

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
        raise HTTPException(status_code=400, detail=str(e))

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
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{agent_id}/planning/days/{day_date}", response_model=PlanningDayDTO)
def upsert_agent_planning_day(
    agent_id: int,
    day_date: date,
    payload: PlanningDayPutDTO,
    agent_day_service: AgentDayService = Depends(get_agent_day_service),
    planning_day_assembler: PlanningDayAssembler = Depends(get_planning_day_assembler),
):
    try:
        day = agent_day_service.upsert_day(
            agent_id=agent_id,
            day_date=day_date,
            day_type=payload.day_type,
            tranche_id=payload.tranche_id,
            description=payload.description,
        )

        planning_day = planning_day_assembler.build_one_for_agent(agent_id=agent_id, day_date=day_date)
        return to_planning_day_dto(planning_day)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.put(
    "/{agent_id}/planning/days:bulk",
    response_model=AgentPlanningDayBulkPutResponseDTO,
)
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

            planning_day = planning_day_assembler.build_one_for_agent(
                agent_id=agent_id,
                day_date=day_date,
            )
            updated.append(to_planning_day_dto(planning_day))

        except ValueError as e:
            failed.append(
                BulkFailedItem(
                    day_date=day_date,
                    code="VALIDATION_ERROR",
                    message=str(e),
                )
            )
        except Exception as e:
            failed.append(
                BulkFailedItem(
                    day_date=day_date,
                    code="UNEXPECTED_ERROR",
                    message=str(e),
                )
            )

    return AgentPlanningDayBulkPutResponseDTO(updated=updated, failed=failed)