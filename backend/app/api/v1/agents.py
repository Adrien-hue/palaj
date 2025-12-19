from fastapi import APIRouter, Depends
from backend.app.api.deps import get_agent_service
from backend.app.dto.agents import AgentListDTO
from backend.app.mappers.agents import to_agent_list_item_dto
from core.application.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("", response_model=AgentListDTO)
def list_agents(
    agent_service: AgentService = Depends(get_agent_service),
) -> AgentListDTO:
    agents = agent_service.list_all()
    return AgentListDTO(
        items=[to_agent_list_item_dto(a) for a in agents],
        total=len(agents),
    )
