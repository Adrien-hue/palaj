from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.api.deps_current_user import current_user
from backend.app.api.http_exceptions import bad_request, forbidden, not_found, unprocessable_entity
from backend.app.dto.team_planning import TeamPlanningResponseDTO
from backend.app.services.planning_draft_read_service import get_draft_team_planning as get_draft_team_planning_service
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
from db.models import PlanningDraft, User

router = APIRouter(prefix="/planning", tags=["Planning - Generation"])




def _require_manager_or_admin(user: User) -> None:
    if user.role not in {"admin", "manager"}:
        forbidden("Role manager or admin required")


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
