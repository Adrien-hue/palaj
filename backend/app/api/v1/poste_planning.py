from datetime import date

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import (
    get_poste_planning_day_assembler,
    get_poste_planning_day_service,
    get_poste_planning_factory,
    get_poste_service,
)
from backend.app.api.http_exceptions import bad_request, not_found
from backend.app.dto.poste_coverage_day import PosteCoverageDayDTO
from backend.app.dto.poste_planning import PostePlanningDayDTO, PostePlanningDayEditRequest, PostePlanningResponseDTO
from backend.app.mappers.poste_coverage_day import to_poste_coverage_day_dto
from backend.app.mappers.poste_planning import to_poste_planning_day_dto, to_poste_planning_response
from core.application.services import PosteService
from core.application.services.exceptions import NotFoundError
from core.application.services.planning.poste_planning_day_assembler import PostePlanningDayAssembler
from core.application.services.planning.poste_planning_day_service import (
    PostePlanningDayService,
    PostePlanningTrancheAgents,
)
from core.application.services.planning.poste_planning_factory import PostePlanningFactory

router = APIRouter(prefix="/postes", tags=["Postes - Planning"])


@router.get("/{poste_id}/planning", response_model=PostePlanningResponseDTO)
def get_poste_planning(
    poste_id: int,
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date: date = Query(..., description="YYYY-MM-DD"),
    poste_planning_factory: PostePlanningFactory = Depends(get_poste_planning_factory),
):
    try:
        planning = poste_planning_factory.build(
            poste_id=poste_id,
            start_date=start_date,
            end_date=end_date,
        )
        return to_poste_planning_response(planning)
    except ValueError as e:
        msg = str(e)
        # compat avec ton existant (idéalement remplacer par NotFoundError côté service)
        if msg.lower() == "poste not found":
            not_found(msg)
        bad_request(msg)


@router.get("/{poste_id}/planning/coverage", response_model=PosteCoverageDayDTO)
def get_poste_planning_coverage(
    poste_id: int,
    date: date,
    service: PosteService = Depends(get_poste_service),
) -> PosteCoverageDayDTO:
    try:
        rm = service.get_poste_coverage_for_day(poste_id=poste_id, day_date=date)
        return to_poste_coverage_day_dto(rm)
    except NotFoundError as e:
        # on conserve ton payload structuré (pratique côté front)
        not_found({"code": e.code, "details": e.details})


@router.put("/{poste_id}/planning/days/{day_date}", response_model=PostePlanningDayDTO)
def rewrite_poste_day(
    poste_id: int,
    day_date: date,
    payload: PostePlanningDayEditRequest,
    svc: PostePlanningDayService = Depends(get_poste_planning_day_service),
    assembler: PostePlanningDayAssembler = Depends(get_poste_planning_day_assembler),
):
    try:
        svc.rewrite_poste_day(
            poste_id=poste_id,
            day_date=day_date,
            tranches_payload=[
                PostePlanningTrancheAgents(tranche_id=t.tranche_id, agent_ids=t.agent_ids)
                for t in payload.tranches
            ],
            cleanup_empty_agent_days=payload.cleanup_empty_agent_days,
        )

        poste_planning_day = assembler.build_one_for_poste(poste_id=poste_id, day_date=day_date)
        return to_poste_planning_day_dto(poste_planning_day)

    except ValueError as e:
        bad_request(str(e))


@router.delete("/{poste_id}/planning/days/{day_date}")
def delete_poste_day(
    poste_id: int,
    day_date: date,
    cleanup_empty_agent_days: bool = True,
    svc: PostePlanningDayService = Depends(get_poste_planning_day_service),
):
    try:
        svc.delete_poste_day(
            poste_id=poste_id,
            day_date=day_date,
            cleanup_empty_agent_days=cleanup_empty_agent_days,
        )
        return {"status": "ok"}
    except ValueError as e:
        bad_request(str(e))
