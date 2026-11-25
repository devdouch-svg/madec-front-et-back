"""Tests for order creation, RBAC, status machine, and plafond enforcement."""
from __future__ import annotations

import pytest

from tests.conftest import auth, login, make_product, make_user


def _create_order(client, token, product_code="PROD001", qty=1.0, payment_mode=None):
    payload = {"lines": [{"product_code": product_code, "quantity": qty}]}
    if payment_mode:
        payload["payment_mode"] = payment_mode
    return client.post("/api/v1/orders", json=payload, headers=auth(token))


class TestOrderCreation:
    def test_acheteur_can_create(self, client, acheteur, buyer_token, product):
        r = _create_order(client, buyer_token)
        assert r.status_code == 201
        orders = r.json()
        assert len(orders) >= 1
        assert orders[0]["user_id"] == acheteur.id
        assert orders[0]["user_email"] == acheteur.email
        assert orders[0]["user_name"]
        # Waiting for ETL pull (pending → GET /sync/orders/pending)
        assert orders[0]["sorder_status"] == "pending"

    def test_create_order_succeeds_when_staff_notify_raises(self, client, buyer_token, product, monkeypatch):
        def _boom(*_args, **_kwargs):
            raise RuntimeError("notification service down")

        monkeypatch.setattr("app.services.notification.notify_role_users", _boom)
        r = _create_order(client, buyer_token)
        assert r.status_code == 201
        assert r.json()[0]["sorder_code"]

    def test_admin_cannot_create_order(self, client, admin_token, product):
        r = _create_order(client, admin_token)
        assert r.status_code == 403

    def test_gestionnaire_cannot_create_order(self, client, gest_token, product):
        r = _create_order(client, gest_token)
        assert r.status_code == 403

    def test_inactive_product_rejected(self, client, db, buyer_token):
        make_product(db, "INACTIVE", is_active=False)
        r = _create_order(client, buyer_token, "INACTIVE")
        assert r.status_code == 400

    def test_nonexistent_product_rejected(self, client, buyer_token):
        r = _create_order(client, buyer_token, "DOESNOTEXIST")
        assert r.status_code == 400

    def test_fixedtax_not_applied_for_especes(self, client, db, buyer_token):
        """Sabile prices only — no cash fee / fixedtax surcharge on espèces."""
        make_product(db, "TAX001", base_price=100.0)
        r = _create_order(client, buyer_token, "TAX001", qty=1.0)
        assert r.status_code == 201
        order = r.json()[0]
        assert float(order["amount"]) == pytest.approx(100.0, abs=0.01)
        assert float(order["fixedtax"]) == pytest.approx(0.0, abs=0.01)
        assert float(order["dueamount"]) == pytest.approx(100.0, abs=0.01)

    def test_no_fixedtax_for_carte(self, client, db):
        user = make_user(db, "carte@test.com", payment_mode="carte")
        token = login(client, user.matricule)
        make_product(db, "CARTE001", base_price=100.0)
        r = _create_order(client, token, "CARTE001")
        assert r.status_code == 201
        order = r.json()[0]
        assert float(order["fixedtax"]) == 0.0
        assert float(order["dueamount"]) == pytest.approx(100.0, abs=0.01)


class TestLesDeux:
    def test_les_deux_without_payment_mode_fails(self, client, db, product):
        user = make_user(db, "both@test.com", payment_mode="les_deux")
        token = login(client, user.matricule)
        r = _create_order(client, token)   # no payment_mode in payload
        assert r.status_code == 400
        assert "especes" in r.json()["detail"].lower() or "carte" in r.json()["detail"].lower()

    def test_les_deux_with_especes_no_tax(self, client, db, product):
        user = make_user(db, "both@test.com", payment_mode="les_deux")
        token = login(client, user.matricule)
        r = _create_order(client, token, payment_mode="especes")
        assert r.status_code == 201
        assert float(r.json()[0]["fixedtax"]) == 0.0

    def test_les_deux_with_carte_no_tax(self, client, db, product):
        user = make_user(db, "both@test.com", payment_mode="les_deux")
        token = login(client, user.matricule)
        r = _create_order(client, token, payment_mode="carte")
        assert r.status_code == 201
        assert float(r.json()[0]["fixedtax"]) == 0.0


class TestPlafond:
    def test_order_within_plafond_succeeds(self, client, acheteur, buyer_token, product):
        """Acheteur has plafond=500, product costs 100 → OK."""
        r = _create_order(client, buyer_token)
        assert r.status_code == 201

    def test_order_exceeds_plafond_blocked(self, client, db, product):
        user = make_user(db, "tight@test.com", plafond_mensuel=50.0)
        token = login(client, user.matricule)
        r = _create_order(client, token, qty=1.0)  # product costs 100 > 50 plafond
        assert r.status_code == 402
        detail = r.json()["detail"]
        assert detail["code"] == "PLAFOND_EXCEEDED"
        assert "available" in detail
        assert "requested" in detail

    def test_no_plafond_always_succeeds(self, client, db):
        user = make_user(db, "unlimited@test.com", plafond_mensuel=None)
        token = login(client, user.matricule)
        make_product(db, "BIG001", base_price=999999.0)
        r = _create_order(client, token, "BIG001")
        assert r.status_code == 201


