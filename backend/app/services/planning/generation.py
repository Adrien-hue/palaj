from __future__ import annotations

import logging
from datetime import date
from numbers import Real
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.services.solver.interface import SolverService
from backend.app.services.solver.mapper import SolverInputMapper
from backend.app.services.solver.models import (
    CoverageDemand,
    InfeasibleError,
    SolverInput,
    SolverOutput,
    TimeoutError,
    TrancheInfo,
)
from backend.app.services.solver.ortools_solver import OrtoolsSolver
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import PlanningDraft, PlanningDraftAgentDay, PlanningDraftAssignment, Team

from db import db

logger = logging.getLogger(__name__)


def _json_safe(value):
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Real):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def merge_stats(*dicts: dict | None) -> dict[str, object]:
    merged: dict[str, object] = {}
    for item in dicts:
        if not item:
            continue
        for key, value in item.items():
            merged[str(key)] = _json_safe(value)
    return merged


class PlanningGenerationService:
    def __init__(self, solver: SolverService, database):
        self.solver = solver
        self.db = database

    def create_draft(
        self,
        session: Session,
        team_id: int,
        start_date: date,
        end_date: date,
        seed: int | None,
        time_limit_seconds: int,
        quality_profile: str = "balanced",
        v3_strategy: str = "two_phase_lns",
        phase1_fraction: float | None = None,
        phase1_seconds: float | None = None,
        lns_iter_seconds: float | None = None,
        lns_min_remaining_seconds: float | None = None,
        lns_strict_improve: bool = True,
        lns_max_days_to_relax: int | None = None,
        lns_neighborhood_mode: str = "poste_only",
        min_lns_seconds: float | None = None,
        phase2_max_fraction_of_remaining: float | None = None,
        phase2_no_improve_seconds: float | None = None,
        enable_decision_strategy: bool | None = None,
        enable_symmetry_breaking: bool | None = None,
    ) -> PlanningDraft:
        team = session.get(Team, team_id)
        if team is None:
            raise ValueError(f"Team {team_id} not found")

        draft = PlanningDraft(
            job_id=str(uuid4()),
            team_id=team_id,
            start_date=start_date,
            end_date=end_date,
            status=PlanningDraftStatus.QUEUED.value,
            seed=seed,
            time_limit_seconds=time_limit_seconds,
            solver_options={
                "quality_profile": quality_profile,
                "v3_strategy": v3_strategy,
                "phase1_fraction": phase1_fraction,
                "phase1_seconds": phase1_seconds,
                "lns_iter_seconds": lns_iter_seconds,
                "lns_min_remaining_seconds": lns_min_remaining_seconds,
                "lns_strict_improve": lns_strict_improve,
                "lns_max_days_to_relax": lns_max_days_to_relax,
                "lns_neighborhood_mode": lns_neighborhood_mode,
                "min_lns_seconds": min_lns_seconds,
                "phase2_max_fraction_of_remaining": phase2_max_fraction_of_remaining,
                "phase2_no_improve_seconds": phase2_no_improve_seconds,
                "enable_decision_strategy": enable_decision_strategy,
                "enable_symmetry_breaking": enable_symmetry_breaking,
            },
        )
        session.add(draft)
        session.flush()
        logger.error("planning_generation.create_draft", extra={"draft_id": draft.id, "job_id": draft.job_id})
        return draft

    def _compute_hard_infeasible_stats(
        self,
        demands: list[CoverageDemand],
        tranches: list[TrancheInfo],
        agent_ids: list[int],
        qualified_postes_by_agent: dict[int, tuple[int, ...]],
        absences: set[tuple[int, date]],
    ) -> tuple[int, list[dict[str, int | str]]]:
        tranche_to_poste = {tranche.id: tranche.poste_id for tranche in tranches}

        qualified_agents_by_poste: dict[int, set[int]] = {}
        for agent_id, poste_ids in qualified_postes_by_agent.items():
            for poste_id in poste_ids:
                qualified_agents_by_poste.setdefault(poste_id, set()).add(agent_id)

        all_agents = set(agent_ids)
        absences_by_day: dict[date, set[int]] = {}
        for agent_id, day_date in absences:
            absences_by_day.setdefault(day_date, set()).add(agent_id)

        available_agents_by_day: dict[date, set[int]] = {}
        for demand in demands:
            available_agents_by_day.setdefault(
                demand.day_date,
                all_agents - absences_by_day.get(demand.day_date, set()),
            )

        hard_infeasible_count = 0
        hard_infeasible_sample: list[dict[str, int | str]] = []

        for demand in demands:
            poste_id = tranche_to_poste.get(demand.tranche_id)
            if poste_id is None:
                continue

            qualified_agents = qualified_agents_by_poste.get(poste_id, set())
            available_agents = available_agents_by_day.get(demand.day_date, set())
            capacity = len(qualified_agents & available_agents)

            if capacity < demand.required_count:
                hard_infeasible_count += 1
                if len(hard_infeasible_sample) < 10:
                    hard_infeasible_sample.append(
                        {
                            "day_date": demand.day_date.isoformat(),
                            "tranche_id": demand.tranche_id,
                            "required_count": demand.required_count,
                            "capacity": capacity,
                        }
                    )

        return hard_infeasible_count, hard_infeasible_sample

    def run_job(self, job_id: str) -> None:
        normalized_job_id = str(job_id)
        logger.error(
            "planning_generation.run_job.start",
            extra={"job_id": normalized_job_id, "job_id_type": type(job_id).__name__},
        )

        with self.db.session_scope() as session:
            draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == normalized_job_id).first()

            if draft is None:
                logger.error(
                    "planning_generation.run_job.missing_draft",
                    extra={"job_id": normalized_job_id, "job_id_type": type(job_id).__name__},
                )
                return

            try:
                draft.status = PlanningDraftStatus.RUNNING.value
                session.commit()

                mapper = SolverInputMapper(session=session)
                team_agent_ids = mapper.list_team_agent_ids(team_id=draft.team_id)
                raw_qualified_postes_by_agent = mapper.list_qualified_postes_by_agent(agent_ids=team_agent_ids)
                sorted_qualified_postes_by_agent = mapper.normalize_qualified_postes_by_agent(
                    agent_ids=team_agent_ids,
                    qualified_postes_by_agent=raw_qualified_postes_by_agent,
                )

                poste_ids = sorted(mapper.list_team_poste_ids(qualified_postes_by_agent=raw_qualified_postes_by_agent))
                tranches = mapper.list_tranches_for_postes(poste_ids=set(poste_ids))
                requirements = mapper.list_coverage_requirements(poste_ids=set(poste_ids))
                ignored_coverage_requirements_count, ignored_poste_ids_sample = mapper.summarize_ignored_coverage_requirements(
                    poste_ids=set(poste_ids)
                )

                coverage_demands = mapper.expand_requirements_to_demands(
                    requirements=requirements,
                    start_date=draft.start_date,
                    end_date=draft.end_date,
                    existing_tranche_ids={tranche.id for tranche in tranches},
                )
                absences = mapper.list_absences(
                    agent_ids=team_agent_ids,
                    start_date=draft.start_date,
                    end_date=draft.end_date,
                )
                qualification_date_by_agent_poste = mapper.list_qualification_dates(agent_ids=team_agent_ids)
                existing_day_type_by_agent_day = mapper.list_existing_day_types(
                    agent_ids=team_agent_ids,
                    start_date=draft.start_date,
                    end_date=draft.end_date,
                )
                gpt_context_days = mapper.list_gpt_context_days(start_date=draft.start_date, end_date=draft.end_date)
                existing_day_type_by_agent_day_ctx = mapper.list_existing_day_types_context(
                    agent_ids=team_agent_ids,
                    start_date=draft.start_date,
                    end_date=draft.end_date,
                )
                (
                    existing_work_minutes_by_agent_day_ctx,
                    existing_shift_start_end_by_agent_day_ctx,
                ) = mapper.list_existing_work_context(
                    agent_ids=team_agent_ids,
                    start_date=draft.start_date,
                    end_date=draft.end_date,
                )

                hard_infeasible_count, hard_infeasible_sample = self._compute_hard_infeasible_stats(
                    demands=coverage_demands,
                    tranches=tranches,
                    agent_ids=team_agent_ids,
                    qualified_postes_by_agent=sorted_qualified_postes_by_agent,
                    absences=absences,
                )
                mapper_debug_stats = {
                    "absence_count": len(absences),
                    "demand_count": len(coverage_demands),
                    "tranche_count": len(tranches),
                    "poste_count": len(poste_ids),
                    "agent_count": len(team_agent_ids),
                    "ignored_coverage_requirements_count": ignored_coverage_requirements_count,
                    "covered_poste_ids_count": len(poste_ids),
                    "ignored_poste_ids_sample": ignored_poste_ids_sample,
                    "hard_infeasible_demands_count": hard_infeasible_count,
                    "hard_infeasible_demands_sample": hard_infeasible_sample,
                }

                solver_opts = draft.solver_options or {}
                solver_output = self.solver.generate(
                    SolverInput(
                        team_id=draft.team_id,
                        start_date=draft.start_date,
                        end_date=draft.end_date,
                        seed=draft.seed,
                        time_limit_seconds=draft.time_limit_seconds,
                        agent_ids=team_agent_ids,
                        absences=absences,
                        qualified_postes_by_agent=sorted_qualified_postes_by_agent,
                        qualification_date_by_agent_poste=qualification_date_by_agent_poste,
                        existing_day_type_by_agent_day=existing_day_type_by_agent_day,
                        gpt_context_days=gpt_context_days,
                        existing_day_type_by_agent_day_ctx=existing_day_type_by_agent_day_ctx,
                        existing_work_minutes_by_agent_day_ctx=existing_work_minutes_by_agent_day_ctx,
                        existing_shift_start_end_by_agent_day_ctx=existing_shift_start_end_by_agent_day_ctx,
                        poste_ids=poste_ids,
                        tranches=tranches,
                        coverage_demands=coverage_demands,
                        quality_profile=str(solver_opts.get("quality_profile", "balanced")),
                        v3_strategy=str(solver_opts.get("v3_strategy", "two_phase_lns")),
                        phase1_fraction=solver_opts.get("phase1_fraction"),
                        phase1_seconds=solver_opts.get("phase1_seconds"),
                        lns_iter_seconds=solver_opts.get("lns_iter_seconds"),
                        lns_min_remaining_seconds=solver_opts.get("lns_min_remaining_seconds"),
                        lns_strict_improve=bool(solver_opts.get("lns_strict_improve", True)),
                        lns_max_days_to_relax=solver_opts.get("lns_max_days_to_relax"),
                        lns_neighborhood_mode=str(solver_opts.get("lns_neighborhood_mode", "poste_only")),
                        min_lns_seconds=solver_opts.get("min_lns_seconds"),
                        phase2_max_fraction_of_remaining=solver_opts.get("phase2_max_fraction_of_remaining"),
                        phase2_no_improve_seconds=solver_opts.get("phase2_no_improve_seconds"),
                        enable_decision_strategy=solver_opts.get("enable_decision_strategy"),
                        enable_symmetry_breaking=solver_opts.get("enable_symmetry_breaking"),
                    )
                )

                self._persist_output(session=session, draft=draft, solver_output=solver_output)

                stats = merge_stats(mapper_debug_stats, solver_output.stats)

                draft.result_stats = stats
                draft.status = PlanningDraftStatus.SUCCESS.value
                draft.error = None
                session.commit()

                logger.info(
                    "planning_generation.run_job.success",
                    extra={"draft_id": draft.id, "job_id": normalized_job_id},
                )
                return
            except TimeoutError as exc:
                session.rollback()

                failed_draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == normalized_job_id).first()
                if failed_draft is not None:
                    failed_draft.status = PlanningDraftStatus.FAILED.value
                    failed_draft.error = "timeout"
                    failed_draft.result_stats = merge_stats(
                        mapper_debug_stats,
                        getattr(exc, "stats", {}),
                        {
                            "solver_status": "TIMEOUT",
                            "solver_status_raw": "UNKNOWN",
                            "normalized_solver_status": "TIMEOUT",
                            "coverage_ratio": 0,
                        },
                    )
                    session.commit()

                logger.warning(
                    "planning_generation.run_job.timeout",
                    extra={"draft_id": failed_draft.id if failed_draft else None, "job_id": normalized_job_id},
                )
                return
            except InfeasibleError as exc:
                session.rollback()

                failed_draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == normalized_job_id).first()
                if failed_draft is None:
                    return
                failed_draft.status = PlanningDraftStatus.FAILED.value
                failed_draft.error = "infeasible"
                failed_draft.result_stats = merge_stats(
                    mapper_debug_stats,
                    getattr(exc, "stats", {}),
                    {"solver_status": "INFEASIBLE", "coverage_ratio": 0, "normalized_solver_status": "INFEASIBLE"},
                )
                session.commit()

                logger.info(
                    "planning_generation.run_job.infeasible",
                    extra={"draft_id": failed_draft.id if failed_draft else None, "job_id": normalized_job_id},
                )
                return
            except Exception as exc:  # pragma: no cover
                logger.exception(
                    "planning_generation.run_job.failure",
                    extra={"draft_id": getattr(draft, "id", None), "job_id": normalized_job_id},
                )
                session.rollback()

                failed_draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == normalized_job_id).first()
                if failed_draft is None:
                    return
                failed_draft.status = PlanningDraftStatus.FAILED.value
                failed_draft.error = str(exc)
                session.commit()

    def _persist_output(self, session: Session, draft: PlanningDraft, solver_output: SolverOutput) -> None:
        by_key: dict[tuple[int, date], PlanningDraftAgentDay] = {}

        for item in solver_output.agent_days:
            model = PlanningDraftAgentDay(
                draft_id=draft.id,
                agent_id=item.agent_id,
                day_date=item.day_date,
                day_type=item.day_type,
                description=item.description,
                is_off_shift=item.is_off_shift,
            )
            session.add(model)
            session.flush()
            by_key[(item.agent_id, item.day_date)] = model

        for assignment in solver_output.assignments:
            agent_day = by_key.get((assignment.agent_id, assignment.day_date))
            if agent_day is None:
                raise ValueError(
                    "Solver assignment references unknown agent-day "
                    f"(agent_id={assignment.agent_id}, day_date={assignment.day_date})"
                )
            session.add(
                PlanningDraftAssignment(
                    draft_agent_day_id=agent_day.id,
                    tranche_id=assignment.tranche_id,
                )
            )


planning_generation_service = PlanningGenerationService(solver=OrtoolsSolver(), database=db)
