from __future__ import annotations

import pytest

from backend.app.settings import settings
from db.models import User
from db.models.refresh_token import RefreshToken

pytestmark = [pytest.mark.flow, pytest.mark.integration]

API = "/api/v1"

def _login(client, username: str, password: str):
    r = client.post(f"{API}/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"

    # cookies posés
    assert settings.access_cookie_name in client.cookies
    assert settings.refresh_cookie_name in client.cookies


def test_login_sets_cookies_and_me_works(client):
    _login(client, "admin", "admin123")

    r = client.get(f"{API}/auth/me")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"
    assert data["is_active"] is True


def test_login_bad_credentials_is_401(client):
    r = client.post(f"{API}/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401

    r2 = client.post(f"{API}/auth/login", json={"username": "nope", "password": "whatever"})
    assert r2.status_code == 401


def test_login_inactive_user_is_401(client):
    r = client.post(f"{API}/auth/login", json={"username": "inactive", "password": "inactive123"})
    assert r.status_code == 401


def test_refresh_rotates_refresh_token_and_keeps_me_working(client, db_session):
    """
    Test stable:
    - login
    - refresh => rotation refresh + access renouvelé
    - /me fonctionne toujours
    - DB: ancien refresh révoqué, nouveau actif
    """
    _login(client, "user", "user123")

    old_refresh = client.cookies.get(settings.refresh_cookie_name)
    assert old_refresh

    r = client.post(f"{API}/auth/refresh")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"

    new_refresh = client.cookies.get(settings.refresh_cookie_name)
    assert new_refresh
    assert new_refresh != old_refresh  # rotation

    # /me doit fonctionner
    r_me = client.get(f"{API}/auth/me")
    assert r_me.status_code == 200, r_me.text

    # DB : l'ancien refresh est révoqué, le nouveau actif (pour le user "user")
    user = db_session.query(User).filter(User.username == "user").first()
    assert user is not None

    rows = (
        db_session.query(RefreshToken)
        .filter(RefreshToken.user_id == user.id)
        .order_by(RefreshToken.id.desc())
        .limit(10)
        .all()
    )
    assert len(rows) >= 2
    assert rows[0].revoked_at is None
    assert any(rt.revoked_at is not None for rt in rows[1:])

@pytest.mark.slow
def test_refresh_reuse_detection_revokes_all_sessions(client, db_session):
    """
    Mode strict:
    - refresh normal => rotation => ancien refresh révoqué
    - relecture/replay de l'ancien refresh => 401
    - tous les refresh tokens du user révoqués
    """
    _login(client, "user", "user123")
    old_refresh = client.cookies.get(settings.refresh_cookie_name)
    assert old_refresh

    # 1) refresh normal -> rotation (ancien révoqué)
    r1 = client.post(f"{API}/auth/refresh")
    assert r1.status_code == 200, r1.text

    new_refresh = client.cookies.get(settings.refresh_cookie_name)
    assert new_refresh != old_refresh

    # 2) Simule un attaquant qui rejoue l'ancien refresh (révoqué)
    client.cookies.set(settings.refresh_cookie_name, old_refresh, path="/")

    r2 = client.post(f"{API}/auth/refresh")
    assert r2.status_code == 401, r2.text

    # 3) Vérifie que tout est révoqué en DB pour ce user uniquement
    user = db_session.query(User).filter(User.username == "user").first()
    assert user is not None

    tokens = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).all()
    assert tokens, "No refresh tokens in DB to validate reuse detection"
    assert all(t.revoked_at is not None for t in tokens), "Expected all user refresh tokens to be revoked"


def test_logout_revokes_refresh_and_clears_cookies(client):
    _login(client, "admin", "admin123")
    assert client.get(f"{API}/auth/me").status_code == 200

    r = client.post(f"{API}/auth/logout")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # cookies supprimés
    assert client.cookies.get(settings.access_cookie_name) is None
    assert client.cookies.get(settings.refresh_cookie_name) is None

    # plus authentifié
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.post(f"{API}/auth/refresh").status_code == 401


def test_logout_all_revokes_sessions_across_clients(app, db_session):
    """
    Deux clients = deux sessions (refresh tokens).
    logout-all sur l'un doit invalider l'autre.
    """
    from fastapi.testclient import TestClient

    c1 = TestClient(app)
    c2 = TestClient(app)
    try:
        r1 = c1.post(f"{API}/auth/login", json={"username": "user", "password": "user123"})
        assert r1.status_code == 200

        r2 = c2.post(f"{API}/auth/login", json={"username": "user", "password": "user123"})
        assert r2.status_code == 200

        user = db_session.query(User).filter(User.username == "user").first()
        assert user is not None

        tokens_before = db_session.query(RefreshToken).filter(RefreshToken.user_id == user.id).all()
        assert len(tokens_before) >= 2

        r_lo = c1.post(f"{API}/auth/logout-all")
        assert r_lo.status_code == 200, r_lo.text

        # c2 doit être invalidé
        assert c2.post(f"{API}/auth/refresh").status_code == 401
        assert c2.get(f"{API}/auth/me").status_code == 401

    finally:
        c1.close()
        c2.close()


def test_admin_ping_rbac(client):
    # user normal -> 403/401 (selon impl)
    _login(client, "user", "user123")
    r = client.get(f"{API}/admin/ping")
    assert r.status_code in (401, 403), r.text
    client.post(f"{API}/auth/logout")

    # admin -> 200
    _login(client, "admin", "admin123")
    r2 = client.get(f"{API}/admin/ping")
    assert r2.status_code == 200, r2.text
    assert r2.json()["status"] == "ok"
