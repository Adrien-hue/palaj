from fastapi import APIRouter, Depends, HTTPException
from backend.app.api.deps import get_agent_service
from backend.app.dto.agents import AgentDetailDTO, AgentListDTO
from backend.app.mappers.agents import to_agent_detail_dto, to_agent_list_item_dto
from core.application.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/{agent_id}", response_model=AgentDetailDTO)
def get_agent(agent_id: int, agent_service: AgentService = Depends(get_agent_service)) -> AgentDetailDTO:
    agent = agent_service.get_agent_complet(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return to_agent_detail_dto(agent)

@router.get("", response_model=AgentListDTO)
def list_agents(
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentListDTO:
    agents = agent_service.list_all()
    return AgentListDTO(
        items=[to_agent_list_item_dto(a) for a in agents],
        total=len(agents),
    )
