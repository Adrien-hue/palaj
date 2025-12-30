from core.domain.models.agent_day import AgentDay
from backend.app.dto.agent_days import AgentDayDTO
from backend.app.dto.tranches import TrancheDTO

def to_agent_day_dto(day: AgentDay) -> AgentDayDTO:
    return AgentDayDTO(
        date=day.date,
        day_type=day.day_type.value,
        description=day.description,
        is_off_shift=day.is_off_shift,
        shifts=[
            TrancheDTO(
                id=s.id,
                nom=s.nom,
                heure_debut=s.heure_debut,
                heure_fin=s.heure_fin,
                poste_id=s.poste_id,
            )
            for s in day.shifts
        ],
    )
