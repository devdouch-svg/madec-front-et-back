"""Reset products + catalog référentiels and load MADEC food / non-food data."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.db.madec_catalog_data import MADEC_CATALOG, MOBILE_CATEGORIES, mobile_labels_for_famille
from app.models.catalog import (
    CatalogCategorie,
    CatalogFamille,
    CatalogGamme,
    CatalogSousCategorie,
    CatalogSousFamille,
)
import app.models  # noqa: F401 — ensures all models are registered before any mapper is used
from app.models.order import OrderLine
from app.models.product import Product

logger = logging.getLogger("mymadec.reset_catalog")


def reset_madec_catalog(db: Session) -> dict[str, int]:
    """
    Delete all products (and order lines referencing them) and catalog hierarchy,
    then insert MADEC gammes / familles / sous-familles + mobile categories + sample products.
    """
    lines_deleted = db.query(OrderLine).delete(synchronize_session=False)
    products_deleted = db.query(Product).delete(synchronize_session=False)
    db.query(CatalogSousCategorie).delete(synchronize_session=False)
    db.query(CatalogCategorie).delete(synchronize_session=False)
    gammes_deleted = db.query(CatalogGamme).delete(synchronize_session=False)
    db.flush()

    counts = {
        "order_lines_removed": lines_deleted,
        "products_removed": products_deleted,
        "catalog_gammes_removed": gammes_deleted,
        "gammes": 0,
        "familles": 0,
        "sous_familles": 0,
        "categories": 0,
        "sous_categories": 0,
        "products": 0,
    }

    for ci, (cat_name, sc_names) in enumerate(MOBILE_CATEGORIES):
        cat = CatalogCategorie(name=cat_name, sort_order=ci, is_active=True)
        db.add(cat)
        db.flush()
        counts["categories"] += 1
        for si, sc_name in enumerate(sc_names):
            db.add(
                CatalogSousCategorie(
                    categorie_id=cat.id,
                    name=sc_name,
                    sort_order=si,
                    is_active=True,
                )
            )
            counts["sous_categories"] += 1

    for gi, gamme_seed in enumerate(MADEC_CATALOG):
        gamme = CatalogGamme(name=gamme_seed.name, sort_order=gi, is_active=True)
        db.add(gamme)
        db.flush()
        counts["gammes"] += 1

        for fi, fam_seed in enumerate(gamme_seed.familles):
            famille = CatalogFamille(
                gamme_id=gamme.id,
                name=fam_seed.name,
                sort_order=fi,
                is_active=True,
            )
            db.add(famille)
            db.flush()
            counts["familles"] += 1

            for si, sf_name in enumerate(fam_seed.sous_familles):
                db.add(
                    CatalogSousFamille(
                        famille_id=famille.id,
                        name=sf_name,
                        sort_order=si,
                        is_active=True,
                    )
                )
                counts["sous_familles"] += 1

            psg = "NONFOOD" if gamme_seed.name == "Non alimentaire" else "FOOD"
            mobile_cat, mobile_sc = mobile_labels_for_famille(gamme_seed.name, fam_seed.name)
            for prod in fam_seed.products:
                db.add(
                    Product(
                        product_code=prod.code,
                        name=prod.name,
                        description=prod.description,
                        unit=prod.unit,
                        gamme=gamme_seed.name,
                        famille=fam_seed.name,
                        sous_famille=_brand_for_product(prod, fam_seed.sous_familles),
                        categorie=mobile_cat,
                        sous_categorie=mobile_sc,
                        productsalesgroup_code=prod.psg or psg,
                        society_code=prod.society,
                        base_price=prod.price,
                        discount_rate=prod.discount,
                        is_active=True,
                        synced_from_intermediate=False,
                    )
                )
                counts["products"] += 1

    db.commit()
    logger.info("MADEC catalog reset: %s", counts)
    return counts


def _brand_for_product(prod, sous_familles: list[str]) -> str:
    """Map product code prefix to brand when possible."""
    prefix = prod.code.split("-")[0]
    brand_map = {
        "IDEAL": "Ideal",
        "ASS": "Assila",
        "DP": "Del Pacha",
        "DAM": "Damti",
        "EBK": "El Baraka",
        "CHOC": "Chocao",
        "VIN": "MADEC",
        "LC": "La Chaîne",
        "EP": "MADEC",
        "MAY": "Mayfine",
        "JEL": "Jelly",
        "CHO": "Chobedo",
        "DEL": "Delicio",
        "TEM": "Temtem",
        "NET": "MADEC",
        "EXE": "Exet",
        "CLO": "Clorel",
        "EVY": "Evybaby",
        "SOI": "MADEC",
        "RAS": "MADEC",
        "HYG": "MADEC",
    }
    return brand_map.get(prefix, sous_familles[0] if sous_familles else "MADEC")
