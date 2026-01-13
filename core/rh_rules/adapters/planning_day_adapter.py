# core/rh_rules/adapters/planning_day_adapter.py
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from core.domain.models.planning_day import PlanningDay
from core.rh_rules.contexts.rh_context import RhContext
from core.rh_rules.models.rh_day import RhDay
from core.rh_rules.models.rh_interval import RhInterval


def rh_day_from_planning_day(agent_id: int, pd: PlanningDay) -> RhDay:
    intervals: list[RhInterval] = []

    for t in (pd.tranches or []):
        start_dt = datetime.combine(pd.day_date, t.heure_debut)
        end_dt = datetime.combine(pd.day_date, t.heure_fin)

        # tranche crossing midnight
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        intervals.append(
            RhInterval(
                start=start_dt,
                end=end_dt,
                tranche_id=getattr(t, "id", None),
                poste_id=getattr(t, "poste_id", None),
            )
        )

    return RhDay(
        agent_id=agent_id,
        day_date=pd.day_date,
        day_type=pd.day_type,
        intervals=intervals,
    )


def rh_context_from_planning_days(
    *,
    agent,
    days: Iterable[PlanningDay],
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
) -> RhContext:
    rh_days = [rh_day_from_planning_day(agent.id, pd) for pd in days]

    rh_days.sort(key=lambda d: d.day_date)

    return RhContext(
        agent=agent,
        days=tuple(rh_days),
        window_start=window_start,
        window_end=window_end,
    )