class TestCancelOrder:
    def _place_order(self, client, token, product_code="PROD001"):
        r = _create_order(client, token, product_code)
        assert r.status_code == 201
        return r.json()[0]["id"]

    def test_acheteur_can_cancel_own_before_etl_push(self, client, acheteur, buyer_token, product):
        oid = self._place_order(client, buyer_token)
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["sorder_status"] == "cancelled"

    def test_admin_can_cancel_any(self, client, db, acheteur, buyer_token, admin_token, product):
        oid = self._place_order(client, buyer_token)
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(admin_token))
        assert r.status_code == 200

    def test_gestionnaire_cannot_cancel(self, client, acheteur, buyer_token, gest_token, product):
        oid = self._place_order(client, buyer_token)
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(gest_token))
        assert r.status_code == 403

    def test_cancel_blocked_after_etl_push(self, client, db, acheteur, buyer_token, admin_token, product):
        """Once pushed to ERP, /cancel is blocked — use status endpoint / ETL."""
        from datetime import datetime, timezone
        from app.models.order import Order

        oid = self._place_order(client, buyer_token)
        order = db.get(Order, oid)
        order.sorder_status = "processing"
        order.pushed_at = datetime.now(timezone.utc)
        db.commit()
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(admin_token))
        assert r.status_code == 400

    def test_admin_can_cancel_via_status_endpoint(self, client, acheteur, buyer_token, admin_token, product):
        oid = self._place_order(client, buyer_token)
        r = client.patch(f"/api/v1/orders/{oid}/status",
                         json={"status": "cancelled"},
                         headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["sorder_status"] == "cancelled"

    def test_acheteur_cannot_cancel_others_order(self, client, db, product):
        u1 = make_user(db, "u1@test.com")
        u2 = make_user(db, "u2@test.com")
        t1 = login(client, u1.matricule)
        t2 = login(client, u2.matricule)
        oid = _create_order(client, t1).json()[0]["id"]
        r = client.patch(f"/api/v1/orders/{oid}/cancel", headers=auth(t2))
        assert r.status_code in (403, 404)


class TestStatusMachine:
    def test_create_pending_awaits_etl(self, client, acheteur, buyer_token, admin_token, product):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.get(f"/api/v1/orders/{oid}", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["sorder_status"] == "pending"

    def test_invalid_transition_rejected(self, client, acheteur, buyer_token, admin_token, product):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.patch(f"/api/v1/orders/{oid}/status",
                         json={"status": "delivered"},   # can't jump from pending to delivered
                         headers=auth(admin_token))
        assert r.status_code == 400

    def test_acheteur_cannot_update_status(self, client, acheteur, buyer_token, admin_token, product):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.patch(f"/api/v1/orders/{oid}/status",
                         json={"status": "cancelled"},
                         headers=auth(buyer_token))
        assert r.status_code == 403

    def test_pending_can_move_to_processing(self, client, acheteur, buyer_token, admin_token, product):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.patch(
            f"/api/v1/orders/{oid}/status",
            json={"status": "processing"},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["sorder_status"] == "processing"


class TestOrderVisibility:
    def test_acheteur_sees_only_own_orders(self, client, db, product):
        u1 = make_user(db, "u1@test.com")
        u2 = make_user(db, "u2@test.com")
        t1 = login(client, u1.matricule)
        t2 = login(client, u2.matricule)
        _create_order(client, t1)
        _create_order(client, t2)
        r = client.get("/api/v1/orders", headers=auth(t1))
        assert r.status_code == 200
        assert all(o["user_id"] == u1.id for o in r.json()["items"])

    def test_admin_sees_all_orders(self, client, db, admin_token, product):
        u1 = make_user(db, "u1@test.com")
        u2 = make_user(db, "u2@test.com")
        _create_order(client, login(client, u1.matricule))
        _create_order(client, login(client, u2.matricule))
        r = client.get("/api/v1/orders", headers=auth(admin_token))
        assert r.json()["total"] >= 2

    def test_order_response_includes_user_name(self, client, acheteur, buyer_token, product):
        oid = _create_order(client, buyer_token).json()[0]["id"]
        r = client.get(f"/api/v1/orders/{oid}", headers=auth(buyer_token))
        d = r.json()
        assert "user_email" in d
        assert "user_name" in d
        assert d["user_email"] == acheteur.email


class TestOrderLineImages:
    def test_my_orders_include_line_previews_with_images(self, client, db, acheteur, buyer_token):
        from app.models.order import Order, OrderLine

        product = make_product(db, "ORD-IMG")
        product.image_path = "/uploads/products/ord-img.png"
        db.commit()
        db.refresh(product)

        order = Order(
            sorder_code="SMD_IMG01",
            user_id=acheteur.id,
            sorder_status="pending",
            payment_mode="especes",
            amount=50,
            dueamount=55,
        )
        db.add(order)
        db.flush()
        db.add(
            OrderLine(
                order_id=order.id,
                sorder_line_code=10,
                product_id=product.id,
                product_code=product.product_code,
                product_name=product.name,
                unit_price=25,
                quantity=2,
                line_amount=50,
            )
        )
        db.commit()

        r = client.get("/api/v1/orders/me", headers=auth(buyer_token))
        assert r.status_code == 200
        row = next(o for o in r.json()["items"] if o["sorder_code"] == "SMD_IMG01")
        assert row["line_count"] == 1
        assert row["lines"] == [
            {
                "product_code": product.product_code,
                "product_name": product.name,
                "image_path": product.image_path,
            }
        ]

    def test_order_lines_endpoint_includes_image_path(self, client, db, acheteur, buyer_token):
        product = make_product(db, "LINE-IMG")
        product.image_path = "/uploads/products/line-img.png"
        db.commit()
        db.refresh(product)

        oid = _create_order(client, buyer_token, "LINE-IMG").json()[0]["id"]
        r = client.get(f"/api/v1/orders/{oid}/lines", headers=auth(buyer_token))
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["image_path"] == product.image_path
