from __future__ import annotations

from datetime import date, timedelta
import pytest

from backend.app.settings import settings

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1"


def _login(client, username: str, password: str):
    r = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"
    assert settings.access_cookie_name in client.cookies
    assert settings.refresh_cookie_name in client.cookies


def test_agent_planning_requires_auth(client):
    today = date.today()
    r = client.get(f"{API}/agents/1/planning?start_date={today}&end_date={today}")
    assert r.status_code == 401, r.text


def test_agent_planning_invalid_range_is_400(client):
    _login(client, "admin", "admin123")

    start = date.today()
    end = start - timedelta(days=1)  # volontairement invalide
    r = client.get(f"{API}/agents/1/planning?start_date={start}&end_date={end}")
    assert r.status_code == 400, r.text


def test_agents_planning_days_batch(client):
    _login(client, "admin", "admin123")

    payload = {
        "agent_ids": [1, 2],
        "day_date": str(date.today()),
    }
    r = client.post(f"{API}/agents/planning/days/batch", json=payload)
    assert r.status_code == 200, r.text

    data = r.json()
    assert "day_date" in data
    assert "items" in data
    assert data["day_date"] == payload["day_date"]
