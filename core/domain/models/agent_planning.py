# core/domain/models/agent_planning.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List

from core.domain.entities import Agent
from core.domain.models.planning_day import PlanningDay


@dataclass(frozen=True)
class AgentPlanning:
    """
    Snapshot de planning pour affichage.
    Pas de logique de construction, pas de stats.
    """
    agent: Agent
    start_date: date
    end_date: date
    days: List[PlanningDay]
