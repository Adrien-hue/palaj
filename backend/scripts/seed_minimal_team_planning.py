from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Iterable, Optional

from sqlalchemy import select, delete

from db import db

# --- Models (adapte les chemins/noms si besoin) ---
from db.models.agent import Agent as AgentModel
from db.models.poste import Poste as PosteModel
from db.models.tranche import Tranche as TrancheModel
from db.models.agent_day import AgentDay as AgentDayModel
from db.models.agent_day_assignment import AgentDayAssignment as AgentDayAssignmentModel
from db.models.team import Team as TeamModel
from db.models.agent_team import AgentTeam as AgentTeamModel

# Si ton modèle s'appelle autrement, adapte l'import.
# Dans ton API, une qualification ressemble à {agent_id, poste_id, date_qualification}
from db.models.qualification import Qualification as QualificationModel


# -------------------------
# Config seed
# -------------------------
POSTE_NAME = "GTI"
TEAM_NAME = "GTI"
TEAM_DESC = "Équipe GTI (seed)"

TRANCHES = [
    ("GTI M", time(6, 15), time(14, 5)),
    ("GTI S", time(13, 55), time(22, 0)),
    ("GTI N", time(22, 0), time(6, 15)),
]

AGENTS = [
    ("HOUEE", "Adrien", "0106135P"),
    ("BLANCHARD", "Thibault", "0106136P"),
    ("MOREAU", "Romain", "0106137P"),
]

START = date(2026, 1, 1)
END = date(2026, 1, 31)


# -------------------------
# Helpers: get or create
# -------------------------
def get_or_create_poste(session, name: str) -> PosteModel:
    poste = session.execute(select(PosteModel).where(PosteModel.nom == name)).scalar_one_or_none()
    if poste:
        return poste
    poste = PosteModel(nom=name)
    session.add(poste)
    session.flush()
    return poste


def get_or_create_tranche(session, poste_id: int, nom: str, h_debut: time, h_fin: time) -> TrancheModel:
    tranche = session.execute(
        select(TrancheModel).where(TrancheModel.poste_id == poste_id, TrancheModel.nom == nom)
    ).scalar_one_or_none()
    if tranche:
        # On s'assure que les heures sont conformes à la demande
        tranche.heure_debut = h_debut
        tranche.heure_fin = h_fin
        session.flush()
        return tranche

    tranche = TrancheModel(nom=nom, heure_debut=h_debut, heure_fin=h_fin, poste_id=poste_id)
    session.add(tranche)
    session.flush()
    return tranche


def get_or_create_team(session, name: str, description: Optional[str] = None) -> TeamModel:
    team = session.execute(select(TeamModel).where(TeamModel.name == name)).scalar_one_or_none()
    if team:
        team.description = description
        session.flush()
        return team
    team = TeamModel(name=name, description=description)
    session.add(team)
    session.flush()
    return team


def get_or_create_agent(session, nom: str, prenom: str, code_personnel: str) -> AgentModel:
    # On prend code_personnel comme clé stable
    agent = session.execute(select(AgentModel).where(AgentModel.code_personnel == code_personnel)).scalar_one_or_none()
    if agent:
        agent.nom = nom
        agent.prenom = prenom
        agent.actif = True
        session.flush()
        return agent

    agent = AgentModel(nom=nom, prenom=prenom, code_personnel=code_personnel, actif=True)
    session.add(agent)
    session.flush()
    return agent


def ensure_team_membership(session, agent_id: int, team_id: int) -> None:
    link = session.execute(
        select(AgentTeamModel).where(AgentTeamModel.agent_id == agent_id, AgentTeamModel.team_id == team_id)
    ).scalar_one_or_none()
    if link:
        return
    session.add(AgentTeamModel(agent_id=agent_id, team_id=team_id))
    session.flush()


