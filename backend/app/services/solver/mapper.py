from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import AgentDay, AgentTeam, PosteCoverageRequirement, Qualification, Tranche

from .models import CoverageDemand, TrancheInfo

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CoverageRequirementPattern:
    poste_id: int
    weekday: int
    tranche_id: int
    required_count: int


class SolverInputMapper:
    """Prépare les données DB pour le solver à partir des entités métier persistées."""

    def __init__(self, session: Session):
        self.session = session

    def list_team_agent_ids(self, team_id: int) -> list[int]:
        rows = self.session.execute(select(AgentTeam.agent_id).where(AgentTeam.team_id == team_id)).all()
        return sorted(agent_id for (agent_id,) in rows)

    def list_qualified_postes_by_agent(self, agent_ids: list[int]) -> dict[int, set[int]]:
        qualified_postes_by_agent: dict[int, set[int]] = {agent_id: set() for agent_id in sorted(agent_ids)}
        if not agent_ids:
            return qualified_postes_by_agent

        rows = self.session.execute(
            select(Qualification.agent_id, Qualification.poste_id)
            .where(Qualification.agent_id.in_(agent_ids))
            .order_by(Qualification.agent_id, Qualification.poste_id)
        ).all()
        for agent_id, poste_id in rows:
            qualified_postes_by_agent.setdefault(agent_id, set()).add(poste_id)

        return qualified_postes_by_agent

    def normalize_qualified_postes_by_agent(
        self,
        agent_ids: list[int],
        qualified_postes_by_agent: dict[int, set[int]],
    ) -> dict[int, tuple[int, ...]]:
        return {
            agent_id: tuple(sorted(qualified_postes_by_agent.get(agent_id, set())))
            for agent_id in sorted(agent_ids)
        }


    def list_qualification_dates(
        self,
        agent_ids: list[int],
    ) -> dict[tuple[int, int], date | None]:
        qualification_date_by_agent_poste: dict[tuple[int, int], date | None] = {}
        if not agent_ids:
            return qualification_date_by_agent_poste

        rows = self.session.execute(
            select(Qualification.agent_id, Qualification.poste_id, Qualification.date_qualification)
            .where(Qualification.agent_id.in_(agent_ids))
            .order_by(Qualification.agent_id, Qualification.poste_id)
        ).all()
        for agent_id, poste_id, qualification_date in rows:
            qualification_date_by_agent_poste[(agent_id, poste_id)] = qualification_date

        return qualification_date_by_agent_poste

    def list_existing_day_types(
        self,
        agent_ids: list[int],
        start_date: date,
        end_date: date,
    ) -> dict[tuple[int, date], str]:
        if not agent_ids:
            return {}

        rows = self.session.execute(
            select(AgentDay.agent_id, AgentDay.day_date, AgentDay.day_type)
            .where(AgentDay.agent_id.in_(agent_ids))
            .where(AgentDay.day_date >= start_date, AgentDay.day_date <= end_date)
            .order_by(AgentDay.day_date, AgentDay.agent_id)
        ).all()

        return {(agent_id, day_date): day_type for agent_id, day_date, day_type in rows}

    def list_team_poste_ids(self, qualified_postes_by_agent: dict[int, set[int]]) -> set[int]:
        return {poste_id for postes in qualified_postes_by_agent.values() for poste_id in postes}

    def list_tranches_for_postes(self, poste_ids: set[int]) -> list[TrancheInfo]:
        if not poste_ids:
            return []

        tranches = self.session.execute(
            select(Tranche.id, Tranche.poste_id)
            .where(Tranche.poste_id.in_(poste_ids))
            .order_by(Tranche.id)
        ).all()
        return [TrancheInfo(id=tranche_id, poste_id=poste_id) for tranche_id, poste_id in tranches]

    def list_coverage_requirements(self, poste_ids: set[int]) -> list[CoverageRequirementPattern]:
        if not poste_ids:
            return []

        rows = self.session.execute(
            select(
                PosteCoverageRequirement.poste_id,
                PosteCoverageRequirement.weekday,
                PosteCoverageRequirement.tranche_id,
                PosteCoverageRequirement.required_count,
            )
            .where(PosteCoverageRequirement.poste_id.in_(poste_ids))
            .order_by(
                PosteCoverageRequirement.weekday,
                PosteCoverageRequirement.tranche_id,
                PosteCoverageRequirement.poste_id,
            )
        ).all()
        return [
            CoverageRequirementPattern(
                poste_id=poste_id,
                weekday=weekday,
                tranche_id=tranche_id,
                required_count=required_count,
            )
            for poste_id, weekday, tranche_id, required_count in rows
        ]

    def summarize_ignored_coverage_requirements(self, poste_ids: set[int]) -> tuple[int, list[int]]:
        if poste_ids:
            ignored_poste_rows = self.session.execute(
                select(PosteCoverageRequirement.poste_id)
                .where(~PosteCoverageRequirement.poste_id.in_(poste_ids))
                .distinct()
                .order_by(PosteCoverageRequirement.poste_id)
            ).all()
        else:
            ignored_poste_rows = self.session.execute(
                select(PosteCoverageRequirement.poste_id)
                .distinct()
                .order_by(PosteCoverageRequirement.poste_id)
            ).all()

        ignored_poste_ids = [poste_id for (poste_id,) in ignored_poste_rows]

        total = self.session.execute(select(func.count(PosteCoverageRequirement.id))).scalar_one()
        if not poste_ids:
            return int(total), ignored_poste_ids[:10]

        covered = self.session.execute(
            select(func.count(PosteCoverageRequirement.id)).where(PosteCoverageRequirement.poste_id.in_(poste_ids))
        ).scalar_one()
        return int(total - covered), ignored_poste_ids[:10]

    def expand_requirements_to_demands(
        self,
        requirements: list[CoverageRequirementPattern],
        start_date: date,
        end_date: date,
        existing_tranche_ids: set[int],
    ) -> list[CoverageDemand]:
        demands: list[CoverageDemand] = []

        req_by_weekday: dict[int, list[CoverageRequirementPattern]] = {i: [] for i in range(7)}
        for requirement in requirements:
            req_by_weekday.setdefault(requirement.weekday, []).append(requirement)

        cursor = start_date
        while cursor <= end_date:
            for requirement in req_by_weekday.get(cursor.weekday(), []):
                if requirement.tranche_id not in existing_tranche_ids:
                    continue
                demands.append(
                    CoverageDemand(
                        day_date=cursor,
                        tranche_id=requirement.tranche_id,
                        required_count=requirement.required_count,
                        poste_id=requirement.poste_id,
                    )
                )
            cursor += timedelta(days=1)

        demands.sort(key=lambda d: (d.day_date, d.tranche_id))
        return demands

    def list_absences(self, agent_ids: list[int], start_date: date, end_date: date) -> set[tuple[int, date]]:
        if not agent_ids:
            return set()

        rows = self.session.execute(
            select(AgentDay.agent_id, AgentDay.day_date)
            .where(AgentDay.agent_id.in_(agent_ids))
            .where(AgentDay.day_date >= start_date, AgentDay.day_date <= end_date)
            .where(AgentDay.day_type.in_(("absent", "leave")))
            .order_by(AgentDay.day_date, AgentDay.agent_id)
        ).all()

        absences = {(agent_id, day_date) for agent_id, day_date in rows}
        logger.info("Loaded %s absences for agent_ids=%s", len(absences), len(agent_ids))
        return absences
