# core/application/ports/agent_day_repository.py
from __future__ import annotations
from datetime import date
from typing import Protocol, List, Optional

from core.domain.models.agent_day import AgentDay


class AgentDayRepository(Protocol):
    def get_by_agent_and_date(self, agent_id: int, day_date: date) -> Optional[AgentDay]:...
    def list_by_agent_and_range(self, agent_id: int, start_date: date, end_date: date) -> List[AgentDay]:...