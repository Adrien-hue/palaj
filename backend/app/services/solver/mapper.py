from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from db.models import AgentDay, AgentTeam

logger = logging.getLogger(__name__)


class SolverInputMapper:
    """Prépare les données DB pour le solver (placeholder V1)."""

    def __init__(self, session: Session):
        self.session = session

    def list_team_agent_ids(self, team_id: int) -> list[int]:
        # TODO V2: filtrer sur les qualifications/postes éligibles.
        rows = self.session.query(AgentTeam.agent_id).filter(AgentTeam.team_id == team_id).all()
        return [agent_id for (agent_id,) in rows]

    def list_absences(self, team_id: int, start_date: date, end_date: date) -> list[AgentDay]:
        # TODO V2: enrichir avec jours fériés / indisponibilités externes.
        query = (
            self.session.query(AgentDay)
            .join(AgentTeam, AgentTeam.agent_id == AgentDay.agent_id)
            .filter(AgentTeam.team_id == team_id)
            .filter(AgentDay.day_date >= start_date, AgentDay.day_date <= end_date)
            .filter(AgentDay.day_type == "absent")
        )
        absences = query.all()
        logger.info("Loaded %s absences for team_id=%s", len(absences), team_id)
        return absences
