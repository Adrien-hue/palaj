from __future__ import annotations

from datetime import date, time, timedelta
from importlib.util import find_spec
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend.app.services.planning.generation import PlanningGenerationService
from backend.app.services.solver.ortools_solver import OrtoolsSolver
from backend.app.settings import settings
from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import (
    Agent,
    AgentTeam,
    PlanningDraft,
    PlanningDraftAgentDay,
    PlanningDraftAssignment,
    Poste,
    Team,
    Tranche,
)

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1"
HTTPX_MISSING = find_spec("httpx") is None


class _TestDbAdapter:
    def __init__(self, bind):
        self._session_factory = sessionmaker(bind=bind, expire_on_commit=False, autoflush=False, autocommit=False)

    def session_scope(self):
        class _SessionManager:
            def __init__(self, session_factory):
                self._session_factory = session_factory
                self._session = None

            def __enter__(self):
                self._session = self._session_factory()
                return self._session

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self._session is None:
                    return
                try:
                    if exc_type:
                        self._session.rollback()
                    else:
                        self._session.commit()
                finally:
                    self._session.close()

        return _SessionManager(self._session_factory)


def _build_generation_service(db_session: Session) -> PlanningGenerationService:
    return PlanningGenerationService(solver=OrtoolsSolver(), database=_TestDbAdapter(db_session.get_bind()))


def _login(client, username: str, password: str):
    r = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    assert settings.access_cookie_name in client.cookies
    assert settings.refresh_cookie_name in client.cookies


def _seed_team(db_session: Session, agent_count: int = 1) -> Team:
    team = Team(name=f"Team draft read {uuid4()}", description=None)
    db_session.add(team)
    db_session.flush()

    for idx in range(agent_count):
        agent = Agent(
            actif=True,
            nom=f"Doe-{idx}",
            prenom="Jane",
            code_personnel=f"A-{idx}",
            regime_id=None,
        )
        db_session.add(agent)
        db_session.flush()
        db_session.add(AgentTeam(agent_id=agent.id, team_id=team.id))

    db_session.commit()
    return team


