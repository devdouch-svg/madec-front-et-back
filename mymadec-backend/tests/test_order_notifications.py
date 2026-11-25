"""Tests for order-related in-app notifications."""
from __future__ import annotations

from app.models.notification import Notification
from tests.conftest import auth, login, make_product, make_user
from tests.test_orders import _create_order


def _notifs_for(db, user_id: int) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.id)
        .all()
    )


class TestOrderNotifications:
    def test_new_order_notifies_admin_and_gestionnaire(
        self, client, db, acheteur, buyer_token, admin, gestionnaire, product,
    ):
        r = _create_order(client, buyer_token)
        assert r.status_code == 201

        admin_notifs = _notifs_for(db, admin.id)
        gest_notifs = _notifs_for(db, gestionnaire.id)
        assert len(admin_notifs) == 1
        assert len(gest_notifs) == 1
        assert admin_notifs[0].title == "Nouvelle commande"
        assert acheteur.full_name in admin_notifs[0].body
        assert r.json()[0]["sorder_code"] in admin_notifs[0].body

    def test_cancel_notifies_buyer(
        self, client, db, acheteur, buyer_token, product,
    ):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(buyer_token))
        assert r.status_code == 200

        notifs = _notifs_for(db, acheteur.id)
        assert len(notifs) == 1
        assert "Annulée" in notifs[0].body

    def test_status_update_notifies_buyer_with_french_label(
        self, client, db, acheteur, buyer_token, admin_token, product,
    ):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.patch(
            f"/api/v1/orders/{oid}/status",
            json={"status": "processing"},
            headers=auth(admin_token),
        )
        assert r.status_code == 200

        notifs = _notifs_for(db, acheteur.id)
        assert len(notifs) == 1
        assert "Traitement en cours" in notifs[0].body

    def test_buyer_not_notified_on_own_order_creation(
        self, client, db, acheteur, buyer_token, admin, gestionnaire, product,
    ):
        _create_order(client, buyer_token)
        assert len(_notifs_for(db, acheteur.id)) == 0
