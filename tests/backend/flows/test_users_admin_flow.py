from __future__ import annotations

import uuid

import pytest

from backend.app.api.deps_current_user import current_user
from backend.app.security.password import verify_password
from db.models import User

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1/users"


def _request(client, method: str, path: str, json: dict | None = None):
    return client.request(method=method, url=path, json=json)


def _override_as_admin(app, db_session):
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    def _admin_user():
        return admin_user

    app.dependency_overrides[current_user] = _admin_user


def test_users_routes_require_authentication(client):
    endpoints = [
        ("POST", API, {"username": "u", "password": "password123", "role": "manager", "is_active": True}),
        ("GET", API, None),
        ("GET", f"{API}/1", None),
        ("PATCH", f"{API}/1", {"username": "updated"}),
        ("DELETE", f"{API}/1", None),
    ]

    for method, path, payload in endpoints:
        resp = _request(client, method, path, payload)
        assert resp.status_code == 401, (method, path, resp.text)


def test_users_routes_forbid_non_admin(app, client):
    def _manager_user():
        return User(id=999, username="manager", password_hash="x", role="manager", is_active=True)

    app.dependency_overrides[current_user] = _manager_user

    endpoints = [
        ("POST", API, {"username": "u2", "password": "password123", "role": "manager", "is_active": True}),
        ("GET", API, None),
        ("GET", f"{API}/1", None),
        ("PATCH", f"{API}/1", {"username": "updated"}),
        ("DELETE", f"{API}/1", None),
    ]

    for method, path, payload in endpoints:
        resp = _request(client, method, path, payload)
        assert resp.status_code == 403, (method, path, resp.text)

    app.dependency_overrides.pop(current_user, None)


def test_admin_users_crud_flow(app, client, db_session):
    _override_as_admin(app, db_session)

    suffix = uuid.uuid4().hex[:8]
    username = f"new-user-{suffix}"

    create_resp = client.post(
        API,
        json={
            "username": f"  {username}  ",
            "password": "password123",
            "role": "manager",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    created = create_resp.json()
    assert created["username"] == username
    assert created["role"] == "manager"
    assert created["is_active"] is True
    assert "password_hash" not in created
    user_id = created["id"]

    list_resp = client.get(API)
    assert list_resp.status_code == 200, list_resp.text
    users = list_resp.json()
    assert any(item["id"] == user_id for item in users)

    detail_resp = client.get(f"{API}/{user_id}")
    assert detail_resp.status_code == 200, detail_resp.text
    assert detail_resp.json()["username"] == username

    patch_resp = client.patch(
        f"{API}/{user_id}",
        json={"username": f" updated-{suffix} ", "role": "admin", "is_active": False},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    patched = patch_resp.json()
    assert patched["username"] == f"updated-{suffix}"
    assert patched["role"] == "admin"
    assert patched["is_active"] is False

    db_user_before_pwd = db_session.query(User).filter(User.id == user_id).first()
    assert db_user_before_pwd is not None
    old_hash = db_user_before_pwd.password_hash

    pwd_resp = client.patch(f"{API}/{user_id}", json={"password": "  newpassword123  "})
    assert pwd_resp.status_code == 200, pwd_resp.text

    db_session.expire_all()
    db_user_after_pwd = db_session.query(User).filter(User.id == user_id).first()
    assert db_user_after_pwd is not None
    assert db_user_after_pwd.password_hash != old_hash
    assert verify_password("newpassword123", db_user_after_pwd.password_hash)

    missing_resp = client.get(f"{API}/999999")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["detail"] == "Not found"

    duplicate_resp = client.post(
        API,
        json={
            "username": f"updated-{suffix}",
            "password": "password123",
            "role": "manager",
            "is_active": True,
        },
    )
    assert duplicate_resp.status_code == 409
    assert duplicate_resp.json()["detail"] == "Conflict"

    delete_resp = client.delete(f"{API}/{user_id}")
    assert delete_resp.status_code == 204, delete_resp.text

    db_session.expire_all()
    deleted_user = db_session.query(User).filter(User.id == user_id).first()
    assert deleted_user is not None
    assert deleted_user.is_active is False

    app.dependency_overrides.pop(current_user, None)


def test_admin_patch_empty_payload_and_patch_conflict(app, client, db_session):
    _override_as_admin(app, db_session)

    suffix = uuid.uuid4().hex[:8]
    first = client.post(
        API,
        json={"username": f"u1-{suffix}", "password": "password123", "role": "manager", "is_active": True},
    )
    second = client.post(
        API,
        json={"username": f"u2-{suffix}", "password": "password123", "role": "manager", "is_active": True},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    user_1 = first.json()["id"]
    username_2 = second.json()["username"]

    empty_patch = client.patch(f"{API}/{user_1}", json={})
    assert empty_patch.status_code == 400
    assert empty_patch.json()["detail"] == "Invalid payload"

    conflict_patch = client.patch(f"{API}/{user_1}", json={"username": username_2})
    assert conflict_patch.status_code == 409
    assert conflict_patch.json()["detail"] == "Conflict"

    app.dependency_overrides.pop(current_user, None)


def test_delete_nonexistent_returns_404(app, client, db_session):
    _override_as_admin(app, db_session)

    resp = client.delete(f"{API}/999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Not found"

    app.dependency_overrides.pop(current_user, None)


def test_list_include_inactive_filter(app, client, db_session):
    _override_as_admin(app, db_session)

    suffix = uuid.uuid4().hex[:8]
    active_resp = client.post(
        API,
        json={"username": f"active-{suffix}", "password": "password123", "role": "manager", "is_active": True},
    )
    inactive_resp = client.post(
        API,
        json={"username": f"inactive-{suffix}", "password": "password123", "role": "manager", "is_active": False},
    )
    assert active_resp.status_code == 201
    assert inactive_resp.status_code == 201

    active_id = active_resp.json()["id"]
    inactive_id = inactive_resp.json()["id"]

    default_list = client.get(API)
    assert default_list.status_code == 200
    default_ids = {item["id"] for item in default_list.json()}
    assert active_id in default_ids
    assert inactive_id not in default_ids

    include_inactive_list = client.get(f"{API}?include_inactive=true")
    assert include_inactive_list.status_code == 200
    include_ids = {item["id"] for item in include_inactive_list.json()}
    assert active_id in include_ids
    assert inactive_id in include_ids

    app.dependency_overrides.pop(current_user, None)


def test_self_demote_and_self_delete_are_forbidden(app, client, db_session):
    _override_as_admin(app, db_session)
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    demote_resp = client.patch(f"{API}/{admin_user.id}", json={"role": "manager"})
    assert demote_resp.status_code == 403
    assert demote_resp.json()["detail"] == "Forbidden"

    deactivate_resp = client.patch(f"{API}/{admin_user.id}", json={"is_active": False})
    assert deactivate_resp.status_code == 403
    assert deactivate_resp.json()["detail"] == "Forbidden"

    delete_resp = client.delete(f"{API}/{admin_user.id}")
    assert delete_resp.status_code == 403
    assert delete_resp.json()["detail"] == "Forbidden"

    app.dependency_overrides.pop(current_user, None)
