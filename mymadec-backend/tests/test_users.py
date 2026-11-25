"""Tests for user management endpoints and RBAC."""
from __future__ import annotations

from tests.conftest import auth, make_user


class TestGetMe:
    def test_returns_own_profile(self, client, acheteur, buyer_token):
        r = client.get("/api/v1/users/me", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["email"] == acheteur.email

    def test_response_includes_new_fields(self, client, admin_token):
        r = client.get("/api/v1/users/me", headers=auth(admin_token))
        d = r.json()
        assert "matricule" in d
        assert "langue" in d
        assert "synced_from_intermediate" in d


class TestListUsers:
    def test_admin_can_list(self, client, acheteur, admin_token):
        r = client.get("/api/v1/users", headers=auth(admin_token))
        assert r.status_code == 200
        assert "items" in r.json()

    def test_gestionnaire_can_list(self, client, acheteur, gest_token):
        assert client.get("/api/v1/users", headers=auth(gest_token)).status_code == 200

    def test_acheteur_cannot_list(self, client, buyer_token):
        assert client.get("/api/v1/users", headers=auth(buyer_token)).status_code == 403

    def test_search_filter_works(self, client, db, admin_token):
        make_user(db, "alice@test.com")
        make_user(db, "bob@test.com")
        r = client.get("/api/v1/users?search=alice", headers=auth(admin_token))
        items = r.json()["items"]
        assert len(items) >= 1
        assert all("alice" in u["email"] for u in items)


class TestCreateUser:
    def test_admin_creates_user(self, client, admin_token):
        r = client.post("/api/v1/users",
                        json={"email": "new@test.com", "first_name": "New",
                              "role": "acheteur", "payment_mode": "especes"},
                        headers=auth(admin_token))
        assert r.status_code == 201
        assert r.json()["email"] == "new@test.com"

    def test_gestionnaire_cannot_create(self, client, gest_token):
        r = client.post("/api/v1/users",
                        json={"email": "new@test.com", "first_name": "New",
                              "role": "acheteur", "payment_mode": "especes"},
                        headers=auth(gest_token))
        assert r.status_code == 403

    def test_create_with_matricule(self, client, admin_token):
        r = client.post("/api/v1/users",
                        json={"email": "mat@test.com", "first_name": "Mat",
                              "role": "acheteur", "payment_mode": "especes",
                              "matricule": "MAT001"},
                        headers=auth(admin_token))
        assert r.status_code == 201
        assert r.json()["matricule"] == "MAT001"

    def test_create_with_les_deux_payment(self, client, admin_token):
        r = client.post("/api/v1/users",
                        json={"email": "both@test.com", "first_name": "Both",
                              "role": "acheteur", "payment_mode": "les_deux"},
                        headers=auth(admin_token))
        assert r.status_code == 201
        assert r.json()["payment_mode"] == "les_deux"


class TestUpdateUser:
    def test_admin_can_update(self, client, acheteur, admin_token):
        r = client.put(f"/api/v1/users/{acheteur.id}",
                       json={"first_name": "Updated"},
                       headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["first_name"] == "Updated"

    def test_gestionnaire_cannot_update(self, client, acheteur, gest_token):
        assert client.put(f"/api/v1/users/{acheteur.id}",
                          json={"first_name": "X"},
                          headers=auth(gest_token)).status_code == 403

    def test_gestionnaire_can_view_detail(self, client, acheteur, gest_token):
        assert client.get(f"/api/v1/users/{acheteur.id}",
                          headers=auth(gest_token)).status_code == 200


class TestToggleUser:
    def test_admin_can_toggle(self, client, acheteur, admin_token):
        r = client.patch(f"/api/v1/users/{acheteur.id}/toggle", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_gestionnaire_cannot_toggle(self, client, acheteur, gest_token):
        assert client.patch(f"/api/v1/users/{acheteur.id}/toggle",
                            headers=auth(gest_token)).status_code == 403


class TestPlafondStatus:
    def test_admin_sees_any_user(self, client, acheteur, admin_token):
        assert client.get(f"/api/v1/users/{acheteur.id}/plafond/status",
                          headers=auth(admin_token)).status_code == 200

    def test_gestionnaire_sees_any_user(self, client, acheteur, gest_token):
        assert client.get(f"/api/v1/users/{acheteur.id}/plafond/status",
                          headers=auth(gest_token)).status_code == 200

    def test_acheteur_sees_own(self, client, acheteur, buyer_token):
        assert client.get(f"/api/v1/users/{acheteur.id}/plafond/status",
                          headers=auth(buyer_token)).status_code == 200

    def test_acheteur_cannot_see_others(self, client, db, acheteur, buyer_token):
        other = make_user(db, "other@test.com", role="acheteur")
        assert client.get(f"/api/v1/users/{other.id}/plafond/status",
                          headers=auth(buyer_token)).status_code == 403


class TestFCMToken:
    def test_set_fcm_token(self, client, buyer_token):
        r = client.patch("/api/v1/users/me/fcm-token",
                         json={"fcm_token": "device-token-abc"},
                         headers=auth(buyer_token))
        assert r.status_code == 200

    def test_clear_fcm_token(self, client, buyer_token):
        r = client.patch("/api/v1/users/me/fcm-token",
                         json={"fcm_token": None},
                         headers=auth(buyer_token))
        assert r.status_code == 200

    def test_fcm_token_not_in_profile_update(self, client, buyer_token):
        """fcm_token removed from UserMeUpdate — should be ignored or 422."""
        r = client.put("/api/v1/users/me",
                       json={"first_name": "Test", "fcm_token": "should-be-ignored"},
                       headers=auth(buyer_token))
        # 200 because Pydantic ignores unknown fields by default (extra="ignore")
        assert r.status_code == 200
