"""Tests for /catalog reference-data API (additive)."""
from __future__ import annotations

from tests.conftest import auth, make_product, make_user


class TestCatalogCRUD:
    def test_create_gamme_and_famille_hierarchy(self, client, admin_token):
        g = client.post("/api/v1/catalog/gammes", json={"name": "Plomberie"}, headers=auth(admin_token))
        assert g.status_code == 201
        gamme_id = g.json()["id"]

        f = client.post(
            "/api/v1/catalog/familles",
            json={"gamme_id": gamme_id, "name": "Robinetterie"},
            headers=auth(admin_token),
        )
        assert f.status_code == 201

        listed = client.get(f"/api/v1/catalog/familles?gamme_id={gamme_id}", headers=auth(admin_token))
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["gamme_name"] == "Plomberie"

    def test_create_societe_and_agence(self, client, admin_token):
        s = client.post(
            "/api/v1/catalog/societes",
            json={"code": "SOC99", "label": "MADEC Test"},
            headers=auth(admin_token),
        )
        assert s.status_code == 201
        societe_id = s.json()["id"]

        a = client.post(
            "/api/v1/catalog/agences",
            json={"societe_id": societe_id, "code": "001", "label": "Siège"},
            headers=auth(admin_token),
        )
        assert a.status_code == 201

    def test_acheteur_can_list_but_not_create(self, client, buyer_token, admin_token):
        client.post("/api/v1/catalog/gammes", json={"name": "Electrique"}, headers=auth(admin_token))
        r_list = client.get("/api/v1/catalog/gammes", headers=auth(buyer_token))
        assert r_list.status_code == 200
        r_create = client.post("/api/v1/catalog/gammes", json={"name": "Autre"}, headers=auth(buyer_token))
        assert r_create.status_code == 403

    def test_import_from_existing_product_data(self, client, db, admin_token):
        p = make_product(db, "IMP001")
        p.gamme = "GammeA"
        p.famille = "FamA"
        p.sous_famille = "SFA"
        db.commit()
        r = client.post("/api/v1/catalog/import-from-data", headers=auth(admin_token))
        assert r.status_code == 200
        body = r.json()
        assert body["gammes"] >= 1

    def test_gest_cannot_import_from_data(self, client, gest_token):
        r = client.post("/api/v1/catalog/import-from-data", headers=auth(gest_token))
        assert r.status_code == 403


class TestCatalogMobile:
    def test_create_categorie_and_sous_categorie_hierarchy(self, client, admin_token):
        c = client.post("/api/v1/catalog/categories", json={"name": "Boissons"}, headers=auth(admin_token))
        assert c.status_code == 201
        categorie_id = c.json()["id"]

        sc = client.post(
            "/api/v1/catalog/sous-categories",
            json={"categorie_id": categorie_id, "name": "Jus"},
            headers=auth(admin_token),
        )
        assert sc.status_code == 201

        listed = client.get(f"/api/v1/catalog/sous-categories?categorie_id={categorie_id}", headers=auth(admin_token))
        assert listed.status_code == 200
        assert len(listed.json()) == 1
        assert listed.json()[0]["categorie_name"] == "Boissons"

    def test_deactivate_categorie_deactivates_sous_categories(self, client, admin_token):
        c = client.post("/api/v1/catalog/categories", json={"name": "CascadeCat"}, headers=auth(admin_token))
        categorie_id = c.json()["id"]
        sc1 = client.post(
            "/api/v1/catalog/sous-categories",
            json={"categorie_id": categorie_id, "name": "SubA"},
            headers=auth(admin_token),
        )
        sc2 = client.post(
            "/api/v1/catalog/sous-categories",
            json={"categorie_id": categorie_id, "name": "SubB"},
            headers=auth(admin_token),
        )
        assert sc1.status_code == 201 and sc2.status_code == 201

        off = client.put(
            f"/api/v1/catalog/categories/{categorie_id}",
            json={"is_active": False},
            headers=auth(admin_token),
        )
        assert off.status_code == 200
        assert off.json()["is_active"] is False

        listed = client.get(
            f"/api/v1/catalog/sous-categories?categorie_id={categorie_id}&include_inactive=true",
            headers=auth(admin_token),
        )
        assert listed.status_code == 200
        assert all(not row["is_active"] for row in listed.json())

        on = client.put(
            f"/api/v1/catalog/categories/{categorie_id}",
            json={"is_active": True},
            headers=auth(admin_token),
        )
        assert on.status_code == 200
        assert on.json()["is_active"] is True

        relisted = client.get(
            f"/api/v1/catalog/sous-categories?categorie_id={categorie_id}&include_inactive=true",
            headers=auth(admin_token),
        )
        assert relisted.status_code == 200
        assert all(row["is_active"] for row in relisted.json())

    def test_categories_tree(self, client, admin_token):
        c = client.post("/api/v1/catalog/categories", json={"name": "TreeCat"}, headers=auth(admin_token))
        categorie_id = c.json()["id"]
        client.post(
            "/api/v1/catalog/sous-categories",
            json={"categorie_id": categorie_id, "name": "TreeSub"},
            headers=auth(admin_token),
        )
        r = client.get("/api/v1/catalog/categories/tree", headers=auth(admin_token))
        assert r.status_code == 200
        node = next(x for x in r.json() if x["name"] == "TreeCat")
        assert len(node["sous_categories"]) == 1
        assert node["sous_categories"][0]["name"] == "TreeSub"

    def test_categories_tree_includes_product_counts(self, client, db, admin_token):
        from tests.conftest import make_product

        c = client.post("/api/v1/catalog/categories", json={"name": "CountCat"}, headers=auth(admin_token))
        cat_name = c.json()["name"]
        p = make_product(db, "CNT001")
        p.categorie = cat_name
        db.commit()
        r = client.get("/api/v1/catalog/categories/tree", headers=auth(admin_token))
        node = next(x for x in r.json() if x["name"] == cat_name)
        assert node["product_count"] >= 1
