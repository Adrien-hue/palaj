from datetime import date
from typing import List

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_agent_day_service, get_planning_day_assembler, get_team_planning_factory, get_team_service
from backend.app.api.http_exceptions import bad_request, not_found
from backend.app.dto.planning_day import AgentPlanningDayDTO
from backend.app.dto.team_planning import TeamPlanningDayBulkPutDTO, TeamPlanningDayBulkPutResponseDTO, TeamPlanningResponseDTO, TeamBulkFailedItem
from backend.app.mappers.planning_day import to_planning_day_dto
from backend.app.mappers.team_planning import to_team_planning_response
from core.application.services.exceptions import NotFoundError
from core.application.services.planning.team_planning_factory import TeamPlanningFactory

router = APIRouter(prefix="/teams", tags=["Teams - Planning"])


@router.get("/{team_id}/planning", response_model=TeamPlanningResponseDTO)
def get_team_planning(
    team_id: int,
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date: date = Query(..., description="YYYY-MM-DD"),
    team_planning_factory: TeamPlanningFactory = Depends(get_team_planning_factory),
):
    try:
        planning = team_planning_factory.build(team_id=team_id, start_date=start_date, end_date=end_date)
        return to_team_planning_response(planning)
    except NotFoundError as e:
        # tu avais un detail structuré, on conserve
        not_found({"code": e.code, "details": e.details})
    except ValueError as e:
        bad_request(str(e))

@router.put("/{team_id}/planning/days:bulk", response_model=TeamPlanningDayBulkPutResponseDTO)
def bulk_upsert_team_planning_days(
    team_id: int,
    payload: TeamPlanningDayBulkPutDTO,
    agent_day_service=Depends(get_agent_day_service),
    planning_day_assembler=Depends(get_planning_day_assembler),
    team_service=Depends(get_team_service),
):
    updated: List[AgentPlanningDayDTO] = []
    failed: List[TeamBulkFailedItem] = []

    try:
        team_agent_ids = set(team_service.list_agent_ids(team_id=team_id))
    except NotFoundError as e:
        not_found({"code": e.code, "details": e.details})

    for item in payload.items:
        agent_id = item.agent_id

        if agent_id not in team_agent_ids:
            for d in item.day_dates:
                failed.append(
                    TeamBulkFailedItem(
                        agent_id=agent_id,
                        day_date=d,
                        code="NOT_IN_TEAM",
                        message="Agent does not belong to this team",
                    )
                )
            continue

        for day_date in item.day_dates:
            try:
                agent_day_service.upsert_day(
                    agent_id=agent_id,
                    day_date=day_date,
                    day_type=payload.day_type,
                    tranche_id=payload.tranche_id,
                    description=payload.description,
                )

                planning_day = planning_day_assembler.build_one_for_agent(agent_id=agent_id, day_date=day_date)
                updated.append(
                    AgentPlanningDayDTO(
                        agent_id=agent_id,
                        planning_day=to_planning_day_dto(planning_day),
                    )
                )

            except ValueError as e:
                failed.append(
                    TeamBulkFailedItem(
                        agent_id=agent_id,
                        day_date=day_date,
                        code="VALIDATION_ERROR",
                        message=str(e),
                    )
                )
            except Exception as e:
                failed.append(
                    TeamBulkFailedItem(
                        agent_id=agent_id,
                        day_date=day_date,
                        code="UNEXPECTED_ERROR",
                        message=str(e),
                    )
                )

    return TeamPlanningDayBulkPutResponseDTO(updated=updated, failed=failed)
