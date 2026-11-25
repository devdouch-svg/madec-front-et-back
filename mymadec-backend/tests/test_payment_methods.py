"""Payment methods RBAC and behaviour."""
from __future__ import annotations

from tests.conftest import auth, login, make_user


class TestPaymentMethodsMe:
    def test_acheteur_gets_own_mode(self, client, acheteur, buyer_token):
        r = client.get("/api/v1/payment-methods", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json() == ["especes"]

    def test_les_deux_expands_to_both(self, client, db, acheteur, buyer_token):
        user = acheteur
        user.payment_mode = "les_deux"
        db.commit()
        r = client.get("/api/v1/payment-methods", headers=auth(buyer_token))
        assert set(r.json()) == {"especes", "carte"}


class TestPaymentMethodsAdmin:
    def test_all_modes_requires_admin(self, client, buyer_token, admin_token):
        assert client.get("/api/v1/payment-methods/all", headers=auth(buyer_token)).status_code == 403
        r = client.get("/api/v1/payment-methods/all", headers=auth(admin_token))
        assert r.status_code == 200
        assert set(r.json()) == {"especes", "carte", "deduction_salaire"}

    def test_deduction_salaire_mode_on_me(self, client, db, acheteur, buyer_token):
        acheteur.payment_mode = "deduction_salaire"
        db.commit()
        r = client.get("/api/v1/payment-methods", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json() == ["deduction_salaire"]

    def test_admin_can_set_multi_modes(self, client, acheteur, admin_token, buyer_token):
        r = client.put(
            f"/api/v1/payment-methods/{acheteur.id}/modes",
            json={"modes": ["especes", "deduction_salaire"]},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        me = client.get("/api/v1/payment-methods", headers=auth(buyer_token))
        assert set(me.json()) == {"especes", "deduction_salaire"}

    def test_admin_can_set_user_mode(self, client, acheteur, admin_token):
        r = client.patch(
            f"/api/v1/payment-methods/{acheteur.id}/carte/toggle",
            headers=auth(admin_token),
        )
        assert r.status_code == 200

    def test_gest_cannot_toggle(self, client, db, acheteur):
        gest = make_user(db, "gest@test.com", role="gestionnaire")
        token = login(client, gest.matricule, "Test1234!")
        r = client.patch(
            f"/api/v1/payment-methods/{acheteur.id}/carte/toggle",
            headers=auth(token),
        )
        assert r.status_code == 403
