from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Optional

from core.application.ports.agent_day_repo import AgentDayRepositoryPort
from core.application.ports.agent_day_assignment_repo import (
    AgentDayAssignmentRepositoryPort,
)
from core.domain.enums.day_type import DayType
from core.domain.entities.agent_day import AgentDay
from core.domain.entities.agent_day_assignment import AgentDayAssignment


class AgentDayService:
    """
    Command service for editing an agent day (create/update/delete) + its single assignment (V1).

    Key rules:
    - AgentDay is identified by (agent_id, day_date)
    - V1 enforces 0..1 assignment per day (by deleting all then optionally adding one)
    - If day_type != WORKING: no assignment
    - is_off_shift is derived from day_type == OFF_SHIFT
    """

    def __init__(
        self,
        agent_day_repo: AgentDayRepositoryPort,
        assignment_repo: AgentDayAssignmentRepositoryPort,
    ) -> None:
        self.agent_day_repo = agent_day_repo
        self.assignment_repo = assignment_repo

    def upsert_day(
        self,
        agent_id: int,
        day_date: date,
        day_type: DayType,
        tranche_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> AgentDay:
        """
        Create or update an AgentDay by (agent_id, day_date).
        Returns the refreshed AgentDay entity (with assignments if your repo hydrates them).
        """
        existing = self.agent_day_repo.get_by_agent_and_date(agent_id, day_date)

        is_off_shift = (day_type == DayType.OFF_SHIFT)

        if existing is None:
            # Create
            created = self.agent_day_repo.create(
                AgentDay(
                    id=0,
                    agent_id=agent_id,
                    day_date=day_date,
                    day_type=day_type.value,
                    description=description,
                    is_off_shift=is_off_shift,
                )
            )
            agent_day = created
        else:
            # Update
            existing.day_type = day_type.value
            existing.description = description
            existing.is_off_shift = (day_type == DayType.OFF_SHIFT)

            agent_day = self.agent_day_repo.update(existing)

        # --- V1: enforce 0..1 assignment ---
        # We act on agent_day.id internally (not exposed at API level)
        if agent_day is None or agent_day.id is None or agent_day.id <= 0:
            # Defensive: if your entity doesn't carry id, your repo should still return it after create/update.
            raise ValueError("AgentDay must have a valid id after persistence to manage assignments.")

        # Clear all assignments for this day
        self.assignment_repo.delete_by_agent_day_id(agent_day.id)

        # Add only if WORKING and tranche_id is provided
        if day_type == DayType.WORKING and tranche_id is not None:
            self.assignment_repo.create(
                AgentDayAssignment(
                    id=0,
                    agent_day_id=agent_day.id,
                    tranche_id=tranche_id,
                )
            )

        # Re-fetch to return fully hydrated entity (incl. assignments/tranche relationship)
        refreshed = self.agent_day_repo.get_by_agent_and_date(agent_id, day_date)
        return refreshed if refreshed is not None else agent_day

    def delete_day(self, agent_id: int, day_date: date) -> bool:
        """
        Delete an AgentDay by (agent_id, day_date).
        Returns True if a day was deleted, False if it didn't exist.
        Assignments are deleted by cascade, but we can be defensive and clear them if day exists.
        """
        existing = self.agent_day_repo.get_by_agent_and_date(agent_id, day_date)
        if existing is None:
            return False

        # Defensive: clear assignments first (even if DB cascade handles it)
        self.assignment_repo.delete_by_agent_day_id(existing.id)

        return self.agent_day_repo.delete_by_agent_and_date(agent_id, day_date)
