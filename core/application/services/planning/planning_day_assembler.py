from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from core.application.ports.agent_day_repo import AgentDayRepositoryPort
from core.application.ports.tranche_repo import TrancheRepositoryPort
from core.domain.entities import Tranche
from core.domain.models.planning_day import PlanningDay


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

        return planning_days
