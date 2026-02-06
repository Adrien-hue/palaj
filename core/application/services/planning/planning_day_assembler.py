from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List

from core.application.ports.agent_day_repo import AgentDayRepositoryPort
from core.application.ports.tranche_repo import TrancheRepositoryPort
from core.domain.entities import Tranche
from core.domain.enums.day_type import DayType
from core.domain.models.planning_day import PlanningDay


def _daterange(start: date, end: date) -> List[date]:
    d = start
    out: List[date] = []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out

def _densify_days(
    days: List[PlanningDay],
    start_date: date,
    end_date: date,
    *,
    default_day_type: DayType = DayType.UNKNOWN,
) -> List[PlanningDay]:
    by_date = {d.day_date: d for d in days}
    out: List[PlanningDay] = []
    for d in _daterange(start_date, end_date):
        existing = by_date.get(d)
        if existing is not None:
            out.append(existing)
        else:
            out.append(
                PlanningDay(
                    day_date=d,
                    day_type=default_day_type,
                    description=None,
                    is_off_shift=False,
                    tranches=[],
                )
            )
    return out


@dataclass
class PlanningDayAssembler:
    agent_day_repo: AgentDayRepositoryPort
    tranche_repo: TrancheRepositoryPort

    def build_for_agent(self, agent_id: int, start_date: date, end_date: date) -> List[PlanningDay]:
        agent_days = self.agent_day_repo.list_by_agent_and_range(agent_id, start_date, end_date)

        # Batch fetch all tranches
        tranche_ids: List[int] = []
        for d in agent_days:
            tranche_ids.extend(d.tranche_ids)

        unique_ids = sorted(set(tranche_ids))
        tranches_by_id: Dict[int, Tranche] = {}
        if unique_ids:
            tranches = self.tranche_repo.list_by_ids(unique_ids)
            tranches_by_id = {t.id: t for t in tranches}

        # Build projections
        planning_days: List[PlanningDay] = []
        for d in agent_days:
            tranches = [tranches_by_id[i] for i in d.tranche_ids if i in tranches_by_id]
            planning_days.append(
                PlanningDay(
                    day_date=d.day_date,
                    day_type=d.day_type,
                    description=d.description,
                    is_off_shift=d.is_off_shift,
                    tranches=tranches,
                )
            )

        sorted_planning_days = sorted(planning_days, key=lambda day: day.day_date)
        
        return _densify_days(sorted_planning_days, start_date, end_date)
    
    def build_one_for_agent(self, agent_id: int, day_date: date) -> PlanningDay:
        """
        Build a single PlanningDay projection for one agent and one date.
        No densify, no range rebuild, optimized for PUT response.
        """
        agent_day = self.agent_day_repo.get_by_agent_and_date(agent_id, day_date)

        if agent_day is None:
            # Si tu veux que PUT renvoie toujours une journée, même si supprimée,
            # on renvoie une journée "vide" (UNKNOWN) plutôt que None.
            return PlanningDay(
                day_date=day_date,
                day_type="unknown",
                description=None,
                is_off_shift=False,
                tranches=[],
            )

        tranche_ids = list(getattr(agent_day, "tranche_ids", []) or [])
        tranches: List[Tranche] = []

        if tranche_ids:
            unique_ids = sorted(set(tranche_ids))
            tranche_models = self.tranche_repo.list_by_ids(unique_ids)
            tranches_by_id: Dict[int, Tranche] = {t.id: t for t in tranche_models}
            tranches = [tranches_by_id[i] for i in tranche_ids if i in tranches_by_id]

        # V1: 0..1 tranche max (au cas où)
        tranches = tranches[:1]

        return PlanningDay(
            day_date=agent_day.day_date,
            day_type=agent_day.day_type,
            description=agent_day.description,
            is_off_shift=agent_day.is_off_shift,
            tranches=tranches,
        )


    def build_for_agents(self, agent_ids: List[int], start_date: date, end_date: date) -> Dict[int, List[PlanningDay]]:
        agent_days = self.agent_day_repo.list_by_agents_and_range(agent_ids, start_date, end_date)

        tranche_ids: List[int] = []
        for d in agent_days:
            tranche_ids.extend(d.tranche_ids)

        unique_ids = sorted(set(tranche_ids))
        tranches_by_id: Dict[int, Tranche] = {}
        if unique_ids:
            tranches = self.tranche_repo.list_by_ids(unique_ids)
            tranches_by_id = {t.id: t for t in tranches}

        by_agent: Dict[int, List[PlanningDay]] = {aid: [] for aid in agent_ids}

        for d in agent_days:
            tranches = [tranches_by_id[i] for i in d.tranche_ids if i in tranches_by_id]
            by_agent.setdefault(d.agent_id, []).append(
                PlanningDay(
                    day_date=d.day_date,
                    day_type=d.day_type,
                    description=d.description,
                    is_off_shift=d.is_off_shift,
                    tranches=tranches,
                )
            )

        for aid in by_agent:
            by_agent[aid] = sorted(by_agent[aid], key=lambda day: day.day_date)
            by_agent[aid] = _densify_days(by_agent[aid], start_date, end_date)
        return by_agent
    
    def build_for_agents_day(self, agent_ids: List[int], day_date: date) -> Dict[int, PlanningDay]:
        by_agent = self.build_for_agents(agent_ids, day_date, day_date)

        return {aid: days[0] for aid, days in by_agent.items()}