def ensure_qualification(session, agent_id: int, poste_id: int, q_date: date) -> None:
    q = session.execute(
        select(QualificationModel).where(
            QualificationModel.agent_id == agent_id,
            QualificationModel.poste_id == poste_id,
        )
    ).scalar_one_or_none()
    if q:
        # On conserve la date la plus ancienne si besoin
        if getattr(q, "date_qualification", None) and q.date_qualification <= q_date:
            return
        q.date_qualification = q_date
        session.flush()
        return

    q = QualificationModel(agent_id=agent_id, poste_id=poste_id, date_qualification=q_date)
    session.add(q)
    session.flush()


# -------------------------
# Planning generation
# -------------------------
@dataclass(frozen=True)
class Block:
    kind: str  # "working" | "zcot" | "rest" | "absence"
    length: int
    tranche_name: Optional[str] = None  # for working/zcot (optional)


def daterange(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def upsert_agent_day(
    session,
    *,
    agent_id: int,
    day_date: date,
    day_type: str,
    description: Optional[str] = None,
    is_off_shift: bool = False,
    tranche_id: Optional[int] = None,
) -> None:
    """
    Respecte uq_agent_days_agent_date.
    Si le jour existe, on le met à jour et on remplace les assignments.
    """
    day = session.execute(
        select(AgentDayModel).where(AgentDayModel.agent_id == agent_id, AgentDayModel.day_date == day_date)
    ).scalar_one_or_none()

    if day is None:
        day = AgentDayModel(
            agent_id=agent_id,
            day_date=day_date,
            day_type=day_type,
            description=description,
            is_off_shift=is_off_shift,
        )
        session.add(day)
        session.flush()
    else:
        day.day_type = day_type
        day.description = description
        day.is_off_shift = is_off_shift
        session.flush()
        # remove existing assignments (replace)
        session.execute(delete(AgentDayAssignmentModel).where(AgentDayAssignmentModel.agent_day_id == day.id))
        session.flush()

    if tranche_id is not None:
        session.add(AgentDayAssignmentModel(agent_day_id=day.id, tranche_id=tranche_id))
        session.flush()


def build_month_plan_for_agent(agent_index: int) -> list[Block]:
    """
    Génère un planning cohérent:
    - blocs travail/zcot: 3-6 jours
    - blocs repos: 1-3 jours
    - 1 agent avec une absence de 2 jours
    Rotation tranches: T1 -> T2 -> T3 -> ...
    """
    # Rotation des tranches selon l'agent pour varier
    tranche_cycle = ["GTI M", "GTI S", "GTI N"]
    start_offset = agent_index % 3
    tranche_cycle = tranche_cycle[start_offset:] + tranche_cycle[:start_offset]

    blocks: list[Block] = []
    # Semaine 1
    blocks += [Block("working", 5, tranche_cycle[0]), Block("rest", 2)]
    # Semaine 2 (introduit un zcot)
    blocks += [Block("zcot", 4, tranche_cycle[1]), Block("rest", 2)]
    # Semaine 3 (absence pour un agent)
    if agent_index == 1:  # Thibault
        blocks += [Block("working", 3, tranche_cycle[2]), Block("absence", 2), Block("rest", 2)]
    else:
        blocks += [Block("working", 5, tranche_cycle[2]), Block("rest", 2)]
    # Semaine 4/fin de mois
    blocks += [Block("working", 4, tranche_cycle[0]), Block("rest", 2), Block("working", 3, tranche_cycle[1])]

    return blocks


def materialize_blocks_to_days(blocks: list[Block], start: date, end: date) -> list[tuple[date, Block]]:
    out: list[tuple[date, Block]] = []
    current = start
    for b in blocks:
        for _ in range(b.length):
            if current > end:
                return out
            out.append((current, b))
            current += timedelta(days=1)
        if current > end:
            break
    # Si on n'a pas rempli tout le mois, on met du rest
    while current <= end:
        out.append((current, Block("rest", 1)))
        current += timedelta(days=1)
    return out


# -------------------------
# Seed entrypoint
# -------------------------
def seed(reset_days_for_agents: bool = True) -> None:
    """
    reset_days_for_agents=True:
      - supprime les AgentDays du mois de janvier 2026 pour ces agents avant de recréer
      - laisse le reste intact
    """

    with db.session_scope() as session:
        # 1) Poste + tranches
        poste = get_or_create_poste(session, POSTE_NAME)
        tranches_by_name: dict[str, TrancheModel] = {}
        for nom, h1, h2 in TRANCHES:
            tranches_by_name[nom] = get_or_create_tranche(session, poste.id, nom, h1, h2)

        # 2) Team
        team = get_or_create_team(session, TEAM_NAME, TEAM_DESC)

        # 3) Agents + qualifications + membership
        agents: list[AgentModel] = []
        for nom, prenom, code in AGENTS:
            a = get_or_create_agent(session, nom, prenom, code)
            agents.append(a)
            ensure_qualification(session, a.id, poste.id, START)  # qualification au 01/01/2026
            ensure_team_membership(session, a.id, team.id)

        # 4) Optionnel: reset AgentDays du mois pour ces agents
        if reset_days_for_agents:
            agent_ids = [a.id for a in agents]
            # delete assignments first via cascade? on supprime explicitement
            days_to_delete = session.execute(
                select(AgentDayModel.id).where(
                    AgentDayModel.agent_id.in_(agent_ids),
                    AgentDayModel.day_date >= START,
                    AgentDayModel.day_date <= END,
                )
            ).scalars().all()

            if days_to_delete:
                session.execute(
                    delete(AgentDayAssignmentModel).where(AgentDayAssignmentModel.agent_day_id.in_(days_to_delete))
                )
                session.execute(
                    delete(AgentDayModel).where(AgentDayModel.id.in_(days_to_delete))
                )
                session.flush()

        # 5) Génération planning janvier 2026
        for idx, a in enumerate(agents):
            blocks = build_month_plan_for_agent(idx)
            timeline = materialize_blocks_to_days(blocks, START, END)

            for d, b in timeline:
                if b.kind == "working":
                    tranche_id = tranches_by_name[b.tranche_name].id if b.tranche_name else None
                    upsert_agent_day(
                        session,
                        agent_id=a.id,
                        day_date=d,
                        day_type="working",
                        description=None,
                        is_off_shift=False,
                        tranche_id=tranche_id,
                    )
                elif b.kind == "zcot":
                    # Selon ton métier, zcot peut avoir une tranche ou non.
                    # Ici: on met une tranche (cohérent avec la matrice) + day_type="zcot".
                    upsert_agent_day(
                        session,
                        agent_id=a.id,
                        day_date=d,
                        day_type="zcot",
                        description="ZCOT",
                        is_off_shift=False,
                        tranche_id=None,
                    )
                elif b.kind == "absence":
                    upsert_agent_day(
                        session,
                        agent_id=a.id,
                        day_date=d,
                        day_type="absent",
                        description="ABSENCE",
                        is_off_shift=False,
                        tranche_id=None,
                    )
                else:  # rest
                    upsert_agent_day(
                        session,
                        agent_id=a.id,
                        day_date=d,
                        day_type="rest",
                        description=None,
                        is_off_shift=False,
                        tranche_id=None,
                    )

        print(
            "Seed OK ✅\n"
            f"- Poste: {poste.nom} (id={poste.id})\n"
            f"- Tranches: {', '.join([f'{k}(id={v.id})' for k, v in tranches_by_name.items()])}\n"
            f"- Team: {team.name} (id={team.id})\n"
            f"- Agents: {', '.join([f'{a.prenom} {a.nom}(id={a.id})' for a in agents])}\n"
            f"- Période: {START} -> {END}\n"
            f"- reset_days_for_agents={reset_days_for_agents}"
        )


if __name__ == "__main__":
    seed(reset_days_for_agents=True)
