"""Tests for notifications endpoint: pagination, ownership, RBAC."""
from __future__ import annotations

from tests.conftest import auth, login, make_user
from app.models.notification import Notification
from app.db.session import SessionLocal


def _create_notification(user_id: int, title: str = "Test") -> None:
    db = SessionLocal()
    try:
        db.add(Notification(user_id=user_id, title=title, body="body", type="general"))
        db.commit()
    finally:
        db.close()


class TestNotificationsList:
    def test_returns_paginated_response(self, client, acheteur, buyer_token):
        _create_notification(acheteur.id, "Notif 1")
        _create_notification(acheteur.id, "Notif 2")
        r = client.get("/api/v1/notifications", headers=auth(buyer_token))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_user_sees_only_own_notifications(self, client, db, acheteur, buyer_token):
        other = make_user(db, "other@test.com")
        _create_notification(acheteur.id, "Mine")
        _create_notification(other.id, "Not mine")
        r = client.get("/api/v1/notifications", headers=auth(buyer_token))
        assert all(n["user_id"] == acheteur.id for n in r.json()["items"])

    def test_pagination_works(self, client, acheteur, buyer_token):
        for i in range(5):
            _create_notification(acheteur.id, f"Notif {i}")
        r = client.get("/api/v1/notifications?page=1&page_size=3", headers=auth(buyer_token))
        assert r.status_code == 200
        assert len(r.json()["items"]) <= 3


class TestMarkRead:
    def test_mark_notification_read(self, client, acheteur, buyer_token):
        _create_notification(acheteur.id)
        notif_id = client.get("/api/v1/notifications",
                              headers=auth(buyer_token)).json()["items"][0]["id"]
        r = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    def test_cannot_mark_others_notification(self, client, db, acheteur, buyer_token):
        other = make_user(db, "other@test.com")
        _create_notification(other.id)
        db2 = SessionLocal()
        try:
            notif = db2.query(Notification).filter(Notification.user_id == other.id).first()
            notif_id = notif.id
        finally:
            db2.close()
        r = client.patch(f"/api/v1/notifications/{notif_id}/read", headers=auth(buyer_token))
        assert r.status_code == 404

    def test_mark_all_read(self, client, acheteur, buyer_token):
        _create_notification(acheteur.id)
        _create_notification(acheteur.id)
        r = client.patch("/api/v1/notifications/read-all", headers=auth(buyer_token))
        assert r.status_code == 200
        # All should be read
        items = client.get("/api/v1/notifications",
                           headers=auth(buyer_token)).json()["items"]
        assert all(n["is_read"] for n in items)


class TestDeleteNotification:
    def test_delete_own_notification(self, client, acheteur, buyer_token):
        _create_notification(acheteur.id)
        notif_id = client.get("/api/v1/notifications",
                              headers=auth(buyer_token)).json()["items"][0]["id"]
        r = client.delete(f"/api/v1/notifications/{notif_id}", headers=auth(buyer_token))
        assert r.status_code == 200

    def test_cannot_delete_others_notification(self, client, db, acheteur, buyer_token):
        other = make_user(db, "other@test.com")
        _create_notification(other.id)
        db2 = SessionLocal()
        try:
            notif = db2.query(Notification).filter(Notification.user_id == other.id).first()
            notif_id = notif.id
        finally:
            db2.close()
        r = client.delete(f"/api/v1/notifications/{notif_id}", headers=auth(buyer_token))
        assert r.status_code == 404


class TestSendNotification:
    def test_admin_can_send(self, client, acheteur, admin_token):
        r = client.post("/api/v1/notifications/send",
                        json={"user_id": acheteur.id, "title": "Hello",
                              "body": "Test push", "type": "general"},
                        headers=auth(admin_token))
        assert r.status_code == 201

    def test_non_admin_cannot_send(self, client, acheteur, buyer_token):
        r = client.post("/api/v1/notifications/send",
                        json={"user_id": acheteur.id, "title": "Hello",
                              "body": "Test", "type": "general"},
                        headers=auth(buyer_token))
        assert r.status_code == 403

    def test_send_unknown_user_404(self, client, admin_token):
        r = client.post("/api/v1/notifications/send",
                        json={"user_id": 999999, "title": "Hello",
                              "body": "Test", "type": "general"},
                        headers=auth(admin_token))
        assert r.status_code == 404


class TestUnreadCount:
    def test_unread_count(self, client, acheteur, buyer_token):
        _create_notification(acheteur.id, "Unread 1")
        _create_notification(acheteur.id, "Unread 2")
        r = client.get("/api/v1/notifications/unread-count", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["unread_count"] >= 2
