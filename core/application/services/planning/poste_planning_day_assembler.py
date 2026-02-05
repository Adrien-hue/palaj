from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List

from core.application.ports.agent_day_repo import AgentDayRepositoryPort
from core.application.ports.agent_repo import AgentRepositoryPort
from core.application.ports.tranche_repo import TrancheRepositoryPort
from core.domain.entities import Agent, Tranche
from core.domain.entities.agent_day import AgentDay
from core.domain.enums.day_type import DayType
from core.domain.models.poste_planning import PostePlanningDay, PostePlanningTranche


def _daterange(start: date, end: date) -> List[date]:
    d = start
    out: List[date] = []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def _dedupe_keep_order(values: List[int]) -> List[int]:
    seen = set()
    out: List[int] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


@dataclass
class PostePlanningDayAssembler:
    tranche_repo: TrancheRepositoryPort
    agent_repo: AgentRepositoryPort
    agent_day_repo: AgentDayRepositoryPort

    def build_for_poste(self, poste_id: int, start_date: date, end_date: date) -> List[PostePlanningDay]:
        # 1) Fetch tranches (sorted, stable ordering)
        tranches = self.tranche_repo.list_by_poste_id(poste_id)
        tranches = sorted(tranches, key=lambda t: (t.heure_debut, t.heure_fin, t.id))

        # 2) Fetch agent_days in range
        agent_days = self.agent_day_repo.list_by_poste_and_range(
            poste_id=poste_id,
            start_date=start_date,
            end_date=end_date,
        )

        # 3) Batch fetch agents referenced by agent_days
        agent_ids = sorted({ad.agent_id for ad in agent_days})
        agents_by_id: Dict[int, Agent] = {}
        if agent_ids:
            agents = self.agent_repo.list_by_ids(agent_ids)
            agents_by_id = {a.id: a for a in agents}

        return self._assemble_days(
            start_date=start_date,
            end_date=end_date,
            tranches=tranches,
            agents_by_id=agents_by_id,
            agent_days=agent_days,
        )
    
    def build_one_for_poste(self, poste_id: int, day_date: date) -> PostePlanningDay:
        # 1) Fetch tranches (sorted, stable ordering)
        tranches = self.tranche_repo.list_by_poste_id(poste_id)
        tranches = sorted(tranches, key=lambda t: (t.heure_debut, t.heure_fin, t.id))

        # 2) Fetch agent_days for the single day
        agent_days = self.agent_day_repo.list_by_poste_and_day(poste_id=poste_id, day_date=day_date)

        # 3) Batch fetch agents referenced
        agent_ids = sorted({ad.agent_id for ad in agent_days})
        agents_by_id: Dict[int, Agent] = {}
        if agent_ids:
            agents = self.agent_repo.list_by_ids(agent_ids)
            agents_by_id = {a.id: a for a in agents}

        # 4) Assemble one day (still uses your stable _assemble_days)
        days = self._assemble_days(
            start_date=day_date,
            end_date=day_date,
            tranches=tranches,
            agents_by_id=agents_by_id,
            agent_days=agent_days,
        )

        if not days:
            # defensive: _assemble_days should always return 1 element for a 1-day range
            raise ValueError(f"Could not build PostePlanningDay for poste {poste_id} on {day_date}")

        return days[0]


    def _assemble_days(
        self,
        *,
        start_date: date,
        end_date: date,
        tranches: List[Tranche],
        agents_by_id: Dict[int, Agent],
        agent_days: List[AgentDay],
    ) -> List[PostePlanningDay]:
        # Index: date -> tranche_id -> list[agent_id]
        idx: Dict[date, Dict[int, List[int]]] = {}

        for ad in agent_days:
            tranche_ids = list(getattr(ad, "tranche_ids", []) or [])
            if not tranche_ids:
                continue

            day_map = idx.setdefault(ad.day_date, {})
            for tranche_id in tranche_ids:
                day_map.setdefault(tranche_id, []).append(ad.agent_id)

        # Build all days with all tranches
        days: List[PostePlanningDay] = []
        for cur in _daterange(start_date, end_date):
            day_tranche_map = idx.get(cur, {})
            tranches_out: List[PostePlanningTranche] = []

            for t in tranches:
                agent_ids = _dedupe_keep_order(day_tranche_map.get(t.id, []))
                agents = [agents_by_id[a_id] for a_id in agent_ids if a_id in agents_by_id]
                tranches_out.append(PostePlanningTranche(tranche=t, agents=agents))

            # Pour une vue poste, on met des valeurs stables
            days.append(
                PostePlanningDay(
                    day_date=cur,
                    day_type=DayType.WORKING,
                    description=None,
                    is_off_shift=False,
                    tranches=tranches_out,
                )
            )

        return days
