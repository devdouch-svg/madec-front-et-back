"""Reset products + import Figma catalog with CTGS categories, sous-cats and images."""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.figma_product_catalog import (
    copy_product_images,
    default_catalog_csv,
    default_product_images_dir,
    image_path_for,
    load_catalog_rows,
    map_product_to_ctgs,
    pick_products,
    sql_safe_code,
)
from app.db.product_pricing import pick_pricing_rows, resolve_product_price, resolve_product_unit
from app.models.catalog import CatalogCategorie, CatalogSousCategorie
from app.models.order import OrderLine
from app.models.product import Product

logger = logging.getLogger("mymadec.seed_figma_products")


def _sous_index(db: Session) -> dict[str, list[str]]:
    """ctgs category name (lower) -> sous-categorie names in sort_order."""
    rows = (
        db.query(CatalogCategorie.name, CatalogSousCategorie.name, CatalogSousCategorie.sort_order)
        .join(CatalogSousCategorie, CatalogSousCategorie.categorie_id == CatalogCategorie.id)
        .order_by(CatalogCategorie.name, CatalogSousCategorie.sort_order, CatalogSousCategorie.name)
        .all()
    )
    out: dict[str, list[str]] = {}
    for cat_name, sc_name, _ in rows:
        out.setdefault(cat_name.lower(), []).append(sc_name)
    return out


def resolve_sous_categorie(
    sous_index: dict[str, list[str]],
    ctgs_cat: str,
    preferred: str | None,
) -> str | None:
    options = sous_index.get(ctgs_cat.lower(), [])
    if not options:
        return None
    if preferred:
        p = preferred.strip().lower()
        if p and p not in {"frame 1171275037", "ajouter une nouvelle carte", "greta", "cremerie"}:
            for s in options:
                if s.lower() == p:
                    return s
    return options[0]


def seed_figma_products(
    db: Session,
    *,
    catalog_csv: Path | None = None,
    images_dir: Path | None = None,
    copy_images: bool = True,
) -> dict[str, int | str]:
    csv_path = (catalog_csv or default_catalog_csv()).resolve()
    img_dir = (images_dir or default_product_images_dir()).resolve()
    uploads_dir = Path(settings.UPLOAD_DIR) / "products"

    if not csv_path.is_file():
        raise FileNotFoundError(f"Catalog CSV not found: {csv_path}")

    cats = db.query(CatalogCategorie).count()
    if cats == 0:
        raise RuntimeError("No catalog_categories — run seed_ctgs_categories + seed_figma_sous_categories first")

    sous_index = _sous_index(db)
    if not sous_index:
        raise RuntimeError("No catalog_sous_categories — run seed_figma_sous_categories first")

    images_copied = 0
    by_image: dict[str, str] = {}
    if copy_images:
        if not img_dir.is_dir():
            raise FileNotFoundError(f"Product images dir not found: {img_dir}")
        by_image, images_copied = copy_product_images(img_dir, uploads_dir)
    elif uploads_dir.is_dir():
        from app.db.figma_product_catalog import load_image_index

        raw = load_image_index(img_dir, uploads_dir)
        for name_upper, (code, ext, _) in raw.items():
            if (uploads_dir / f"{code}{ext}").is_file():
                by_image[name_upper] = f"/uploads/products/{code}{ext}"

    lines_deleted = db.query(OrderLine).delete(synchronize_session=False)
    products_deleted = db.query(Product).delete(synchronize_session=False)
    db.flush()

    rows = load_catalog_rows(csv_path)
    products = pick_products(rows)
    pricing_by_name = pick_pricing_rows(rows)

    inserted = 0
    with_image = 0
    skipped = 0
    seen_codes: set[str] = set()

    for row in sorted(products.values(), key=lambda r: r.get("produit", "").upper()):
        name = row.get("produit", "").strip()
        code = sql_safe_code(name)
        if not code or code in seen_codes:
            skipped += 1
            continue
        seen_codes.add(code)

        old_cat = row.get("categorie") or row.get("gamme") or "Epicerie"
        raw_sous = row.get("sous_categorie") or ""
        ctgs_cat = map_product_to_ctgs(old_cat, raw_sous or None, name)
        sous_cat = resolve_sous_categorie(sous_index, ctgs_cat, raw_sous or None)

        img = image_path_for(name, by_image, uploads_dir)
        if img:
            with_image += 1

        marque = (row.get("marque") or "").strip() or None
        gamme = (row.get("gamme") or old_cat or "").strip() or None
        price_row = pricing_by_name.get(name.upper(), row)
        unit = resolve_product_unit(
            name,
            csv_contenance=price_row.get("contenance"),
            csv_unite=price_row.get("unite"),
            product_code=code,
        )
        price = resolve_product_price(
            code,
            csv_prix=price_row.get("prix_unitaire_dh"),
            use_fake_if_missing=True,
        )

        db.add(
            Product(
                product_code=code,
                name=name,
                description=None,
                unit=unit,
                gamme=gamme,
                famille=old_cat,
                sous_famille=marque,
                categorie=ctgs_cat,
                sous_categorie=sous_cat,
                productsalesgroup_code="FOOD",
                society_code="MADEC",
                base_price=price,
                discount_rate=0,
                image_path=img,
                is_active=True,
                synced_from_intermediate=False,
            )
        )
        inserted += 1
        logger.info("Product %r -> %s / %s", name, ctgs_cat, sous_cat)

    db.commit()

    return {
        "order_lines_deleted": lines_deleted,
        "products_deleted": products_deleted,
        "images_copied": images_copied,
        "products_inserted": inserted,
        "products_with_image": with_image,
        "products_skipped": skipped,
        "catalog_csv": str(csv_path),
        "images_dir": str(img_dir),
        "upload_dir": str(uploads_dir),
    }
