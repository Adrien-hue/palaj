from backend.app.dto.agents import AgentDTO, AgentDetailDTO

from backend.app.mappers.regimes import to_regime_dto
from backend.app.mappers.qualifications import to_qualification_dto
from backend.app.mappers.affectations import to_affectation_dto
from backend.app.mappers.etats_jours_agents import to_etat_jour_agent_dto

def to_agent_list_item_dto(agent) -> AgentDTO:
    return AgentDTO(
        id=agent.id,
        nom=agent.nom,
        prenom=agent.prenom,
        code_personnel=agent.code_personnel,
        actif=agent.actif,
    )

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
        affectations=[to_affectation_dto(a) for a in agent.affectations],
        etat_jours=[to_etat_jour_agent_dto(e) for e in agent.etat_jours],
    )