from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.api.deps import get_agent_service, get_agent_planning_factory
from backend.app.dto.agents import AgentCreateDTO, AgentDTO, AgentDetailDTO, AgentUpdateDTO
from backend.app.dto.common.pagination import build_page, Page, PaginationParams, pagination_params
from backend.app.dto.planning import AgentPlanningResponseDTO
from backend.app.mappers.agents import to_agent_dto, to_agent_detail_dto
from backend.app.mappers.planning import to_agent_planning_response
from core.application.services.agent_service import AgentService
from core.application.services.planning.agent_planning_factory import AgentPlanningFactory

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