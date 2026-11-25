"""Tests for MADEC catalog reset."""
from app.db.reset_madec_catalog import reset_madec_catalog
from app.models.catalog import CatalogCategorie, CatalogFamille, CatalogGamme, CatalogSousFamille
from app.models.product import Product


class TestResetMadecCatalog:
    def test_reset_loads_food_and_non_food(self, db):
        counts = reset_madec_catalog(db)
        assert counts["gammes"] == 2
        assert counts["categories"] == 3
        assert counts["products"] > 0
        assert db.query(CatalogGamme).filter(CatalogGamme.name == "Alimentaire").first()
        assert db.query(CatalogGamme).filter(CatalogGamme.name == "Non alimentaire").first()
        confiture = db.query(Product).filter(Product.famille == "Confitures et conserves").first()
        assert confiture is not None
        assert confiture.sous_famille == "El Baraka"
        assert confiture.categorie == "Épicerie sucrée"
        assert confiture.sous_categorie == "Confitures"
        gel = db.query(Product).filter(Product.famille == "Gel nettoyant").first()
        assert gel is not None
        assert gel.categorie == "Hygiène & entretien"
        assert db.query(CatalogCategorie).filter(CatalogCategorie.name == "Épicerie sucrée").first()
        assert db.query(CatalogSousFamille).join(CatalogFamille).join(CatalogGamme).filter(
            CatalogGamme.name == "Alimentaire",
            CatalogSousFamille.name == "Damti",
        ).first()
