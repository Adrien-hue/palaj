from __future__ import annotations

from datetime import date, time, timedelta

# TODO: adapte ces imports à ton projet
from db import db
from db.models.agent import Agent as AgentModel
from db.models.poste import Poste as PosteModel
from db.models.tranche import Tranche as TrancheModel
from db.models.agent_day import AgentDay as AgentDayModel
from db.models.agent_day_assignment import AgentDayAssignment as AgentDayAssignmentModel


def seed():
    agent_nom = "HOUEE"
    agent_prenom = "Adrien"
    agent_code = "0106135P"

    poste_nom = "POSTE_TEST"
    tranche_nom = "T1"
    tranche_start = time(6, 0)
    tranche_end = time(14, 0)

    start = date(2026, 1, 1)
    end = date(2026, 1, 7)

    with db.session_scope() as session:
        # -------------------------
        # 1) Agent
        # -------------------------
        agent = AgentModel(nom=agent_nom, prenom=agent_prenom, code_personnel=agent_code, actif=True)
        session.add(agent)
        session.flush()  # pour avoir agent.id

        # -------------------------
        # 2) Poste (si nécessaire)
        # -------------------------
        poste = PosteModel(nom=poste_nom)
        session.add(poste)
        session.flush()

        # -------------------------
        # 3) Tranche
        # -------------------------
        tranche = TrancheModel(
            nom=tranche_nom,
            heure_debut=tranche_start,
            heure_fin=tranche_end,
            poste_id=poste.id,
        )
        session.add(tranche)
        session.flush()

        # -------------------------
        # 4) AgentDays + 5) Assignments
        # -------------------------
        current = start
        while current <= end:
            day = AgentDayModel(
                agent_id=agent.id,
                day_date=current,
                day_type="working",
                description=None,
                is_off_shift=False,
            )
            session.add(day)
            session.flush()  # pour day.id

            # Liaison tranche <-> jour
            link = AgentDayAssignmentModel(
                agent_day_id=day.id,
                tranche_id=tranche.id,
            )
            session.add(link)

            current += timedelta(days=1)

        # commit implicite via session_scope() (selon ton impl)
        print(f"Seed OK: agent_id={agent.id}, poste_id={poste.id}, tranche_id={tranche.id}")


if __name__ == "__main__":
    seed()
