from __future__ import annotations

from datetime import date, timedelta
from typing import List

from backend.app.dto.team_planning import TeamPlanningResponseDTO, TeamAgentPlanningDTO

from backend.app.mappers.agents_light import to_agent_dto
from backend.app.mappers.planning_day import to_planning_day_dto
from backend.app.mappers.teams import to_team_dto

from core.domain.models.team_planning import TeamPlanning


def _daterange(start: date, end: date) -> List[date]:
    d = start
    out: List[date] = []
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out


def to_team_planning_response(planning: TeamPlanning) -> TeamPlanningResponseDTO:
    return TeamPlanningResponseDTO(
        team=to_team_dto(planning.team),
        start_date=planning.start_date,
        end_date=planning.end_date,
        days=_daterange(planning.start_date, planning.end_date),
        agents=[
            TeamAgentPlanningDTO(
                agent=to_agent_dto(ap.agent),
                days=[to_planning_day_dto(d) for d in ap.days],
            )
            for ap in planning.agent_plannings
        ],
    )
