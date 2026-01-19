from backend.app.dto.agents import AgentDetailDTO

from backend.app.mappers.regimes_light import to_regime_dto
from backend.app.mappers.qualifications import to_qualification_dto

def to_agent_detail_dto(agent) -> AgentDetailDTO:
    return AgentDetailDTO(
        id=agent.id,
        nom=agent.nom,
        prenom=agent.prenom,
        code_personnel=agent.code_personnel,
        actif=agent.actif,
        regime_id=agent.regime_id,
        regime=to_regime_dto(agent.regime) if agent.regime else None,
        qualifications=[to_qualification_dto(q) for q in agent.qualifications],
    )