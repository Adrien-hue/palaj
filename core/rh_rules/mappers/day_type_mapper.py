from __future__ import annotations

from core.domain.entities import TypeJour
from core.domain.enums.day_type import DayType

def day_type_from_type_jour(t: TypeJour) -> DayType:
    if t == TypeJour.POSTE:
        return DayType.WORKING
    if t == TypeJour.ZCOT:
        return DayType.ZCOT
    if t == TypeJour.REPOS:
        return DayType.REST
    if t == TypeJour.CONGE:
        return DayType.LEAVE
    if t == TypeJour.ABSENCE:
        return DayType.ABSENT

    # fallback pour INCONNU / autres
    return DayType.UNKNOWN
