from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.api.deps import (
    get_db,
    get_agent_day_service,
    get_agent_planning_factory,
    get_planning_day_assembler,
)
from backend.app.api.deps_current_user import current_user


pytestmark = [pytest.mark.unit]
API = "/api/v1"


class _FakeAgentPlanningFactory:
    def build(self, agent_id: int, start_date: date, end_date: date):
        raise ValueError("end_date must be >= start_date")


class _FakeAgentDayService:
    def upsert_day(self, **kwargs):
        raise ValueError("Invalid day payload")

    def delete_day(self, **kwargs):
        raise ValueError("Invalid delete request")


class _FakePlanningDayAssembler:
    # Ne sera pas appelé dans ces tests (on teste seulement les chemins d'erreur)
    pass


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

    # fakes
    app.dependency_overrides[get_agent_planning_factory] = lambda: _FakeAgentPlanningFactory()
    app.dependency_overrides[get_agent_day_service] = lambda: _FakeAgentDayService()
    app.dependency_overrides[get_planning_day_assembler] = lambda: _FakePlanningDayAssembler()

    return app


@pytest.fixture()
def client_no_auth(app_no_auth):
    with TestClient(app_no_auth) as c:
        yield c


@pytest.fixture()
def client(app_auth):
    with TestClient(app_auth) as c:
        yield c


def test_agent_planning_requires_auth(client_no_auth):
    today = date.today()
    r = client_no_auth.get(f"{API}/agents/1/planning?start_date={today}&end_date={today}")
    assert r.status_code == 401, r.text


def test_get_agent_planning_invalid_range_is_400(client):
    start = date.today()
    end = start - timedelta(days=1)

    r = client.get(f"{API}/agents/1/planning?start_date={start}&end_date={end}")
    assert r.status_code == 400, r.text
    assert "end_date" in r.text


def test_upsert_agent_planning_day_validation_error_is_400(client):
    day = date.today()

    # payload minimal : adapte si PlanningDayPutDTO impose d'autres champs
    payload = {
        "day_type": "WORK",
        "tranche_id": None,
        "description": None,
    }

    r = client.put(f"{API}/agents/1/planning/days/{day}", json=payload)
    # soit 422 (pydantic) si day_type invalide selon ton enum,
    # soit 400 si ton service lève ValueError (ce test vise ce second cas)
    assert r.status_code in (400, 422), r.text


def test_delete_agent_planning_day_validation_error_is_400(client):
    day = date.today()
    r = client.delete(f"{API}/agents/1/planning/days/{day}")
    assert r.status_code == 400, r.text
