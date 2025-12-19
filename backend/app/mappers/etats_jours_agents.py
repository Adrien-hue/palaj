from backend.app.dto.etats_jours_agents import EtatJourAgentDTO

def to_etat_jour_agent_dto(e) -> EtatJourAgentDTO:
    # type_jour est un Enum TypeJour côté domaine -> string côté API
    type_jour_str = e.type_jour.value if hasattr(e.type_jour, "value") else str(e.type_jour)

    return EtatJourAgentDTO(
        agent_id=e.agent_id,
        jour=e.jour,
        type_jour=type_jour_str,
        description=e.description or "",
    )
