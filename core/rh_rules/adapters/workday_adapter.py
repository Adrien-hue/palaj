from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from core.domain.models.work_day import WorkDay
from core.domain.entities.tranche import Tranche
from core.rh_rules.models.rh_day import RhDay, RhInterval


def _interval_from_tranche(day_date, t: Tranche) -> RhInterval:
    start = datetime.combine(day_date, t.heure_debut)
    end = datetime.combine(day_date, t.heure_fin)

    # Passage minuit
    if t.heure_fin <= t.heure_debut:
        end = end + timedelta(days=1)

    return RhInterval(
        start=start,
        end=end,
        tranche_id=t.id,
        poste_id=t.poste_id,
    )


def rh_day_from_workday(agent_id: int, wd: WorkDay) -> RhDay:
    intervals: List[RhInterval] = []
    for t in (wd.tranches or []):
        intervals.append(_interval_from_tranche(wd.jour, t))

    return RhDay(
        agent_id=agent_id,
        day_date=wd.jour,
        intervals=intervals,
        day_type=str(wd.type().value) if hasattr(wd.type(), "value") else str(wd.type()),
    )
