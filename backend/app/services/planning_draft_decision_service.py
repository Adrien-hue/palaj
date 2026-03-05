from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.api.http_exceptions import conflict, not_found
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import AgentDay, AgentDayAssignment, AgentTeam, PlanningDraft, PlanningDraftAgentDay, PlanningDraftAssignment

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DraftAcceptResult:
    draft_id: int
    status: PlanningDraftStatus
    published: bool
    team_id: int
    start_date: date
    end_date: date


@dataclass(frozen=True)
class DraftRejectResult:
    draft_id: int
    status: PlanningDraftStatus


def _get_draft_for_update_or_404(session: Session, draft_id: int) -> PlanningDraft:
    draft = (
        session.execute(
            select(PlanningDraft)
            .where(PlanningDraft.id == draft_id)
            .with_for_update()
        )
        .scalar_one_or_none()
    )
    if draft is None:
        not_found("Planning draft not found")
    return draft


def _is_draft_acceptable(session: Session, draft: PlanningDraft) -> bool:
    status = PlanningDraftStatus(draft.status)
    if status == PlanningDraftStatus.SUCCESS:
        return True

    # Fallback: allow solver-timeout-but-usable scenarios when a concrete planning
    # has already been persisted in draft tables and solver metadata indicates a
    # feasible/usable solution.
    if status != PlanningDraftStatus.FAILED:
        return False

    solver_status = str((draft.result_stats or {}).get("solver_status") or "").upper()
    normalized_status = str((draft.result_stats or {}).get("normalized_solver_status") or "").upper()
    has_usable_solver_signal = (
        solver_status in {"FEASIBLE", "OPTIMAL"}
        or normalized_status in {"FEASIBLE", "OPTIMAL", "TIMEOUT"}
    )
    if not has_usable_solver_signal:
        return False

    has_content = (
        session.query(PlanningDraftAgentDay.id)
        .filter(PlanningDraftAgentDay.draft_id == draft.id)
        .first()
        is not None
    )
    return has_content


def _build_accept_response(draft: PlanningDraft) -> DraftAcceptResult:
    return DraftAcceptResult(
        draft_id=draft.id,
        status=PlanningDraftStatus(draft.status),
        published=True,
        team_id=draft.team_id,
        start_date=draft.start_date,
        end_date=draft.end_date,
    )


def accept_draft(session: Session, draft_id: int, actor_user_id: int | None = None) -> DraftAcceptResult:
    with session.begin_nested():
        draft = _get_draft_for_update_or_404(session, draft_id)
        draft_status = PlanningDraftStatus(draft.status)

        if draft_status == PlanningDraftStatus.ACCEPTED:
            return _build_accept_response(draft)
        if draft_status in {PlanningDraftStatus.REJECTED, PlanningDraftStatus.SUPERSEDED}:
            conflict("Planning draft cannot be accepted in its current status")
        if not _is_draft_acceptable(session, draft):
            conflict("Planning draft cannot be accepted in its current status")

        team_agent_ids = [
            agent_id
            for (agent_id,) in session.execute(select(AgentTeam.agent_id).where(AgentTeam.team_id == draft.team_id)).all()
        ]

        if team_agent_ids:
            existing_agent_day_ids = [
                agent_day_id
                for (agent_day_id,) in (
                    session.query(AgentDay.id)
                    .filter(
                        AgentDay.agent_id.in_(team_agent_ids),
                        AgentDay.day_date >= draft.start_date,
                        AgentDay.day_date <= draft.end_date,
                    )
                    .all()
                )
            ]
            if existing_agent_day_ids:
                session.execute(delete(AgentDayAssignment).where(AgentDayAssignment.agent_day_id.in_(existing_agent_day_ids)))
                session.execute(delete(AgentDay).where(AgentDay.id.in_(existing_agent_day_ids)))

        draft_days = session.query(PlanningDraftAgentDay).filter(PlanningDraftAgentDay.draft_id == draft.id).all()
        draft_assignments = (
            session.query(PlanningDraftAssignment)
            .join(PlanningDraftAgentDay, PlanningDraftAgentDay.id == PlanningDraftAssignment.draft_agent_day_id)
            .filter(PlanningDraftAgentDay.draft_id == draft.id)
            .all()
        )

        created_agent_day_by_draft_day_id: dict[int, AgentDay] = {}
        for draft_day in draft_days:
            official_day = AgentDay(
                agent_id=draft_day.agent_id,
                day_date=draft_day.day_date,
                day_type=draft_day.day_type,
                description=draft_day.description,
                is_off_shift=draft_day.is_off_shift,
            )
            session.add(official_day)
            session.flush()
            created_agent_day_by_draft_day_id[draft_day.id] = official_day

        for draft_assignment in draft_assignments:
            official_day = created_agent_day_by_draft_day_id.get(draft_assignment.draft_agent_day_id)
            if official_day is None:
                continue
            session.add(AgentDayAssignment(agent_day_id=official_day.id, tranche_id=draft_assignment.tranche_id))

        now = datetime.utcnow()
        draft.status = PlanningDraftStatus.ACCEPTED.value
        draft.accepted_at = now
        draft.rejected_at = None

        (
            session.query(PlanningDraft)
            .filter(
                PlanningDraft.id != draft.id,
                PlanningDraft.team_id == draft.team_id,
                PlanningDraft.start_date == draft.start_date,
                PlanningDraft.end_date == draft.end_date,
                PlanningDraft.status.in_(
                    [
                        PlanningDraftStatus.QUEUED.value,
                        PlanningDraftStatus.RUNNING.value,
                        PlanningDraftStatus.SUCCESS.value,
                        PlanningDraftStatus.FAILED.value,
                    ]
                ),
            )
            .update({PlanningDraft.status: PlanningDraftStatus.SUPERSEDED.value}, synchronize_session=False)
        )

        logger.info(
            "planning_draft.accepted",
            extra={
                "draft_id": draft.id,
                "team_id": draft.team_id,
                "start_date": str(draft.start_date),
                "end_date": str(draft.end_date),
                "actor_user_id": actor_user_id,
            },
        )

    session.commit()
    session.refresh(draft)
    return _build_accept_response(draft)


def reject_draft(session: Session, draft_id: int, actor_user_id: int | None = None) -> DraftRejectResult:
    with session.begin_nested():
        draft = _get_draft_for_update_or_404(session, draft_id)
        draft_status = PlanningDraftStatus(draft.status)

        if draft_status == PlanningDraftStatus.REJECTED:
            return DraftRejectResult(draft_id=draft.id, status=PlanningDraftStatus.REJECTED)
        if draft_status == PlanningDraftStatus.ACCEPTED:
            conflict("Planning draft has already been accepted")

        draft.status = PlanningDraftStatus.REJECTED.value
        draft.rejected_at = datetime.utcnow()

        logger.info(
            "planning_draft.rejected",
            extra={
                "draft_id": draft.id,
                "team_id": draft.team_id,
                "start_date": str(draft.start_date),
                "end_date": str(draft.end_date),
                "actor_user_id": actor_user_id,
            },
        )

    session.commit()
    session.refresh(draft)
    return DraftRejectResult(draft_id=draft.id, status=PlanningDraftStatus(draft.status))
