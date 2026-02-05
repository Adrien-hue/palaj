from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Sequence, Dict, Set
from collections import defaultdict

from core.application.ports.agent_day_repo import AgentDayRepositoryPort
from core.application.ports.agent_day_assignment_repo import AgentDayAssignmentRepositoryPort
from core.application.ports.tranche_repo import TrancheRepositoryPort
from core.domain.entities.agent_day import AgentDay
from core.domain.entities.agent_day_assignment import AgentDayAssignment
from core.domain.enums.day_type import DayType


@dataclass(frozen=True)
class PostePlanningTrancheAgents:
    tranche_id: int
    agent_ids: List[int]


class PostePlanningDayService:
    """
    Command service for editing a poste day by rewriting all assignments for a poste on a given date.

    Rules:
    - We only manipulate AgentDay + AgentDayAssignment (no poste planning table)
    - We always enforce DayType.WORKING for impacted AgentDays (since we edit "jours travaillés")
    - Rewrite = delete all assignments on tranches of poste for that date, then insert those from payload
    """

    def __init__(
        self,
        tranche_repo: TrancheRepositoryPort,
        agent_day_repo: AgentDayRepositoryPort,
        agent_day_assignment_repo: AgentDayAssignmentRepositoryPort,
    ) -> None:
        self.tranche_repo = tranche_repo
        self.agent_day_repo = agent_day_repo
        self.agent_day_assignment_repo = agent_day_assignment_repo

    def rewrite_poste_day(
        self,
        poste_id: int,
        day_date: date,
        tranches_payload: Sequence[PostePlanningTrancheAgents],
        cleanup_empty_agent_days: bool = True,
    ) -> None:
        poste_tranche_ids = self.tranche_repo.list_ids_by_poste(poste_id)
        poste_tranche_id_set: Set[int] = set(poste_tranche_ids)

        payload_tranche_ids = [t.tranche_id for t in tranches_payload]
        invalid = [tid for tid in payload_tranche_ids if tid not in poste_tranche_id_set]
        if invalid:
            raise ValueError(f"Tranches not in poste {poste_id}: {invalid}")

        # 2) optional validation: prevent same agent on 2 tranches of same poste same day
        seen_agent: Dict[int, int] = {}
        for t in tranches_payload:
            for agent_id in t.agent_ids:
                if agent_id in seen_agent:
                    raise ValueError(
                        f"Agent {agent_id} appears in multiple tranches "
                        f"({seen_agent[agent_id]} and {t.tranche_id})"
                    )
                seen_agent[agent_id] = t.tranche_id

        # 3) rewrite mechanics
        # delete all assignments for poste tranches on that date
        self.agent_day_assignment_repo.delete_by_date_and_tranche_ids(day_date=day_date, tranche_ids=poste_tranche_ids)

        # build desired assignments by agent_id
        by_agent: Dict[int, List[int]] = defaultdict(list)
        for t in tranches_payload:
            for agent_id in t.agent_ids:
                by_agent[agent_id].append(t.tranche_id)

        # upsert working AgentDay + insert assignments
        for agent_id, tranche_ids in by_agent.items():
            agent_day = self._get_or_create_working_day(agent_id=agent_id, day_date=day_date)

            for tranche_id in tranche_ids:
                self.agent_day_assignment_repo.create(
                    AgentDayAssignment(
                        id=0,
                        agent_day_id=agent_day.id,
                        tranche_id=tranche_id,
                    )
                )

        if cleanup_empty_agent_days:
            self.agent_day_repo.delete_empty_days_by_date(day_date)

    def delete_poste_day(
        self,
        poste_id: int,
        day_date: date,
        cleanup_empty_agent_days: bool = True,
    ) -> None:
        poste_tranche_ids = self.tranche_repo.list_ids_by_poste(poste_id)
        self.agent_day_assignment_repo.delete_by_date_and_tranche_ids(day_date=day_date, tranche_ids=poste_tranche_ids)

        if cleanup_empty_agent_days:
            self.agent_day_repo.delete_empty_days_by_date(day_date)

    def _get_or_create_working_day(self, agent_id: int, day_date: date) -> AgentDay:
        existing = self.agent_day_repo.get_by_agent_and_date(agent_id, day_date)
        if existing is None:
            created = self.agent_day_repo.create(
                AgentDay(
                    id=0,
                    agent_id=agent_id,
                    day_date=day_date,
                    day_type=DayType.WORKING.value,
                    description=None,
                    is_off_shift=False,
                )
            )
            if created is None:
                raise ValueError(f"Could not create working day for agent {agent_id} on date {day_date}")
            return created

        existing.day_type = DayType.WORKING.value
        existing.is_off_shift = False

        updated = self.agent_day_repo.update(existing)
        if updated is None:
            raise ValueError(f"Could not update existing working day for agent {agent_id} on date {day_date}")
        return updated
