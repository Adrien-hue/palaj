# tests/core/services/test_auth_service.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List

import pytest

from backend.app.settings import settings

# Importe ton service + erreurs
from core.application.services.auth_service import AuthService, AuthError, LoginResult

# Importe le modèle RefreshToken (SQLAlchemy mapped ok, on l'utilise juste en objet Python)
from db.models.refresh_token import RefreshToken

pytestmark = [pytest.mark.unit]

# -----------------------------
# Fakes (repos + user)
# -----------------------------
@dataclass
class FakeUser:
    id: int
    username: str
    password_hash: str
    role: str
    is_active: bool = True


class FakeUserRepo:
    def __init__(self, users: List[FakeUser]):
        self.by_username: Dict[str, FakeUser] = {u.username: u for u in users}
        self.by_id: Dict[int, FakeUser] = {u.id: u for u in users}

    def get_by_username(self, username: str) -> Optional[FakeUser]:
        return self.by_username.get(username)

    def get_by_id(self, user_id: int) -> Optional[FakeUser]:
        return self.by_id.get(user_id)


class FakeRefreshTokenRepo:
    """
    Stocke les RefreshToken en mémoire.
    Les token_hash doivent être uniques.
    """
    def __init__(self):
        self.tokens: List[RefreshToken] = []
        self._commits = 0

    def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return next((t for t in self.tokens if t.token_hash == token_hash), None)

    def add(self, token: RefreshToken) -> None:
        self.tokens.append(token)

    def revoke(self, token: RefreshToken, now: datetime) -> None:
        token.revoked_at = now

    def revoke_by_hash_if_active(self, token_hash: str, now: datetime) -> bool:
        rt = self.get_by_hash(token_hash)
        if not rt or rt.revoked_at is not None:
            return False
        rt.revoked_at = now
        return True

    def revoke_all_for_user(self, user_id: int, now: datetime) -> int:
        count = 0
        for t in self.tokens:
            if t.user_id == user_id and t.revoked_at is None:
                t.revoked_at = now
                count += 1
        return count

    def commit(self) -> None:
        self._commits += 1


# -----------------------------
# Helpers
# -----------------------------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture(autouse=True)
def _test_settings():
    """
    Settings minimales pour que JWT + hashing refresh fonctionnent en test.
    """
    settings.jwt_secret = "TEST_SECRET"
    settings.jwt_algorithm = "HS256"
    settings.jwt_issuer = "palaj-api"
    settings.jwt_audience = "palaj-web"
    settings.access_token_minutes = 15

    settings.refresh_token_days = 30
    settings.refresh_token_pepper = "TEST_PEPPER"

    yield


@pytest.fixture()
def user_repo():
    # hash_password est déjà dans ton projet et Argon2; on veut de vrais hashes.
    from backend.app.security.password import hash_password

    return FakeUserRepo([
        FakeUser(
            id=1,
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
        ),
        FakeUser(
            id=2,
            username="user",
            password_hash=hash_password("user123"),
            role="user",
            is_active=True,
        ),
        FakeUser(
            id=3,
            username="inactive",
            password_hash=hash_password("inactive123"),
            role="user",
            is_active=False,
        ),
    ])


@pytest.fixture()
def rt_repo():
    return FakeRefreshTokenRepo()


@pytest.fixture()
def auth_service(user_repo, rt_repo):
    return AuthService(users=user_repo, refresh_tokens=rt_repo)


def _set_deterministic_refresh_tokens(monkeypatch, seq: List[str]):
    """
    AuthService importe generate_refresh_token directement,
    donc il faut patcher dans le module auth_service.
    """
    import core.application.services.auth_service as auth_service_module

    it = iter(seq)

    def _fake_generate_refresh_token() -> str:
        return next(it)

    monkeypatch.setattr(auth_service_module, "generate_refresh_token", _fake_generate_refresh_token)


def _force_refresh_expires_at(monkeypatch, expires_at: datetime):
    """
    Patch refresh_expires_at() pour contrôler expires_at facilement.
    """
    import core.application.services.auth_service as auth_service_module
    monkeypatch.setattr(auth_service_module, "refresh_expires_at", lambda: expires_at)


# -----------------------------
# Tests
# -----------------------------
@pytest.mark.unit
def test_login_success_creates_token_pair_and_persists_refresh(monkeypatch, auth_service, rt_repo):
    # refresh token déterministe
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1"])
    _force_refresh_expires_at(monkeypatch, utcnow() + timedelta(days=30))

    pair = auth_service.login("user", "user123", user_agent="pytest", ip="127.0.0.1")

    assert isinstance(pair, LoginResult)
    assert pair.access_token  # jwt non vide
    assert pair.refresh_token == "rt_1"

    assert len(rt_repo.tokens) == 1
    assert rt_repo.tokens[0].user_id == 2
    assert rt_repo.tokens[0].revoked_at is None
    assert rt_repo._commits == 1


