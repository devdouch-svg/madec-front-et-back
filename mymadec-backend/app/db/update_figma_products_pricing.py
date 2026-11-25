"""Update base_price + unit (contenance) for all products from CSV and product names."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.figma_product_catalog import default_catalog_csv, load_catalog_rows
from app.db.product_pricing import (
    pick_pricing_rows,
    resolve_product_price,
    resolve_product_unit,
)
from app.models.product import Product

logger = logging.getLogger("mymadec.update_pricing")


def update_figma_products_pricing(
    db: Session,
    *,
    catalog_csv: Path | None = None,
    only_missing: bool = False,
    use_fake_prices: bool = True,
) -> dict[str, int | str]:
    csv_path = (catalog_csv or default_catalog_csv()).resolve()
    pricing_by_name = {}
    if csv_path.is_file():
        pricing_by_name = pick_pricing_rows(load_catalog_rows(csv_path))

    products = db.query(Product).order_by(Product.id).all()
    updated_price = 0
    updated_unit = 0
    skipped = 0

    for product in products:
        row = pricing_by_name.get(product.name.strip().upper(), {})
        csv_prix = row.get("prix_unitaire_dh")
        csv_cont = row.get("contenance")
        csv_unit = row.get("unite")

        new_unit = resolve_product_unit(
            product.name,
            csv_contenance=csv_cont,
            csv_unite=csv_unit,
            product_code=product.product_code,
        )
        new_price = resolve_product_price(
            product.product_code,
            csv_prix=csv_prix,
            use_fake_if_missing=use_fake_prices,
        )

        changed = False
        if new_unit and (not only_missing or not product.unit or str(product.unit).strip() in ("", "0", "0G", "0ML")):
            if product.unit != new_unit:
                product.unit = new_unit
                updated_unit += 1
                changed = True
        if new_price is not None and (not only_missing or product.base_price is None or float(product.base_price or 0) <= 0):
            if product.base_price != new_price:
                product.base_price = new_price
                updated_price += 1
                changed = True

        if changed:
            logger.info("%s -> %s DH, %s", product.product_code, new_price, new_unit)
        else:
            skipped += 1

    db.commit()

    return {
        "products_total": len(products),
        "prices_updated": updated_price,
        "units_updated": updated_unit,
        "unchanged": skipped,
        "catalog_csv": str(csv_path),
        "only_missing": only_missing,
        "use_fake_prices": use_fake_prices,
    }
