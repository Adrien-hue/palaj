from backend.app.dto.agents import AgentDTO

def to_agent_list_item_dto(agent) -> AgentDTO:
    return AgentDTO(
        id=agent.id,
        nom=agent.nom,
        prenom=agent.prenom,
        code_personnel=agent.code_personnel,
        actif=getattr(agent, "actif", True),
    )
