"""Tests for product endpoints and ETL sync rules."""
from __future__ import annotations

from tests.conftest import auth, make_product


class TestProductAccess:
    def test_acheteur_can_list_active_products(self, client, db, buyer_token):
        make_product(db, "ACT001", is_active=True)
        make_product(db, "INA001", is_active=False)
        r = client.get("/api/v1/products", headers=auth(buyer_token))
        assert r.status_code == 200
        codes = [p["product_code"] for p in r.json()["items"]]
        assert "ACT001" in codes
        assert "INA001" not in codes  # inactive hidden from acheteur

    def test_admin_sees_inactive_products(self, client, db, admin_token):
        make_product(db, "INA001", is_active=False)
        r = client.get("/api/v1/products?is_active=false", headers=auth(admin_token))
        assert r.status_code == 200
        assert any(p["product_code"] == "INA001" for p in r.json()["items"])

    def test_search_works(self, client, db, buyer_token):
        make_product(db, "SEARCH001", base_price=50.0)
        r = client.get("/api/v1/products/search?q=SEARCH", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1


class TestProductMutations:
    def test_admin_can_create(self, client, admin_token):
        r = client.post("/api/v1/products",
                        json={"product_code": "NEW001", "name": "New Product",
                              "base_price": 50.0, "discount_rate": 0},
                        headers=auth(admin_token))
        assert r.status_code == 201

    def test_gestionnaire_can_create(self, client, gest_token):
        r = client.post("/api/v1/products",
                        json={"product_code": "NEW002", "name": "Gest Product",
                              "base_price": 50.0, "discount_rate": 0},
                        headers=auth(gest_token))
        assert r.status_code == 201

    def test_acheteur_cannot_create(self, client, buyer_token):
        r = client.post("/api/v1/products",
                        json={"product_code": "NEW003", "name": "Buyer Product",
                              "base_price": 50.0, "discount_rate": 0},
                        headers=auth(buyer_token))
        assert r.status_code == 403

    def test_admin_can_toggle(self, client, db, admin_token):
        p = make_product(db, "TOG001")
        r = client.patch(f"/api/v1/products/{p.id}/toggle", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_staff_can_reactivate_inactive_product(self, client, db, gest_token):
        p = make_product(db, "TOG002", is_active=False)
        r = client.patch(f"/api/v1/products/{p.id}/toggle", headers=auth(gest_token))
        assert r.status_code == 200
        assert r.json()["is_active"] is True

    def test_create_with_blank_optional_fields(self, client, admin_token):
        r = client.post(
            "/api/v1/products",
            json={
                "product_code": "NEW004",
                "name": "Blank optional",
                "description": "",
                "gamme": "  ",
                "base_price": None,
                "discount_rate": 0,
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 201
        assert r.json()["description"] is None
        assert r.json()["gamme"] is None

    def test_product_response_has_synced_flag(self, client, db, admin_token):
        p = make_product(db, "SYNC001")
        r = client.get(f"/api/v1/products/{p.id}", headers=auth(admin_token))
        assert "synced_from_intermediate" in r.json()

    def test_filter_by_mobile_category(self, client, db, admin_token):
        p1 = make_product(db, "MOB001")
        p1.categorie = "Boissons"
        p1.sous_categorie = "Jus"
        p2 = make_product(db, "MOB002")
        p2.categorie = "Snacks"
        db.commit()
        r = client.get("/api/v1/products?categorie=Boissons", headers=auth(admin_token))
        assert r.status_code == 200
        codes = [x["product_code"] for x in r.json()["items"]]
        assert "MOB001" in codes
        assert "MOB002" not in codes

    def test_missing_mobile_category_filter(self, client, db, admin_token):
        p1 = make_product(db, "NOMOB1")
        p1.categorie = None
        p2 = make_product(db, "NOMOB2")
        p2.categorie = "Cat"
        db.commit()
        r = client.get("/api/v1/products?missing_mobile_category=true", headers=auth(admin_token))
        codes = [x["product_code"] for x in r.json()["items"]]
        assert "NOMOB1" in codes
        assert "NOMOB2" not in codes

    def test_create_product_upserts_mobile_referential(self, client, db, admin_token):
        r = client.post(
            "/api/v1/products",
            json={
                "product_code": "UPS001",
                "name": "Upsert cat",
                "categorie": "Nouvelle cat",
                "sous_categorie": "Nouvelle sous",
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 201
        from app.models.catalog import CatalogCategorie, CatalogSousCategorie

        cat = db.query(CatalogCategorie).filter(CatalogCategorie.name == "Nouvelle cat").first()
        assert cat is not None
        sc = db.query(CatalogSousCategorie).filter(CatalogSousCategorie.name == "Nouvelle sous").first()
        assert sc is not None
        assert sc.categorie_id == cat.id

    def test_bulk_assign_mobile_categories(self, client, db, admin_token):
        p1 = make_product(db, "BLK001")
        p2 = make_product(db, "BLK002")
        r = client.post(
            "/api/v1/products/bulk-assign",
            json={
                "product_ids": [p1.id, p2.id],
                "categorie": "BulkCat",
                "sous_categorie": "BulkSub",
            },
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["updated"] == 2
        db.refresh(p1)
        db.refresh(p2)
        assert p1.categorie == "BulkCat"
        assert p2.sous_categorie == "BulkSub"

    def test_update_categorie_clears_sous_categorie(self, client, db, admin_token):
        p = make_product(db, "CATSW001")
        p.categorie = "OldCat"
        p.sous_categorie = "OldSub"
        db.commit()
        r = client.put(
            f"/api/v1/products/{p.id}",
            json={"categorie": "NewCat"},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["categorie"] == "NewCat"
        assert r.json()["sous_categorie"] is None

    def test_assign_categorie_clears_sous_categorie(self, client, db, admin_token):
        p = make_product(db, "CATSW002")
        p.categorie = "OldCat"
        p.sous_categorie = "OldSub"
        db.commit()
        r = client.post(
            f"/api/v1/products/{p.id}/assign",
            json={"categorie": "NewCat", "sous_categorie": None},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["categorie"] == "NewCat"
        assert r.json()["sous_categorie"] is None

    def test_export_uncategorized_csv(self, client, db, admin_token):
        p = make_product(db, "EXP001")
        p.categorie = None
        db.commit()
        r = client.get("/api/v1/products/export/uncategorized", headers=auth(admin_token))
        assert r.status_code == 200
        assert "product_code" in r.text
        assert "EXP001" in r.text

    def test_mobile_list_omits_sync_fields(self, client, db, buyer_token):
        p = make_product(db, "MOBAPI1")
        p.gamme = "SyncGamme"
        p.famille = "SyncFam"
        p.categorie = "MobileCat"
        db.commit()
        r = client.get("/api/v1/products/mobile", headers=auth(buyer_token))
        assert r.status_code == 200
        item = next(x for x in r.json()["items"] if x["product_code"] == "MOBAPI1")
        assert "gamme" not in item
        assert "famille" not in item
        assert "synced_from_intermediate" not in item
        assert item["categorie"] == "MobileCat"
        assert item["is_liquidation"] is False

    def test_update_is_liquidation(self, client, db, admin_token):
        p = make_product(db, "LIQ001", discount_rate=15.0)
        r = client.put(
            f"/api/v1/products/{p.id}",
            json={"discount_rate": 15.0, "is_liquidation": True},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["is_liquidation"] is True

    def test_mobile_filter_is_liquidation(self, client, db, buyer_token):
        p1 = make_product(db, "LIQ002", discount_rate=10.0)
        p1.is_liquidation = True
        make_product(db, "LIQ003", discount_rate=10.0)
        db.commit()
        r = client.get("/api/v1/products/mobile?is_liquidation=true", headers=auth(buyer_token))
        codes = [x["product_code"] for x in r.json()["items"]]
        assert "LIQ002" in codes
        assert "LIQ003" not in codes

    def test_include_liquidations_with_gamme(self, client, db, buyer_token):
        p = make_product(db, "LIQ005", discount_rate=15.0)
        p.gamme = "Alimentaire"
        p.is_liquidation = True
        prm = make_product(db, "PRM001", discount_rate=0)
        prm.gamme = "Promptinos"
        db.commit()
        r = client.get(
            "/api/v1/products?gamme=Promptinos&include_liquidations=true",
            headers=auth(buyer_token),
        )
        codes = {x["product_code"] for x in r.json()["items"]}
        assert "PRM001" in codes
        assert "LIQ005" in codes

    def test_discount_zero_clears_liquidation(self, client, db, admin_token):
        p = make_product(db, "LIQ004", discount_rate=20.0)
        p.is_liquidation = True
        db.commit()
        r = client.put(
            f"/api/v1/products/{p.id}",
            json={"discount_rate": 0},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["is_liquidation"] is False

    def test_mobile_get_by_code(self, client, db, buyer_token):
        p = make_product(db, "MOBAPI2")
        p.categorie = "Boissons"
        db.commit()
        r = client.get("/api/v1/products/mobile/by-code/MOBAPI2", headers=auth(buyer_token))
        assert r.status_code == 200
        assert r.json()["categorie"] == "Boissons"
        assert "gamme" not in r.json()


class TestETLProductSync:
    def test_bulk_sync_creates_new_products(self, client, etl_token):
        r = client.post("/api/v1/sync/products/bulk",
                        json={"items": [{"product_code": "ETL001", "name": "ETL Product",
                                         "base_price": 99.0, "discount_rate": 5.0,
                                         "is_active": True}]},
                        headers=auth(etl_token))
        assert r.status_code == 200

    def test_bulk_sync_sets_synced_flag(self, client, db, etl_token):
        client.post("/api/v1/sync/products/bulk",
                    json={"items": [{"product_code": "ETL002", "name": "ETL2",
                                     "base_price": 50.0, "discount_rate": 0, "is_active": True}]},
                    headers=auth(etl_token))
        from app.services.product import get_product_by_code
        from app.db.session import SessionLocal
        session = SessionLocal()
        try:
            p = get_product_by_code(session, "ETL002")
            assert p is not None
            assert p.synced_from_intermediate is True
        finally:
            session.close()

    def test_bulk_sync_updates_price_only_for_existing(self, client, db, etl_token):
        """CDC §7.4: existing products → update price only, not name."""
        p = make_product(db, "EXISTING001", base_price=100.0)
        original_name = p.name

        client.post("/api/v1/sync/products/bulk",
                    json={"items": [{"product_code": "EXISTING001",
                                     "name": "CHANGED NAME",
                                     "base_price": 200.0, "discount_rate": 10.0,
                                     "is_active": True}]},
                    headers=auth(etl_token))

        # Use a fresh session — the test's db fixture has a stale object
        from app.db.session import SessionLocal
        from app.models.product import Product
        session = SessionLocal()
        try:
            updated = session.query(Product).filter(Product.product_code == "EXISTING001").first()
            assert float(updated.base_price) == 200.0      # price updated
            assert float(updated.discount_rate) == 10.0    # discount updated
            assert updated.name == original_name           # name NOT changed
            assert updated.synced_from_intermediate is True
        finally:
            session.close()

    def test_bulk_sync_requires_service_token(self, client, admin_token):
        r = client.post("/api/v1/sync/products/bulk",
                        json={"items": []},
                        headers=auth(admin_token))
        assert r.status_code == 401

    def test_discount_rate_applied_to_final_price(self, client, db, buyer_token):
        make_product(db, "DISC001", base_price=100.0, discount_rate=20.0)
        r = client.get("/api/v1/products/search?q=DISC001", headers=auth(buyer_token))
        product = r.json()["items"][0]
        assert product["final_price"] == pytest.approx(80.0, abs=0.01)


import pytest
