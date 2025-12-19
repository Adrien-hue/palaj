from backend.app.dto.affectations import AffectationDTO

def to_affectation_dto(a) -> AffectationDTO:
    return AffectationDTO(
        agent_id=a.agent_id,
        tranche_id=a.tranche_id,
        jour=a.jour,
    )
