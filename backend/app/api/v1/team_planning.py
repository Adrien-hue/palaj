from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_team_planning_factory
from backend.app.api.http_exceptions import bad_request, not_found
from backend.app.dto.team_planning import TeamPlanningResponseDTO
from backend.app.mappers.team_planning import to_team_planning_response
from core.application.services.exceptions import NotFoundError
from core.application.services.planning.team_planning_factory import TeamPlanningFactory

router = APIRouter(prefix="/teams", tags=["teams - planning"])


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
