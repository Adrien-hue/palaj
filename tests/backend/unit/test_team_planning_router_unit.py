from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import (
    get_db,
    get_agent_day_service,
    get_planning_day_assembler,
    get_team_service,
    get_team_planning_factory
)
from backend.app.api.deps_current_user import current_user
from core.application.services.exceptions import NotFoundError

pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakePlanningFactoryNotFound:
    def build(self, **kwargs):
        raise NotFoundError(code="TEAM_NOT_FOUND", details={"team_id": kwargs.get("team_id")})


class _FakePlanningFactoryBadRange:
    def build(self, **kwargs):
        raise ValueError("end_date must be >= start_date")


@pytest.fixture()
def app_no_auth():
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db
    return app


@pytest.fixture()
def app_auth():
    app = create_app()

    def _override_get_db():
        yield None

    app.dependency_overrides[get_db] = _override_get_db

    def _override_current_user():
        return {"id": 1, "username": "test", "role": "admin", "is_active": True}

    app.dependency_overrides[current_user] = _override_current_user
    return app


@pytest.fixture()
def client_no_auth(app_no_auth):
    with TestClient(app_no_auth) as c:
        yield c


@pytest.fixture()
def client(app_auth):
    with TestClient(app_auth) as c:
        yield c


class _FakeTeamServiceNotFound:
    def list_agent_ids(self, team_id: int):
        raise NotFoundError(code="TEAM_NOT_FOUND", details={"team_id": team_id})


class _FakeTeamService:
    def __init__(self, agent_ids: list[int]):
        self._agent_ids = agent_ids

    def list_agent_ids(self, team_id: int):
        return self._agent_ids


class _FakeAgentDayService:
    """
    Permet de simuler un upsert qui peut lever ValueError pour certaines cellules.
    fail_on: set[(agent_id, day_date)]
    """
    def __init__(self, fail_on: set[tuple[int, date]] | None = None):
        self.fail_on = fail_on or set()
        self.calls: list[tuple[int, date]] = []

    def upsert_day(self, agent_id: int, day_date: date, day_type, tranche_id, description):
        self.calls.append((agent_id, day_date))
        if (agent_id, day_date) in self.fail_on:
            raise ValueError("boom validation")


class _FakePlanningDay:
    def __init__(self, day_date: date, day_type: str, description=None, is_off_shift: bool = False, tranches=None):
        self.day_date = day_date
        self.day_type = day_type
        self.description = description
        self.is_off_shift = is_off_shift
        self.tranches = tranches or []


class _FakePlanningDayAssembler:
    def __init__(self, day_type: str = "working", description: str | None = None):
        self.day_type = day_type
        self.description = description

    def build_one_for_agent(self, agent_id: int, day_date: date):
        # Objet minimal compatible avec to_planning_day_dto()
        return _FakePlanningDay(
            day_date=day_date,
            day_type=self.day_type,
            description=self.description,
            is_off_shift=False,
            tranches=[],
        )


def test_team_planning_requires_auth(client_no_auth):
    today = date.today()
    r = client_no_auth.get(f"{API}/teams/1/planning?start_date={today}&end_date={today}")
    assert r.status_code == 401, r.text


def test_get_team_planning_not_found_is_404_structured_detail(client, app_auth):
    app_auth.dependency_overrides[get_team_planning_factory] = lambda: _FakePlanningFactoryNotFound()

    today = date.today()
    r = client.get(f"{API}/teams/123/planning?start_date={today}&end_date={today}")
    assert r.status_code == 404, r.text

    detail = r.json()["detail"]
    assert detail["code"] == "TEAM_NOT_FOUND"
    assert "details" in detail


def test_get_team_planning_invalid_range_is_400(client, app_auth):
    app_auth.dependency_overrides[get_team_planning_factory] = lambda: _FakePlanningFactoryBadRange()

    start = date.today()
    end = start - timedelta(days=1)
    r = client.get(f"{API}/teams/1/planning?start_date={start}&end_date={end}")
    assert r.status_code == 400, r.text
    assert "end_date" in r.text.lower()


def test_team_planning_bulk_requires_auth(client_no_auth):
    payload = {
        "items": [{"agent_id": 1, "day_dates": ["2026-03-01"]}],
        "day_type": "working",
        "description": "x",
        "tranche_id": 4,
    }
    r = client_no_auth.put(f"{API}/teams/1/planning/days:bulk", json=payload)
    assert r.status_code == 401, r.text