@pytest.mark.unit
def test_login_bad_credentials_raises(auth_service):
    with pytest.raises(AuthError):
        auth_service.login("user", "wrong", user_agent=None, ip=None)

    with pytest.raises(AuthError):
        auth_service.login("nope", "whatever", user_agent=None, ip=None)


@pytest.mark.unit
def test_login_inactive_user_raises(auth_service):
    with pytest.raises(AuthError):
        auth_service.login("inactive", "inactive123", user_agent=None, ip=None)


@pytest.mark.unit
def test_refresh_rotates_refresh_and_revokes_old(monkeypatch, auth_service, rt_repo):
    # 1) login -> refresh token rt_1
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1", "rt_2"])
    _force_refresh_expires_at(monkeypatch, utcnow() + timedelta(days=30))

    login_pair = auth_service.login("user", "user123", user_agent="pytest", ip=None)
    assert login_pair.refresh_token == "rt_1"
    assert len(rt_repo.tokens) == 1

    # 2) refresh avec rt_1 -> rotation vers rt_2
    refresh_pair = auth_service.refresh("rt_1", user_agent="pytest", ip=None)

    assert refresh_pair.refresh_token == "rt_2"
    assert refresh_pair.access_token
    assert refresh_pair.access_token != login_pair.access_token  # nouveau JWT (jti change)

    assert len(rt_repo.tokens) == 2

    # ancien révoqué
    old = rt_repo.tokens[0]
    assert old.revoked_at is not None

    # nouveau actif
    new = rt_repo.tokens[1]
    assert new.revoked_at is None


@pytest.mark.unit
def test_refresh_expired_revokes_all_and_raises(monkeypatch, auth_service, rt_repo):
    # 1) login avec refresh expiré
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1"])
    _force_refresh_expires_at(monkeypatch, utcnow() - timedelta(seconds=1))

    auth_service.login("user", "user123", user_agent=None, ip=None)
    assert len(rt_repo.tokens) == 1

    # 2) refresh -> doit révoquer toutes les sessions de l'user (mode strict) et lever
    with pytest.raises(AuthError):
        auth_service.refresh("rt_1", user_agent=None, ip=None)

    assert all(t.revoked_at is not None for t in rt_repo.tokens)


@pytest.mark.unit
def test_refresh_reuse_detected_revokes_all_and_raises(monkeypatch, auth_service, rt_repo):
    # 1) login => token actif
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1"])
    _force_refresh_expires_at(monkeypatch, utcnow() + timedelta(days=30))
    auth_service.login("user", "user123", user_agent=None, ip=None)

    # 2) Marque le token comme déjà révoqué (simulate replay)
    rt_repo.tokens[0].revoked_at = utcnow()

    with pytest.raises(AuthError):
        auth_service.refresh("rt_1", user_agent=None, ip=None)

    # strict: tout révoqué (déjà le cas ici, mais test explicite)
    assert all(t.revoked_at is not None for t in rt_repo.tokens)


@pytest.mark.unit
def test_logout_revokes_current_refresh_if_active(monkeypatch, auth_service, rt_repo):
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1"])
    _force_refresh_expires_at(monkeypatch, utcnow() + timedelta(days=30))

    auth_service.login("user", "user123", user_agent=None, ip=None)
    assert rt_repo.tokens[0].revoked_at is None

    auth_service.logout("rt_1")
    assert rt_repo.tokens[0].revoked_at is not None

    # logout idempotent
    already = rt_repo.tokens[0].revoked_at
    auth_service.logout("rt_1")
    assert rt_repo.tokens[0].revoked_at == already


@pytest.mark.unit
def test_logout_all_revokes_all_active_tokens(monkeypatch, auth_service, rt_repo):
    _set_deterministic_refresh_tokens(monkeypatch, ["rt_1", "rt_2"])
    _force_refresh_expires_at(monkeypatch, utcnow() + timedelta(days=30))

    auth_service.login("user", "user123", user_agent=None, ip=None)
    auth_service.login("user", "user123", user_agent=None, ip=None)
    assert len(rt_repo.tokens) == 2
    assert all(t.revoked_at is None for t in rt_repo.tokens)

    count = auth_service.logout_all(user_id=2)
    assert count == 2
    assert all(t.revoked_at is not None for t in rt_repo.tokens)
