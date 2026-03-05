from __future__ import annotations

from datetime import date, time, timedelta
from importlib.util import find_spec
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from core.domain.enums.planning_draft_status import PlanningDraftStatus
from db.models import (
    Agent,
    AgentDay,
    AgentDayAssignment,
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


def _login(client, username: str, password: str):
    response = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text


def _seed_team_with_one_agent(db_session: Session) -> tuple[Team, Agent]:
    team = Team(name=f"Team decision {uuid4()}", description=None)
    db_session.add(team)
    db_session.flush()

    agent = Agent(
        actif=True,
        nom="Doe",
        prenom="Jane",
        code_personnel=f"A-{uuid4()}",
        regime_id=None,
    )
    db_session.add(agent)
    db_session.flush()
    db_session.add(AgentTeam(agent_id=agent.id, team_id=team.id))
    db_session.commit()
    return team, agent


def _create_tranche(db_session: Session) -> Tranche:
    poste = Poste(nom=f"Poste {uuid4()}")
    db_session.add(poste)
    db_session.flush()
    tranche = Tranche(
        nom=f"Tranche {uuid4()}",
        heure_debut=time(8, 0),
        heure_fin=time(12, 0),
        poste_id=poste.id,
        color="#123456",
    )
    db_session.add(tranche)
    db_session.commit()
    return tranche


def _create_official_planning(db_session: Session, agent_id: int, day_date: date, tranche_id: int, description: str = "official-old"):
    day = AgentDay(
        agent_id=agent_id,
        day_date=day_date,
        day_type="working",
        description=description,
        is_off_shift=False,
    )
    db_session.add(day)
    db_session.flush()
    db_session.add(AgentDayAssignment(agent_day_id=day.id, tranche_id=tranche_id))
    db_session.commit()


def _create_draft(
    db_session: Session,
    team_id: int,
    agent_id: int,
    start_date: date,
    end_date: date,
    tranche_id: int,
    status: PlanningDraftStatus = PlanningDraftStatus.SUCCESS,
) -> PlanningDraft:
    draft = PlanningDraft(
        job_id=str(uuid4()),
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        status=status.value,
        seed=42,
        time_limit_seconds=60,
        result_stats={"solver_status": "OPTIMAL"} if status == PlanningDraftStatus.SUCCESS else None,
        error=None,
    )
    db_session.add(draft)
    db_session.flush()

    current_day = start_date
    while current_day <= end_date:
        draft_day = PlanningDraftAgentDay(
            draft_id=draft.id,
            agent_id=agent_id,
            day_date=current_day,
            day_type="working",
            description=f"draft-{current_day.isoformat()}",
            is_off_shift=False,
        )
        db_session.add(draft_day)
        db_session.flush()
        db_session.add(PlanningDraftAssignment(draft_agent_day_id=draft_day.id, tranche_id=tranche_id))
        current_day += timedelta(days=1)

    db_session.commit()
    return draft


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_accept_draft_replaces_official_planning_for_period(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    old_tranche = _create_tranche(db_session)
    new_tranche = _create_tranche(db_session)

    start = date.today() + timedelta(days=2)
    end = start + timedelta(days=1)

    _create_official_planning(db_session, agent.id, start, old_tranche.id)
    draft = _create_draft(db_session, team.id, agent.id, start, end, new_tranche.id)

    response = client.post(f"{API}/planning/drafts/{draft.id}/accept")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["published"] is True

    official_days = (
        db_session.query(AgentDay)
        .filter(AgentDay.agent_id == agent.id, AgentDay.day_date >= start, AgentDay.day_date <= end)
        .order_by(AgentDay.day_date.asc())
        .all()
    )
    assert len(official_days) == 2
    assert official_days[0].description == f"draft-{start.isoformat()}"
    assert official_days[1].description == f"draft-{end.isoformat()}"

    assignments = (
        db_session.query(AgentDayAssignment)
        .join(AgentDay, AgentDay.id == AgentDayAssignment.agent_day_id)
        .filter(AgentDay.agent_id == agent.id, AgentDay.day_date >= start, AgentDay.day_date <= end)
        .all()
    )
    assert len(assignments) == 2
    assert {a.tranche_id for a in assignments} == {new_tranche.id}


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_reject_draft_does_not_change_official_planning(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)

    start = date.today() + timedelta(days=5)
    _create_official_planning(db_session, agent.id, start, tranche.id)
    draft = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)

    before_ids = [row.id for row in db_session.query(AgentDay).filter(AgentDay.agent_id == agent.id).all()]

    response = client.post(f"{API}/planning/drafts/{draft.id}/reject")
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "rejected"

    after_ids = [row.id for row in db_session.query(AgentDay).filter(AgentDay.agent_id == agent.id).all()]
    assert after_ids == before_ids


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_accept_invalid_state_returns_409(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)
    start = date.today() + timedelta(days=8)

    draft = PlanningDraft(
        job_id=str(uuid4()),
        team_id=team.id,
        start_date=start,
        end_date=start,
        status=PlanningDraftStatus.RUNNING.value,
        seed=1,
        time_limit_seconds=60,
    )
    db_session.add(draft)
    db_session.commit()

    response = client.post(f"{API}/planning/drafts/{draft.id}/accept")
    assert response.status_code == 409, response.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_authz_manager_required(client, db_session: Session):
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)
    start = date.today() + timedelta(days=12)
    draft = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)

    _login(client, "user", "user123")
    response = client.post(f"{API}/planning/drafts/{draft.id}/accept")
    assert response.status_code == 403, response.text


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_accept_does_not_touch_official_outside_period(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    old_tranche = _create_tranche(db_session)
    new_tranche = _create_tranche(db_session)

    start = date.today() + timedelta(days=20)
    end = start + timedelta(days=1)
    outside_day = start - timedelta(days=1)

    _create_official_planning(db_session, agent.id, outside_day, old_tranche.id, description="outside")
    _create_official_planning(db_session, agent.id, start, old_tranche.id, description="inside")
    draft = _create_draft(db_session, team.id, agent.id, start, end, new_tranche.id)

    response = client.post(f"{API}/planning/drafts/{draft.id}/accept")
    assert response.status_code == 200, response.text

    outside = (
        db_session.query(AgentDay)
        .filter(AgentDay.agent_id == agent.id, AgentDay.day_date == outside_day)
        .one()
    )
    assert outside.description == "outside"

    inside_days = (
        db_session.query(AgentDay)
        .filter(AgentDay.agent_id == agent.id, AgentDay.day_date >= start, AgentDay.day_date <= end)
        .all()
    )
    assert len(inside_days) == 2


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_supersede_only_exact_same_range(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)

    start = date.today() + timedelta(days=30)
    draft_target = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)
    draft_other_range = _create_draft(db_session, team.id, agent.id, start, start + timedelta(days=1), tranche.id)
    draft_same_range = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)

    response = client.post(f"{API}/planning/drafts/{draft_target.id}/accept")
    assert response.status_code == 200, response.text

    db_session.refresh(draft_same_range)
    db_session.refresh(draft_other_range)
    assert draft_same_range.status == PlanningDraftStatus.SUPERSEDED.value
    assert draft_other_range.status == PlanningDraftStatus.SUCCESS.value


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_accept_idempotent_double_call(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)
    start = date.today() + timedelta(days=40)
    draft = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)

    response1 = client.post(f"{API}/planning/drafts/{draft.id}/accept")
    response2 = client.post(f"{API}/planning/drafts/{draft.id}/accept")

    assert response1.status_code == 200, response1.text
    assert response2.status_code == 200, response2.text
    assert response1.json() == response2.json()


@pytest.mark.skipif(HTTPX_MISSING, reason="httpx required for TestClient")
def test_reject_idempotent_double_call(client, db_session: Session):
    _login(client, "admin", "admin123")
    team, agent = _seed_team_with_one_agent(db_session)
    tranche = _create_tranche(db_session)
    start = date.today() + timedelta(days=45)
    draft = _create_draft(db_session, team.id, agent.id, start, start, tranche.id)

    response1 = client.post(f"{API}/planning/drafts/{draft.id}/reject")
    response2 = client.post(f"{API}/planning/drafts/{draft.id}/reject")

    assert response1.status_code == 200, response1.text
    assert response2.status_code == 200, response2.text
    assert response1.json() == response2.json()