def test_team_planning_bulk_team_not_found_is_404_structured_detail(client, app_auth):
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamServiceNotFound()
    app_auth.dependency_overrides[get_agent_day_service] = lambda: _FakeAgentDayService()
    app_auth.dependency_overrides[get_planning_day_assembler] = lambda: _FakePlanningDayAssembler()

    payload = {
        "items": [{"agent_id": 1, "day_dates": ["2026-03-01"]}],
        "day_type": "working",
        "description": "x",
        "tranche_id": 4,
    }
    r = client.put(f"{API}/teams/999/planning/days:bulk", json=payload)
    assert r.status_code == 404, r.text

    detail = r.json()["detail"]
    assert detail["code"] == "TEAM_NOT_FOUND"
    assert "details" in detail
    assert detail["details"]["team_id"] == 999


def test_team_planning_bulk_validation_working_requires_tranche_id(client, app_auth):
    # Pas besoin d'overrides: la validation Pydantic doit bloquer avant.
    payload = {
        "items": [{"agent_id": 1, "day_dates": ["2026-03-01"]}],
        "day_type": "working",
        "description": "x",
        # tranche_id manquant -> 422
    }
    r = client.put(f"{API}/teams/1/planning/days:bulk", json=payload)
    assert r.status_code == 422, r.text
    assert "tranche_id is required" in r.text


def test_team_planning_bulk_validation_non_working_must_not_have_tranche_id(client, app_auth):
    payload = {
        "items": [{"agent_id": 1, "day_dates": ["2026-03-01"]}],
        "day_type": "rest",
        "description": "x",
        "tranche_id": 4,  # interdit quand day_type != WORKING
    }
    r = client.put(f"{API}/teams/1/planning/days:bulk", json=payload)
    assert r.status_code == 422, r.text
    assert "tranche_id must be null" in r.text


def test_team_planning_bulk_validation_duplicate_agent_in_items_is_422(client, app_auth):
    payload = {
        "items": [
            {"agent_id": 1, "day_dates": ["2026-03-01"]},
            {"agent_id": 1, "day_dates": ["2026-03-02"]},  # duplicate agent_id
        ],
        "day_type": "working",
        "description": "x",
        "tranche_id": 4,
    }
    r = client.put(f"{API}/teams/1/planning/days:bulk", json=payload)
    assert r.status_code == 422, r.text
    assert "duplicate agent_id" in r.text.lower()


def test_team_planning_bulk_success_partial_failures(client, app_auth):
    # Team contient seulement agents 1 et 6
    app_auth.dependency_overrides[get_team_service] = lambda: _FakeTeamService([1, 6])

    # On force une erreur validation sur (1, 2026-03-02)
    fail_on = {(1, date(2026, 3, 2))}
    app_auth.dependency_overrides[get_agent_day_service] = lambda: _FakeAgentDayService(fail_on=fail_on)
    app_auth.dependency_overrides[get_planning_day_assembler] = lambda: _FakePlanningDayAssembler(day_type="working")

    payload = {
        "items": [
            {"agent_id": 1, "day_dates": ["2026-03-01", "2026-03-02"]},
            {"agent_id": 6, "day_dates": ["2026-03-02"]},
            {"agent_id": 7, "day_dates": ["2026-03-03", "2026-03-04"]},  # pas dans la team
        ],
        "day_type": "working",
        "description": "bulk edit",
        "tranche_id": 4,
    }

    r = client.put(f"{API}/teams/1/planning/days:bulk", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    # updated: (1, 2026-03-01) + (6, 2026-03-02) = 2
    assert len(body["updated"]) == 2, body

    # failed: (1, 2026-03-02) validation + agent 7 (2 jours) NOT_IN_TEAM = 3
    assert len(body["failed"]) == 3, body

    codes = sorted([f["code"] for f in body["failed"]])
    assert codes.count("NOT_IN_TEAM") == 2
    assert codes.count("VALIDATION_ERROR") == 1

    # check que les items updated ont bien agent_id
    updated_agent_ids = sorted([u["agent_id"] for u in body["updated"]])
    assert updated_agent_ids == [1, 6]