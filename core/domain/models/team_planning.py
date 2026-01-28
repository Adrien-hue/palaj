from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List

from core.domain.entities.team import Team
from core.domain.models.agent_planning import AgentPlanning


@dataclass(frozen=True)
class TeamPlanning:
    team: Team
    start_date: date
    end_date: date
    agent_plannings: List[AgentPlanning]