def _create_manual_draft(db_session: Session, team_id: int, start_date: date, end_date: date) -> PlanningDraft:
    draft = PlanningDraft(
        job_id=str(uuid4()),
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        status=PlanningDraftStatus.SUCCESS.value,
        seed=123,
        time_limit_seconds=60,
        result_stats={"solver_status": "OPTIMAL"},
        error=None,
    )
    db_session.add(draft)
    db_session.flush()
    return draft


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_draft_team_planning_happy_path(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=2)

    start_date = date.today()
    end_date = start_date + timedelta(days=2)

    generation_service = _build_generation_service(db_session)
    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=17,
        time_limit_seconds=60,
    )
    db_session.commit()
    generation_service.run_job(str(draft.job_id))

    response = client.get(f"{API}/planning/drafts/{draft.id}/team-planning")
    assert response.status_code == 200, response.text

    data = response.json()
    expected_days = (end_date - start_date).days + 1

    assert data["team"]["id"] == team.id
    assert data["start_date"] == str(start_date)
    assert data["end_date"] == str(end_date)
    assert len(data["days"]) == expected_days
    assert len(data["agents"]) == 2

    first_agent_days = data["agents"][0]["days"]
    assert len(first_agent_days) == expected_days
    assert [row["day_date"] for row in first_agent_days] == sorted(row["day_date"] for row in first_agent_days)
    assert all(isinstance(row["tranches"], list) for row in first_agent_days)


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_draft_team_planning_unknown_draft_returns_404(client):
    _login(client, "admin", "admin123")

    response = client.get(f"{API}/planning/drafts/999999/team-planning")
    assert response.status_code == 404, response.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_get_draft_team_planning_missing_day_row_returns_default_rest(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=1)

    start_date = date.today() + timedelta(days=5)
    end_date = start_date + timedelta(days=2)

    generation_service = _build_generation_service(db_session)
    draft = generation_service.create_draft(
        session=db_session,
        team_id=team.id,
        start_date=start_date,
        end_date=end_date,
        seed=21,
        time_limit_seconds=60,
    )
    db_session.commit()
    generation_service.run_job(str(draft.job_id))

    removable_day = (
        db_session.query(PlanningDraftAgentDay)
        .filter(PlanningDraftAgentDay.draft_id == draft.id)
        .order_by(PlanningDraftAgentDay.day_date.asc())
        .first()
    )
    assert removable_day is not None
    missing_date = removable_day.day_date
    db_session.delete(removable_day)
    db_session.commit()

    response = client.get(f"{API}/planning/drafts/{draft.id}/team-planning")
    assert response.status_code == 200, response.text

    payload = response.json()
    agent_days = payload["agents"][0]["days"]
    missing_row = next(day for day in agent_days if day["day_date"] == str(missing_date))

    assert missing_row["day_type"] == "rest"
    assert missing_row["description"] is None
    assert missing_row["is_off_shift"] is False
    assert missing_row["tranches"] == []

    draft_days = payload["days"]
    assert len(draft_days) == (end_date - start_date).days + 1


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_tranches_sorted_and_unique(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=1)

    agent_id = (
        db_session.query(AgentTeam.agent_id)
        .filter(AgentTeam.team_id == team.id)
        .one()[0]
    )
    target_date = date.today() + timedelta(days=10)

    poste = Poste(nom=f"Poste draft sort {uuid4()}")
    db_session.add(poste)
    db_session.flush()

    later_tranche = Tranche(
        nom=f"Later tranche {uuid4()}",
        heure_debut=time(10, 0),
        heure_fin=time(12, 0),
        poste_id=poste.id,
        color="#FF0000",
    )
    earlier_tranche = Tranche(
        nom=f"Earlier tranche {uuid4()}",
        heure_debut=time(8, 0),
        heure_fin=time(9, 0),
        poste_id=poste.id,
        color="#00FF00",
    )
    db_session.add(later_tranche)
    db_session.add(earlier_tranche)
    db_session.flush()

    draft = _create_manual_draft(db_session, team.id, target_date, target_date)
    draft_day = PlanningDraftAgentDay(
        draft_id=draft.id,
        agent_id=agent_id,
        day_date=target_date,
        day_type="working",
        description="manual",
        is_off_shift=False,
    )
    db_session.add(draft_day)
    db_session.flush()

    db_session.add(
        PlanningDraftAssignment(
            draft_agent_day_id=draft_day.id,
            tranche_id=later_tranche.id,
        )
    )
    db_session.add(
        PlanningDraftAssignment(
            draft_agent_day_id=draft_day.id,
            tranche_id=earlier_tranche.id,
        )
    )
    db_session.commit()

    response = client.get(f"{API}/planning/drafts/{draft.id}/team-planning")
    assert response.status_code == 200, response.text

    payload = response.json()
    day = payload["agents"][0]["days"][0]
    returned_tranches = day["tranches"]

    assert [tranche["heure_debut"] for tranche in returned_tranches] == ["08:00:00", "10:00:00"]
    returned_ids = [tranche["id"] for tranche in returned_tranches]
    assert len(returned_ids) == len(set(returned_ids))


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_no_cross_draft_leak(client, db_session: Session):
    _login(client, "admin", "admin123")
    team = _seed_team(db_session, agent_count=1)

    agent_id = (
        db_session.query(AgentTeam.agent_id)
        .filter(AgentTeam.team_id == team.id)
        .one()[0]
    )
    target_date = date.today() + timedelta(days=20)

    poste = Poste(nom=f"Poste draft leak {uuid4()}")
    db_session.add(poste)
    db_session.flush()

    leak_tranche = Tranche(
        nom=f"Leak tranche {uuid4()}",
        heure_debut=time(7, 0),
        heure_fin=time(8, 0),
        poste_id=poste.id,
        color="#123456",
    )
    db_session.add(leak_tranche)
    db_session.flush()

    draft1 = _create_manual_draft(db_session, team.id, target_date, target_date)
    draft1_day = PlanningDraftAgentDay(
        draft_id=draft1.id,
        agent_id=agent_id,
        day_date=target_date,
        day_type="working",
        description="d1",
        is_off_shift=False,
    )
    db_session.add(draft1_day)

    draft2 = _create_manual_draft(db_session, team.id, target_date, target_date)
    draft2_day = PlanningDraftAgentDay(
        draft_id=draft2.id,
        agent_id=agent_id,
        day_date=target_date,
        day_type="working",
        description="d2",
        is_off_shift=False,
    )
    db_session.add(draft2_day)
    db_session.flush()

    db_session.add(
        PlanningDraftAssignment(
            draft_agent_day_id=draft2_day.id,
            tranche_id=leak_tranche.id,
        )
    )
    db_session.commit()

    response = client.get(f"{API}/planning/drafts/{draft1.id}/team-planning")
    assert response.status_code == 200, response.text

    payload = response.json()
    day = payload["agents"][0]["days"][0]
    assert day["tranches"] == []
