from __future__ import annotations

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


def test_agents_requires_auth(client):
    r = client.get(f"{API}/agents")
    assert r.status_code == 401, r.text


def test_agents_crud_flow(client):
    _login(client, "admin", "admin123")

    # CREATE
    payload = {
        "username": "agent_test_1",
        "first_name": "Agent",
        "last_name": "Test",
        # ajoute ici les champs requis réels de AgentCreateDTO
    }
    r_create = client.post(f"{API}/agents/", json=payload)
    assert r_create.status_code in (200, 201), r_create.text
    created = r_create.json()
    assert "id" in created
    agent_id = created["id"]

    # GET
    r_get = client.get(f"{API}/agents/{agent_id}")
    assert r_get.status_code == 200, r_get.text
    data = r_get.json()
    assert data["id"] == agent_id

    # LIST
    r_list = client.get(f"{API}/agents?limit=10&offset=0")
    assert r_list.status_code == 200, r_list.text
    page = r_list.json()
    assert "items" in page
    assert "total" in page

    # UPDATE: empty payload => 400
    r_bad = client.patch(f"{API}/agents/{agent_id}", json={})
    assert r_bad.status_code == 400
    assert "No fields to update" in r_bad.text

    # UPDATE: real update
    r_up = client.patch(f"{API}/agents/{agent_id}", json={"first_name": "Updated"})
    assert r_up.status_code == 200, r_up.text
    assert r_up.json()["id"] == agent_id

    # ACTIVATE/DEACTIVATE
    r_deact = client.patch(f"{API}/agents/{agent_id}/deactivate")
    assert r_deact.status_code == 204, r_deact.text

    r_act = client.patch(f"{API}/agents/{agent_id}/activate")
    assert r_act.status_code == 204, r_act.text

    # DELETE
    r_del = client.delete(f"{API}/agents/{agent_id}")
    assert r_del.status_code == 204, r_del.text

    # GET after delete => 404
    r_get2 = client.get(f"{API}/agents/{agent_id}")
    assert r_get2.status_code == 404, r_get2.text
