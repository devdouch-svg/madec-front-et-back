"""Tests for /dashboard aggregation endpoint."""
from __future__ import annotations

from app.models.order import Order, OrderLine
from tests.conftest import auth, make_product


class TestDashboard:
    def test_includes_mobile_catalog_for_acheteur(self, client, buyer_token):
        r = client.get("/api/v1/dashboard", headers=auth(buyer_token))
        assert r.status_code == 200
        body = r.json()
        assert "mobile_catalog" in body
        assert isinstance(body["mobile_catalog"], list)

    def test_admin_stats_include_uncategorized_count(self, client, db, admin_token):
        p = make_product(db, "DASH001")
        p.categorie = None
        db.commit()
        r = client.get("/api/v1/dashboard", headers=auth(admin_token))
        assert r.status_code == 200
        stats = r.json()["admin_stats"]
        assert stats["uncategorized_mobile_products"] >= 1

    def test_admin_recent_orders_include_all_buyers(self, client, db, admin_token, acheteur):
        db.add(
            Order(
                sorder_code="SMD_DASH001",
                user_id=acheteur.id,
                sorder_status="pending",
                payment_mode="especes",
                amount=100,
                dueamount=110,
            )
        )
        db.commit()
        r = client.get("/api/v1/dashboard", headers=auth(admin_token))
        assert r.status_code == 200
        recent = r.json()["recent_orders"]
        assert len(recent) == 1
        assert recent[0]["sorder_code"] == "SMD_DASH001"
        assert recent[0]["buyer_name"]

    def test_acheteur_recent_orders_are_own_only(self, client, db, buyer_token, acheteur, acheteur2):
        db.add(
            Order(
                sorder_code="SMD_MINE",
                user_id=acheteur.id,
                sorder_status="pending",
                payment_mode="especes",
                amount=50,
                dueamount=55,
            )
        )
        db.add(
            Order(
                sorder_code="SMD_OTHER",
                user_id=acheteur2.id,
                sorder_status="pending",
                payment_mode="especes",
                amount=80,
                dueamount=88,
            )
        )
        db.commit()
        r = client.get("/api/v1/dashboard", headers=auth(buyer_token))
        assert r.status_code == 200
        codes = [o["sorder_code"] for o in r.json()["recent_orders"]]
        assert codes == ["SMD_MINE"]

    def test_acheteur_recent_orders_include_line_previews(self, client, db, buyer_token, acheteur):
        product = make_product(db, "DASH-IMG")
        product.image_path = "/uploads/products/dash-img.png"
        db.commit()
        db.refresh(product)
        order = Order(
            sorder_code="SMD_LINES",
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

        r = client.get("/api/v1/dashboard", headers=auth(buyer_token))
        assert r.status_code == 200
        recent = r.json()["recent_orders"]
        assert len(recent) == 1
        row = recent[0]
        assert row["line_count"] == 1
        assert row["lines"] == [
            {
                "product_code": product.product_code,
                "product_name": product.name,
                "image_path": product.image_path,
            }
        ]
