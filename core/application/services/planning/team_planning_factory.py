from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, List

from core.domain.models.team_planning import TeamPlanning
from core.domain.models.agent_planning import AgentPlanning

if TYPE_CHECKING:
    from core.application.services.teams.team_service import TeamService
    from core.application.services.agent_service import AgentService
    from core.application.services.planning.planning_day_assembler import PlanningDayAssembler


class TeamPlanningFactory:
    def __init__(
        self,
        team_service: TeamService,
        agent_service: AgentService,
        planning_day_assembler: PlanningDayAssembler,
    ) -> None:
        self.team_service = team_service
        self.agent_service = agent_service
        self.planning_day_assembler = planning_day_assembler

    def build(self, team_id: int, start_date: date, end_date: date) -> TeamPlanning:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        team = self.team_service.get(team_id)
        agent_ids = sorted(self.team_service.list_agent_ids(team_id))

        days_by_agent = self.planning_day_assembler.build_for_agents(agent_ids, start_date, end_date)

        agent_plannings: List[AgentPlanning] = []
        for agent_id in agent_ids:
            agent = self.agent_service.get_agent_complet(agent_id)
            if not agent:
                continue
            days = days_by_agent.get(agent_id, [])
            agent_plannings.append(AgentPlanning(agent, start_date, end_date, days))

        return TeamPlanning(team=team, start_date=start_date, end_date=end_date, agent_plannings=agent_plannings)
