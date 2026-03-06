from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.api.deps_current_user import current_user
from backend.app.api.http_exceptions import bad_request, forbidden, not_found, unprocessable_entity
from backend.app.dto.team_planning import TeamPlanningResponseDTO
from backend.app.services.planning_draft_read_service import get_draft_team_planning as get_draft_team_planning_service
from backend.app.dto.planning_generate_jobs import PlanningGenerateJobListItem, PlanningGenerateJobsListResponse
from backend.app.dto.planning_generate import (
    PlanningDraftAcceptResponse,
    PlanningDraftRejectResponse,
    PlanningGenerateRequest,
    PlanningGenerateResponse,
    PlanningGenerateStatusResponse,
)
from backend.app.services.planning.generation import planning_generation_service
from backend.app.services.planning_draft_decision_service import accept_draft as accept_draft_service, reject_draft as reject_draft_service
from backend.app.services.solver.stats_normalizer import normalize_result_stats_for_api
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import PlanningDraft, Team, User

router = APIRouter(prefix="/planning", tags=["Planning - Generation"])




def _require_manager_or_admin(user: User) -> None:
    if user.role not in {"admin", "manager"}:
        forbidden("Role manager or admin required")


def _require_admin(user: User) -> None:
    if user.role != "admin":
        forbidden("Role admin required")




def _to_start_of_day(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)


def _to_end_of_day(value: date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.max)


def _progress_from_status(status: PlanningDraftStatus) -> float:
    if status == PlanningDraftStatus.QUEUED:
        return 0.0
    if status == PlanningDraftStatus.RUNNING:
        return 0.1
    return 1.0


@router.post("/generate", response_model=PlanningGenerateResponse)
def generate_planning(
    payload: PlanningGenerateRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
) -> PlanningGenerateResponse:
    try:
        draft = planning_generation_service.create_draft(
            session=session,
            team_id=payload.team_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            seed=payload.seed,
            time_limit_seconds=payload.time_limit_seconds,
            quality_profile=payload.quality_profile,
            v3_strategy=payload.v3_strategy,
            phase1_fraction=payload.phase1_fraction,
            phase1_seconds=payload.phase1_seconds,
            lns_iter_seconds=payload.lns_iter_seconds,
            lns_min_remaining_seconds=payload.lns_min_remaining_seconds,
            lns_strict_improve=payload.lns_strict_improve,
            lns_max_days_to_relax=payload.lns_max_days_to_relax,
            lns_neighborhood_mode=payload.lns_neighborhood_mode,
            min_lns_seconds=payload.min_lns_seconds,
            phase2_max_fraction_of_remaining=payload.phase2_max_fraction_of_remaining,
            phase2_no_improve_seconds=payload.phase2_no_improve_seconds,
            enable_decision_strategy=payload.enable_decision_strategy,
            enable_symmetry_breaking=payload.enable_symmetry_breaking,
        )

        session.commit()

        session.refresh(draft)
    except ValueError as exc:
        bad_request(str(exc))

    job_id_str = str(draft.job_id)
    background_tasks.add_task(planning_generation_service.run_job, job_id_str)
    return PlanningGenerateResponse(
        job_id=UUID(draft.job_id),
        draft_id=draft.id,
        status=PlanningDraftStatus.QUEUED,
    )


