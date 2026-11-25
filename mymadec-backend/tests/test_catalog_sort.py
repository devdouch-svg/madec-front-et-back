"""Tests for catalog drag-and-drop reorder + product types."""
from __future__ import annotations

from tests.conftest import auth, make_product


def _cat_tree(client, token):
    c = client.post("/api/v1/catalog/categories", json={"name": "Sauces"}, headers=auth(token))
    assert c.status_code == 201
    cat_id = c.json()["id"]
    sc = client.post(
        "/api/v1/catalog/sous-categories",
        json={"categorie_id": cat_id, "name": "Mayonnaises"},
        headers=auth(token),
    )
    assert sc.status_code == 201
    return cat_id, sc.json()["id"]


class TestCatalogReorder:
    def test_reorder_categories(self, client, admin_token):
        a = client.post("/api/v1/catalog/categories", json={"name": "Alpha"}, headers=auth(admin_token))
        b = client.post("/api/v1/catalog/categories", json={"name": "Beta"}, headers=auth(admin_token))
        ids = [a.json()["id"], b.json()["id"]]
        r = client.put(
            "/api/v1/catalog/reorder/categories",
            json={"ids": list(reversed(ids))},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        assert r.json()["updated"] == 2
        listed = client.get("/api/v1/catalog/categories", headers=auth(admin_token)).json()
        names = [row["name"] for row in listed[:2]]
        assert names == ["Beta", "Alpha"]
        assert listed[0]["sort_order"] == 10
        assert listed[1]["sort_order"] == 20

    def test_reorder_sous_categories_requires_parent(self, client, admin_token):
        cat_id, sc_id = _cat_tree(client, admin_token)
        sc2 = client.post(
            "/api/v1/catalog/sous-categories",
            json={"categorie_id": cat_id, "name": "Ketchups"},
            headers=auth(admin_token),
        )
        sc2_id = sc2.json()["id"]
        r = client.put(
            f"/api/v1/catalog/reorder/sous-categories?categorie_id={cat_id}",
            json={"ids": [sc2_id, sc_id]},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        listed = client.get(
            f"/api/v1/catalog/sous-categories?categorie_id={cat_id}",
            headers=auth(admin_token),
        ).json()
        assert [row["name"] for row in listed] == ["Ketchups", "Mayonnaises"]

    def test_types_and_product_order(self, client, db, admin_token):
        cat_id, sc_id = _cat_tree(client, admin_token)
        p1 = make_product(db, "T1")
        p1.categorie = "Sauces"
        p1.sous_categorie = "Mayonnaises"
        p1.type_produit = "Classique"
        p1.name = "Mayo A"
        p2 = make_product(db, "T2")
        p2.categorie = "Sauces"
        p2.sous_categorie = "Mayonnaises"
        p2.type_produit = "Classique"
        p2.name = "Mayo B"
        db.commit()

        types = client.get(
            f"/api/v1/catalog/types?sous_categorie_id={sc_id}",
            headers=auth(admin_token),
        )
        assert types.status_code == 200
        assert any(t["name"] == "Classique" for t in types.json())
        created = client.post(
            "/api/v1/catalog/types",
            json={"sous_categorie_id": sc_id, "name": "Light"},
            headers=auth(admin_token),
        )
        assert created.status_code == 201
        type_a = next(t["id"] for t in client.get(
            f"/api/v1/catalog/types?sous_categorie_id={sc_id}", headers=auth(admin_token)
        ).json() if t["name"] == "Classique")
        type_b = created.json()["id"]
        r = client.put(
            f"/api/v1/catalog/reorder/types?sous_categorie_id={sc_id}",
            json={"ids": [type_b, type_a]},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        type_names = [
            t["name"]
            for t in client.get(
                f"/api/v1/catalog/types?sous_categorie_id={sc_id}", headers=auth(admin_token)
            ).json()
        ]
        assert type_names[:2] == ["Light", "Classique"]

        prods = client.get(
            "/api/v1/products?categorie=Sauces&sous_categorie=Mayonnaises&type_produit=Classique",
            headers=auth(admin_token),
        )
        assert prods.status_code == 200
        items = prods.json()["items"]
        assert [p["name"] for p in items] == ["Mayo A", "Mayo B"]

        r = client.put(
            "/api/v1/catalog/reorder/products",
            json={"ids": [p2.id, p1.id]},
            headers=auth(admin_token),
        )
        assert r.status_code == 200
        prods2 = client.get(
            "/api/v1/products?categorie=Sauces&sous_categorie=Mayonnaises&type_produit=Classique",
            headers=auth(admin_token),
        ).json()["items"]
        assert [p["name"] for p in prods2] == ["Mayo B", "Mayo A"]

        tree = client.get("/api/v1/catalog/categories/tree", headers=auth(admin_token)).json()
        sauces = next(c for c in tree if c["name"] == "Sauces")
        mayo = next(sc for sc in sauces["sous_categories"] if sc["name"] == "Mayonnaises")
        assert any(t["name"] == "Classique" for t in mayo["types"])

    def test_acheteur_cannot_reorder(self, client, buyer_token, admin_token):
        a = client.post("/api/v1/catalog/categories", json={"name": "One"}, headers=auth(admin_token))
        b = client.post("/api/v1/catalog/categories", json={"name": "Two"}, headers=auth(admin_token))
        r = client.put(
            "/api/v1/catalog/reorder/categories",
            json={"ids": [b.json()["id"], a.json()["id"]]},
            headers=auth(buyer_token),
        )
        assert r.status_code == 403
