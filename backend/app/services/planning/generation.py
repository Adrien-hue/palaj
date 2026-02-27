from __future__ import annotations

import logging
from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.services.solver.interface import SolverService
from backend.app.services.solver.mapper import SolverInputMapper
from backend.app.services.solver.models import CoverageDemand, SolverInput, SolverOutput, TrancheInfo
from backend.app.services.solver.ortools_solver import OrtoolsSolver
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import PlanningDraft, PlanningDraftAgentDay, PlanningDraftAssignment, Team

from db import db

logger = logging.getLogger(__name__)


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
        )
        session.add(draft)
        session.flush()
        conn = session.connection()
        logger.warning(
            "DB_DEBUG_CREATE job_id=%s draft_id=%s db_url=%s",
            draft.job_id,
            draft.id,
            str(conn.engine.url),
        )
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
            conn = session.connection()
            logger.warning(
                "DB_DEBUG_RUN job_id=%s db_url=%s",
                normalized_job_id,
                str(conn.engine.url),
            )
            draft_count = session.query(PlanningDraft).count()
            logger.warning("DB_DEBUG_RUN draft_count=%s", draft_count)
            draft = session.query(PlanningDraft).filter(PlanningDraft.job_id == normalized_job_id).first()

            existing = session.query(PlanningDraft.id, PlanningDraft.job_id).order_by(PlanningDraft.id.desc()).limit(10).all()
            logger.warning("DB_DEBUG_RUN last_drafts=%s", existing)
            logger.warning("DB_DEBUG_RUN looking_for=%r", normalized_job_id)

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

                hard_infeasible_count, hard_infeasible_sample = self._compute_hard_infeasible_stats(
                    demands=coverage_demands,
                    tranches=tranches,
                    agent_ids=team_agent_ids,
                    qualified_postes_by_agent=sorted_qualified_postes_by_agent,
                    absences=absences,
                )

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
                        poste_ids=poste_ids,
                        tranches=tranches,
                        coverage_demands=coverage_demands,
                    )
                )

                self._persist_output(session=session, draft=draft, solver_output=solver_output)

                stats = dict(solver_output.stats)
                stats["absence_count"] = len(absences)
                stats["demand_count"] = len(coverage_demands)
                stats["tranche_count"] = len(tranches)
                stats["poste_count"] = len(poste_ids)
                stats["agent_count"] = len(team_agent_ids)
                stats["ignored_coverage_requirements_count"] = ignored_coverage_requirements_count
                stats["covered_poste_ids_count"] = len(poste_ids)
                stats["ignored_poste_ids_sample"] = ignored_poste_ids_sample
                stats["hard_infeasible_demands_count"] = hard_infeasible_count
                stats["hard_infeasible_demands_sample"] = hard_infeasible_sample

                draft.result_stats = stats
                draft.status = PlanningDraftStatus.SUCCESS.value
                draft.error = None
                session.commit()

                logger.info(
                    "planning_generation.run_job.success",
                    extra={"draft_id": draft.id, "job_id": normalized_job_id},
                )
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
