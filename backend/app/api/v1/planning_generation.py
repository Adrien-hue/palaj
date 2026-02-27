from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.api.http_exceptions import bad_request, not_found, unprocessable_entity
from backend.app.dto.planning_generate import (
    PlanningGenerateRequest,
    PlanningGenerateResponse,
    PlanningGenerateStatusResponse,
)
from backend.app.services.planning.generation import planning_generation_service
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import PlanningDraft

router = APIRouter(prefix="/planning", tags=["Planning - Generation"])


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
    return PlanningGenerateStatusResponse(
        job_id=UUID(draft.job_id),
        draft_id=draft.id,
        status=draft_status,
        progress=_progress_from_status(draft_status),
        result_stats=draft.result_stats if draft_status == PlanningDraftStatus.SUCCESS else None,
        error=draft.error if draft_status == PlanningDraftStatus.FAILED else None,
    )
