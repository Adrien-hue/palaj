from __future__ import annotations

import os
import tempfile
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.app.main import create_app
from backend.app.api.deps import get_db
from db.base import Base

from backend.app.settings import settings
from backend.app.security.password import hash_password

from db.models import User
from db.models.refresh_token import RefreshToken


@pytest.fixture(scope="session")
def db_url() -> str:
    # SQLite fichier temporaire (plus fiable que :memory: avec plusieurs connexions)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return f"sqlite:///{path}"


@pytest.fixture(scope="session")
def engine(db_url: str):
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(engine) -> Generator[Session, None, None]:
    """
    Session utilitaire pour les asserts DB côté tests.
    (Les requêtes API utiliseront une session par requête via override get_db)
    """
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def app(engine):
    app = create_app()

    # DB dependency override: 1 session par requête (beaucoup plus stable)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def _override_get_db():
        s = TestingSessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override_get_db

    # Settings adaptés aux tests
    settings.cookie_secure = False
    settings.cookie_samesite = "lax"
    settings.cookie_domain = None

    settings.access_token_minutes = 15  # on évite les tests flaky d'expiration
    settings.refresh_token_days = 1

    # cookies names (doivent exister dans ton Settings)
    settings.access_cookie_name = getattr(settings, "access_cookie_name", "palaj_at")
    settings.refresh_cookie_name = getattr(settings, "refresh_cookie_name", "palaj_rt")

    # jwt config
    settings.jwt_secret = "TEST_SECRET_CHANGE_ME"
    settings.jwt_algorithm = "HS256"
    settings.jwt_issuer = "palaj-api"
    settings.jwt_audience = "palaj-web"

    return app


@pytest.fixture()
def client(app):
    pytest.importorskip("httpx", reason="httpx required for TestClient")
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def seed_users(db_session: Session):
    """
    Seed idempotent: admin + user + inactive.
    Nettoie refresh_tokens entre tests pour éviter les interférences.
    """
    db_session.query(RefreshToken).delete()
    db_session.commit()

    def ensure_user(username: str, password: str, role: str, is_active: bool = True):
        u = db_session.query(User).filter(User.username == username).first()
        if u:
            u.role = role
            u.is_active = is_active
            u.password_hash = hash_password(password)
            return u
        u = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(u)
        return u

    ensure_user("admin", "admin123", "admin", True)
    ensure_user("user", "user123", "user", True)
    ensure_user("inactive", "inactive123", "user", False)

    db_session.commit()
    yield
