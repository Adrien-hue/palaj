from backend.app.dto.qualifications import QualificationDTO

def to_qualification_dto(q) -> QualificationDTO:
    return QualificationDTO(
        agent_id=q.agent_id,
        poste_id=q.poste_id,
        date_qualification=q.date_qualification,
    )
