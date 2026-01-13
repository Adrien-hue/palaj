# core/application/services/planning/agent_planning_factory.py
from __future__ import annotations
from typing import TYPE_CHECKING

from datetime import date

from core.domain.models.agent_planning import AgentPlanning

if TYPE_CHECKING:
    from core.application.services.agent_service import AgentService
    from core.application.services.planning.planning_day_assembler import PlanningDayAssembler


class AgentPlanningFactory:

    def __init__(
        self,
        agent_service: AgentService,
        planning_day_assembler: PlanningDayAssembler,
    ) -> None:
        self.agent_service = agent_service
        self.planning_day_assembler = planning_day_assembler

    def build(
        self,
        agent_id: int,
        start_date: date,
        end_date: date,
    ) -> AgentPlanning :
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        agent = self.agent_service.get_agent_complet(agent_id)
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found.")
        
        days = self.planning_day_assembler.build_for_agent(agent_id, start_date, end_date)

        return AgentPlanning(agent, start_date, end_date, days)