@router.get("/generate/jobs", response_model=PlanningGenerateJobsListResponse)
def list_generation_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status: PlanningDraftStatus | None = None,
    team_id: int | None = Query(default=None, ge=1),
    search: str | None = Query(default=None, min_length=1),
    created_from: date | datetime | None = None,
    created_to: date | datetime | None = None,
    session: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PlanningGenerateJobsListResponse:
    _require_admin(user)

    query = (
        session.query(PlanningDraft, Team.name.label("team_name"))
        .join(Team, Team.id == PlanningDraft.team_id)
    )

    if status is not None:
        query = query.filter(PlanningDraft.status == status.value)
    if team_id is not None:
        query = query.filter(PlanningDraft.team_id == team_id)
    if created_from is not None:
        query = query.filter(PlanningDraft.created_at >= _to_start_of_day(created_from))
    if created_to is not None:
        query = query.filter(PlanningDraft.created_at <= _to_end_of_day(created_to))
    if created_from is not None and created_to is not None and _to_start_of_day(created_from) > _to_end_of_day(created_to):
        bad_request("created_from must be <= created_to")

    if search is not None:
        normalized_search = search.strip()
        search_filters = [PlanningDraft.job_id.ilike(f"%{normalized_search}%")]
        is_numeric_search = normalized_search.isdigit()
        if is_numeric_search:
            # Numeric search keeps textual matching on job_id and also supports exact draft_id match.
            search_filters.append(PlanningDraft.id == int(normalized_search))
        query = query.filter(or_(*search_filters))

    total = query.count()

    rows = (
        # Stable ordering: most recent first, then deterministic tie-breaker by draft id.
        query.order_by(PlanningDraft.created_at.desc(), PlanningDraft.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        PlanningGenerateJobListItem(
            job_id=UUID(draft.job_id),
            draft_id=draft.id,
            team_id=draft.team_id,
            team_name=team_name,
            start_date=draft.start_date,
            end_date=draft.end_date,
            status=PlanningDraftStatus(draft.status),
            progress=_progress_from_status(PlanningDraftStatus(draft.status)),
            created_at=draft.created_at,
            updated_at=draft.updated_at,
        )
        for draft, team_name in rows
    ]

    return PlanningGenerateJobsListResponse(items=items, page=page, page_size=page_size, total=total)




@router.get("/generate/{job_id}", response_model=PlanningGenerateStatusResponse)
def get_generation_status(job_id: str, session: Session = Depends(get_db)) -> PlanningGenerateStatusResponse:
    try:
        parsed_job_id = str(UUID(job_id))
    except ValueError:
        unprocessable_entity("job_id must be a valid UUID")

    draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == parsed_job_id).first()
    if draft is None:
        not_found("Planning generation job not found")

    draft_status = PlanningDraftStatus(draft.status)
    normalized_result_stats = None
    if draft_status in (PlanningDraftStatus.SUCCESS, PlanningDraftStatus.FAILED):
        normalized_result_stats = normalize_result_stats_for_api(draft.result_stats)

    return PlanningGenerateStatusResponse(
        job_id=UUID(draft.job_id),
        draft_id=draft.id,
        status=draft_status,
        progress=_progress_from_status(draft_status),
        result_stats=normalized_result_stats,
        error=draft.error if draft_status == PlanningDraftStatus.FAILED else None,
    )


@router.get("/drafts/{draft_id}/team-planning", response_model=TeamPlanningResponseDTO)
def get_draft_team_planning(draft_id: int, session: Session = Depends(get_db)) -> TeamPlanningResponseDTO:
    return get_draft_team_planning_service(session=session, draft_id=draft_id)


@router.post("/drafts/{draft_id}/accept", response_model=PlanningDraftAcceptResponse)
def accept_draft(
    draft_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PlanningDraftAcceptResponse:
    _require_manager_or_admin(user)
    result = accept_draft_service(session=session, draft_id=draft_id, actor_user_id=user.id)
    return PlanningDraftAcceptResponse(
        draft_id=result.draft_id,
        status=result.status,
        published=result.published,
        team_id=result.team_id,
        start_date=result.start_date,
        end_date=result.end_date,
    )


@router.post("/drafts/{draft_id}/reject", response_model=PlanningDraftRejectResponse)
def reject_draft(
    draft_id: int,
    session: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> PlanningDraftRejectResponse:
    _require_manager_or_admin(user)
    result = reject_draft_service(session=session, draft_id=draft_id, actor_user_id=user.id)
    return PlanningDraftRejectResponse(draft_id=result.draft_id, status=result.status)
