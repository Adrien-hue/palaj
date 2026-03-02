from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from backend.app.api.http_exceptions import not_found
from backend.app.dto.agents import AgentDTO
from backend.app.dto.planning_day import PlanningDayDTO
from backend.app.dto.team import TeamDTO
from backend.app.dto.team_planning import TeamAgentPlanningDTO, TeamPlanningResponseDTO
from backend.app.dto.tranches import TrancheDTO
from db.models import PlanningDraft, PlanningDraftAgentDay, PlanningDraftAssignment, Team, Tranche

logger = logging.getLogger(__name__)


def _build_period_days(start_date: date, end_date: date) -> list[date]:
    day_count = (end_date - start_date).days + 1
    return [start_date + timedelta(days=offset) for offset in range(day_count)]


def _to_sorted_unique_tranche_dtos(
    *,
    draft_id: int,
    agent_id: int,
    day_date: date,
    tranches: list[Tranche],
) -> list[TrancheDTO]:
    seen: set[int] = set()
    unique_tranches: list[Tranche] = []

    for tranche in tranches:
        if tranche.id in seen:
            logger.warning(
                "draft_team_planning.duplicate_tranche_assignment",
                extra={
                    "draft_id": draft_id,
                    "agent_id": agent_id,
                    "day_date": str(day_date),
                    "tranche_id": tranche.id,
                },
            )
            continue
        seen.add(tranche.id)
        unique_tranches.append(tranche)

    unique_tranches.sort(key=lambda tranche: (tranche.heure_debut, tranche.id))
    return [TrancheDTO.model_validate(tranche) for tranche in unique_tranches]


def get_draft_team_planning(session: Session, draft_id: int) -> TeamPlanningResponseDTO:
    draft = session.get(PlanningDraft, draft_id)
    if draft is None:
        not_found("Planning draft not found")

    team = (
        session.query(Team)
        .options(selectinload(Team.agents))
        .filter(Team.id == draft.team_id)
        .first()
    )
    if team is None:
        not_found("Team not found")

    draft_agent_days = (
        session.query(PlanningDraftAgentDay)
        .filter(PlanningDraftAgentDay.draft_id == draft_id)
        .all()
    )

    by_draft_agent_day_id: dict[int, PlanningDraftAgentDay] = {
        draft_agent_day.id: draft_agent_day
        for draft_agent_day in draft_agent_days
    }

    assignment_rows = (
        session.query(PlanningDraftAssignment.draft_agent_day_id, Tranche)
        .join(PlanningDraftAgentDay, PlanningDraftAgentDay.id == PlanningDraftAssignment.draft_agent_day_id)
        .join(Tranche, Tranche.id == PlanningDraftAssignment.tranche_id)
        .filter(PlanningDraftAgentDay.draft_id == draft_id)
        .all()
    )

    raw_tranches_by_draft_agent_day_id: dict[int, list[Tranche]] = {}
    for draft_agent_day_id, tranche in assignment_rows:
        if draft_agent_day_id not in by_draft_agent_day_id:
            continue
        raw_tranches_by_draft_agent_day_id.setdefault(draft_agent_day_id, []).append(tranche)

    tranches_by_draft_agent_day_id: dict[int, list[TrancheDTO]] = {}
    for draft_agent_day_id, raw_tranches in raw_tranches_by_draft_agent_day_id.items():
        draft_agent_day = by_draft_agent_day_id[draft_agent_day_id]
        tranches_by_draft_agent_day_id[draft_agent_day_id] = _to_sorted_unique_tranche_dtos(
            draft_id=draft_id,
            agent_id=draft_agent_day.agent_id,
            day_date=draft_agent_day.day_date,
            tranches=raw_tranches,
        )

    by_agent_date: dict[tuple[int, date], PlanningDraftAgentDay] = {
        (draft_agent_day.agent_id, draft_agent_day.day_date): draft_agent_day
        for draft_agent_day in draft_agent_days
    }

    days = _build_period_days(draft.start_date, draft.end_date)
    team_agents = sorted(team.agents, key=lambda agent: agent.id)

    agents_response: list[TeamAgentPlanningDTO] = []
    for agent in team_agents:
        planning_days: list[PlanningDayDTO] = []
        for day_date in days:
            draft_agent_day = by_agent_date.get((agent.id, day_date))
            if draft_agent_day is None:
                planning_days.append(
                    PlanningDayDTO(
                        day_date=day_date,
                        day_type="rest",
                        description=None,
                        is_off_shift=False,
                        tranches=[],
                    )
                )
                continue

            planning_days.append(
                PlanningDayDTO(
                    day_date=day_date,
                    day_type=draft_agent_day.day_type,
                    description=draft_agent_day.description,
                    is_off_shift=draft_agent_day.is_off_shift,
                    tranches=tranches_by_draft_agent_day_id.get(draft_agent_day.id, []),
                )
            )

        agents_response.append(
            TeamAgentPlanningDTO(
                agent=AgentDTO.model_validate(agent, from_attributes=True),
                days=planning_days,
            )
        )

    return TeamPlanningResponseDTO(
        team=TeamDTO.model_validate(team),
        start_date=draft.start_date,
        end_date=draft.end_date,
        days=days,
        agents=agents_response,
    )
