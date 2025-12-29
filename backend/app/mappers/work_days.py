from backend.app.dto.work_days import WorkDayDTO

from backend.app.mappers.etats_jours_agents import to_etat_jour_agent_dto
from backend.app.mappers.tranches import to_tranche_dto

def to_work_day_dto(wd) -> WorkDayDTO:
    etat_dto = to_etat_jour_agent_dto(wd.etat) if getattr(wd, "etat", None) is not None else None
    tranches = [to_tranche_dto(t) for t in (wd.tranches or [])]

    return WorkDayDTO(
        jour=wd.jour,
        etat=etat_dto,
        tranches=tranches,
    )