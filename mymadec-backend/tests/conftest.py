"""
Test configuration and shared fixtures.

Sets DATABASE_URL to SQLite BEFORE any app modules are imported so that
app/db/session.py picks up the correct engine on first import.
Tables are wiped before every test for full isolation.
"""
from __future__ import annotations

import os

# ── Must be set before any app imports ──────────────────────────────────────
os.environ.setdefault("APP_ENV",                      "test")   # skips the prod SECRET_KEY guard
os.environ.setdefault("SKIP_MIGRATIONS",              "1")      # SQLite tests use create_all, not Alembic
os.environ.setdefault("SKIP_DB_WAIT",                 "1")
os.environ.setdefault("DATABASE_URL",                 "sqlite:///./test_mymadec.db")
os.environ.setdefault("SECRET_KEY",                   "test-secret-not-for-production")
os.environ.setdefault("DEBUG",                        "true")
os.environ.setdefault("DISABLE_EMAIL",                "true")
os.environ.setdefault("SEED_DEMO",                    "false")
os.environ.setdefault("FIXEDTAX_RATE",                "0.10")   # 10% — easy to test
os.environ.setdefault("RATE_LIMIT_LOGIN",             "1000/minute")
os.environ.setdefault("RATE_LIMIT_RESET_PASSWORD",    "1000/minute")
os.environ.setdefault("RATE_LIMIT_CHANGE_PASSWORD",   "1000/minute")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import app.models.catalog  # noqa: F401 — register reference tables (before app.main import)
from app.main import app
from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.user import User, ServiceToken
from app.models.product import Product


# ── Table lifecycle ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    """Wipe all rows before every test (SQLite-compatible)."""
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f"DELETE FROM {table.name}"))
        db.commit()
    finally:
        db.close()


# ── Core fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    # Override rate-limit dependencies so tests don't throttle each other
    from app.core.rate_limits import (
        login_rate_limit, reset_password_rate_limit, change_password_rate_limit,
        sync_rate_limit,
    )
    app.dependency_overrides[login_rate_limit] = lambda: None
    app.dependency_overrides[reset_password_rate_limit] = lambda: None
    app.dependency_overrides[change_password_rate_limit] = lambda: None
    app.dependency_overrides[sync_rate_limit] = lambda: None
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Factories ────────────────────────────────────────────────────────────────

def make_user(db, email: str, password: str = "Test1234!", role: str = "acheteur",
              is_active: bool = True, **kwargs) -> User:
    # Login is by matricule now — derive a unique one from the email local-part.
    matricule = kwargs.pop("matricule", None) or email.split("@")[0].replace(".", "")
    user = User(
        email=email,
        matricule=matricule,
        hashed_password=hash_password(password),
        first_name="Test",
        last_name=role.capitalize(),
        role=role,
        is_active=is_active,
        payment_mode=kwargs.pop("payment_mode", "especes"),
        agence="001",
        **kwargs,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_product(db, code: str = "PROD001", base_price: float = 100.0,
                 discount_rate: float = 0.0, is_active: bool = True,
                 psg_code: str = "GRP01") -> Product:
    p = Product(
        product_code=code,
        name=f"Product {code}",
        base_price=base_price,
        discount_rate=discount_rate,
        is_active=is_active,
        productsalesgroup_code=psg_code,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def login(client, matricule: str, password: str = "Test1234!") -> str:
    r = client.post("/api/v1/auth/login", json={"matricule": matricule, "password": password})
    assert r.status_code == 200, f"Login failed ({r.status_code}): {r.json()}"
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Role fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def admin(db):
    return make_user(db, "admin@test.com", role="admin")


@pytest.fixture
def gestionnaire(db):
    return make_user(db, "gest@test.com", role="gestionnaire")


@pytest.fixture
def acheteur(db):
    return make_user(db, "buyer@test.com", role="acheteur", plafond_mensuel=500.0)


@pytest.fixture
def acheteur2(db):
    return make_user(db, "buyer2@test.com", role="acheteur")


@pytest.fixture
def admin_token(client, admin):
    return login(client, admin.matricule)


@pytest.fixture
def gest_token(client, gestionnaire):
    return login(client, gestionnaire.matricule)


@pytest.fixture
def buyer_token(client, acheteur):
    return login(client, acheteur.matricule)


@pytest.fixture
def product(db):
    return make_product(db)


@pytest.fixture
def etl_token(db):
    from app.core.security import generate_service_token, hash_service_token
    plain = generate_service_token()
    svc = ServiceToken(name="ETL Test", token_hash=hash_service_token(plain))
    db.add(svc)
    db.commit()
    return plain
