"""Tests for authentication flows."""
from __future__ import annotations

from tests.conftest import auth, login, make_user


class TestLogin:
    def test_valid_credentials(self, client, admin):
        r = client.post("/api/v1/auth/login", json={"matricule": admin.matricule, "password": "Test1234!"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password(self, client, admin):
        r = client.post("/api/v1/auth/login", json={"matricule": admin.matricule, "password": "Wrong1234!"})
        assert r.status_code == 401

    def test_nonexistent_matricule(self, client):
        r = client.post("/api/v1/auth/login", json={"matricule": "GHOST999", "password": "Test1234!"})
        assert r.status_code == 401

    def test_inactive_account_blocked(self, client, db):
        u = make_user(db, "inactive@test.com", is_active=False)
        r = client.post("/api/v1/auth/login", json={"matricule": u.matricule, "password": "Test1234!"})
        assert r.status_code == 401
        assert "disabled" in r.json()["detail"].lower()

    def test_service_account_blocked(self, client, db):
        make_user(db, "etl@test.com", role="service")
        r = client.post("/api/v1/auth/login", json={"matricule": "etl", "password": "Test1234!"})
        assert r.status_code == 401

    def test_missing_password_field(self, client):
        r = client.post("/api/v1/auth/login", json={"matricule": "x"})
        assert r.status_code == 422


class TestRefresh:
    def test_valid_refresh_issues_new_tokens(self, client, admin):
        r1 = client.post("/api/v1/auth/login", json={"matricule": admin.matricule, "password": "Test1234!"})
        r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": r1.json()["refresh_token"]})
        assert r2.status_code == 200
        assert "access_token" in r2.json()

    def test_invalid_refresh_token(self, client):
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-token"})
        assert r.status_code == 401

    def test_access_token_rejected_as_refresh(self, client, admin):
        access = login(client, admin.matricule)
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
        assert r.status_code == 401


class TestProtectedRoutes:
    def test_no_token_returns_401(self, client):
        assert client.get("/api/v1/users/me").status_code == 401

    def test_valid_token_returns_user(self, client, admin, admin_token):
        r = client.get("/api/v1/users/me", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["email"] == admin.email

    def test_garbage_token_returns_401(self, client):
        r = client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401


class TestPasswordReset:
    def test_request_always_200_anti_enumeration(self, client):
        r = client.post("/api/v1/auth/reset-password/request", json={"email": "nobody@nowhere.com"})
        assert r.status_code == 200

    def test_request_real_email_also_200(self, client, admin):
        r = client.post("/api/v1/auth/reset-password/request", json={"email": admin.email})
        assert r.status_code == 200

    def test_confirm_invalid_token_400(self, client):
        r = client.post("/api/v1/auth/reset-password/confirm",
                        json={"token": "bad-token", "new_password": "NewPass123!"})
        assert r.status_code == 400

    def test_confirm_weak_password_422(self, client):
        r = client.post("/api/v1/auth/reset-password/confirm",
                        json={"token": "any", "new_password": "weak"})
        assert r.status_code == 422

    def test_full_reset_flow(self, client, db, admin):
        from app.services.auth import create_reset_token
        _, plain = create_reset_token(db, admin.email)
        r = client.post("/api/v1/auth/reset-password/confirm",
                        json={"token": plain, "new_password": "NewPass999!"})
        assert r.status_code == 200
        # New password works
        assert client.post("/api/v1/auth/login",
                           json={"matricule": admin.matricule, "password": "NewPass999!"}).status_code == 200

    def test_token_cannot_be_reused(self, client, db, admin):
        from app.services.auth import create_reset_token
        _, plain = create_reset_token(db, admin.email)
        client.post("/api/v1/auth/reset-password/confirm",
                    json={"token": plain, "new_password": "NewPass999!"})
        r2 = client.post("/api/v1/auth/reset-password/confirm",
                         json={"token": plain, "new_password": "AnotherPass1!"})
        assert r2.status_code == 400


class TestChangePassword:
    def test_correct_current_password(self, client, admin, admin_token):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "Test1234!", "new_password": "NewPass999!"},
                        headers=auth(admin_token))
        assert r.status_code == 200

    def test_wrong_current_password_401(self, client, admin_token):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "WrongPass1!", "new_password": "NewPass999!"},
                        headers=auth(admin_token))
        assert r.status_code == 401

    def test_no_uppercase_422(self, client, admin_token):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "Test1234!", "new_password": "nouppercase1"},
                        headers=auth(admin_token))
        assert r.status_code == 422

    def test_no_digit_422(self, client, admin_token):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "Test1234!", "new_password": "NoDigitsHere!"},
                        headers=auth(admin_token))
        assert r.status_code == 422

    def test_too_short_422(self, client, admin_token):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "Test1234!", "new_password": "Ab1!"},
                        headers=auth(admin_token))
        assert r.status_code == 422

    def test_unauthenticated_401(self, client):
        r = client.post("/api/v1/auth/change-password",
                        json={"current_password": "Test1234!", "new_password": "NewPass999!"})
        assert r.status_code == 401
