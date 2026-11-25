"""
Seed demo promotions and liquidations for mobile catalogue testing.

Inserts or updates 4 products with a discount:
  - 3 marked is_liquidation=True  → GET /products/mobile?is_liquidation=true
  - 1 promotion only              → visible via has_discount / Promotions

Idempotent — keyed by product_code (SEED-PROMO-001 … 004).
"""
from __future__ import annotations

import logging
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.models.product import Product
from app.services import catalog as catalog_svc

logger = logging.getLogger("mymadec.seed_promo_liquidations")

MARKER_PREFIX = "SEED-PROMO-"


class _PromoSeed(NamedTuple):
    code: str
    name: str
    description: str
    categorie: str
    sous_categorie: str
    base_price: float
    discount_rate: float
    is_liquidation: bool


PROMO_PRODUCTS: tuple[_PromoSeed, ...] = (
    _PromoSeed(
        "SEED-PROMO-001",
        "Liquidation — Confiture fraise El Baraka",
        "Promo liquidation confiture extra fraise 430g",
        "Epicerie",
        "Confitures",
        32.50,
        30.0,
        True,
    ),
    _PromoSeed(
        "SEED-PROMO-002",
        "Liquidation — Bouillon cube poulet Damti",
        "Promo liquidation bouillon poulet x24",
        "Epicerie",
        "Bouillons",
        18.90,
        25.0,
        True,
    ),
    _PromoSeed(
        "SEED-PROMO-003",
        "Liquidation — Gel nettoyant multi-surfaces",
        "Promo liquidation gel nettoyant 750ml",
        "Entretien & Nettoyage",
        "Gel nettoyant",
        24.90,
        20.0,
        True,
    ),
    _PromoSeed(
        "SEED-PROMO-004",
        "Promo — Chocao poudre chocolatée",
        "Promotion classique (hors liquidations)",
        "Biscuiterie, Confiserie & Snacks",
        "Chocolat",
        28.00,
        15.0,
        False,
    ),
)


def seed_promo_liquidations(db: Session) -> dict[str, int]:
    created = updated = 0

    for item in PROMO_PRODUCTS:
        catalog_svc.ensure_mobile_catalog_refs(db, item.categorie, item.sous_categorie)

        existing = (
            db.query(Product)
            .filter(Product.product_code == item.code)
            .first()
        )
        if existing:
            existing.name = item.name
            existing.description = item.description
            existing.unit = "u"
            existing.categorie = item.categorie
            existing.sous_categorie = item.sous_categorie
            existing.base_price = item.base_price
            existing.discount_rate = item.discount_rate
            existing.is_liquidation = item.is_liquidation
            existing.is_active = True
            existing.gamme = existing.gamme or "Alimentaire"
            existing.famille = existing.famille or "Promotions seed"
            existing.productsalesgroup_code = existing.productsalesgroup_code or "GRP01"
            existing.society_code = existing.society_code or "SOC01"
            updated += 1
            continue

        db.add(
            Product(
                product_code=item.code,
                name=item.name,
                description=item.description,
                unit="u",
                gamme="Alimentaire",
                famille="Promotions seed",
                sous_famille="Seed",
                categorie=item.categorie,
                sous_categorie=item.sous_categorie,
                productsalesgroup_code="GRP01",
                society_code="SOC01",
                base_price=item.base_price,
                discount_rate=item.discount_rate,
                is_liquidation=item.is_liquidation,
                is_active=True,
            )
        )
        created += 1

    db.commit()

    liquidations = sum(1 for p in PROMO_PRODUCTS if p.is_liquidation)
    promos = len(PROMO_PRODUCTS)
    logger.info(
        "Promo/liquidation seed done — %d created, %d updated (%d promos, %d liquidations)",
        created,
        updated,
        promos,
        liquidations,
    )
    return {
        "created": created,
        "updated": updated,
        "promotions": promos,
        "liquidations": liquidations,
    }


def clear_promo_liquidations(db: Session) -> int:
    deleted = (
        db.query(Product)
        .filter(Product.product_code.like(f"{MARKER_PREFIX}%"))
        .delete(synchronize_session=False)
    )
    db.commit()
    logger.info("Removed %d promo/liquidation seed products", deleted)
    return deleted
