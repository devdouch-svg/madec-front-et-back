"""Import the WF product Excel into catalog + products (upsert by product_code)."""
from __future__ import annotations

import logging
import re
import shutil
import unicodedata
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.catalog import CatalogCategorie, CatalogSousCategorie, CatalogType
from app.models.product import Product

logger = logging.getLogger("mymadec.import_wf")

DEFAULT_XLSX = Path(r"D:\Mymadec\LISTE BASE APPLI SALARIE WF_ Brief Dev 2026.xlsx")
DEFAULT_PRODUCT_IMAGES = Path(r"D:\Mymadec\exports\exports\uploads\products")
DEFAULT_CATEGORY_IMAGES = Path(r"D:\Mymadec\exports\exports\uploads\categories")
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _clean(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clip(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    return value[:max_len]


def _norm_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.upper().replace("'", "").replace("’", "").replace("`", "")
    text = text.replace("P TIT", "PTIT").replace("P-TIT", "PTIT")
    text = text.replace("H.V", "HUILE VEGETALE").replace("H-V", "HUILE VEGETALE")
    return re.sub(r"[^A-Z0-9]+", "-", text).strip("-")


def _compact(value: str) -> str:
    return _norm_key(value).replace("-", "")


def _find_export_image(product_code: str, name: str, files: list[Path]) -> Path | None:
    """Match an export file to a product. No match → None (leave image empty)."""
    code_key = _norm_key(product_code)
    name_key = _norm_key(name)
    if not name_key or name_key == code_key:
        name_key = ""
    code_c = _compact(product_code)
    name_c = _compact(name) if name_key else ""

    exact: Path | None = None
    prefix_hits: list[tuple[int, Path]] = []
    for path in files:
        stem_key = _norm_key(path.stem)
        stem_c = _compact(path.stem)
        if stem_key == code_key or stem_c == code_c:
            return path
        if name_key and stem_key == name_key:
            exact = path
            continue
        if not name_c or len(name_c) < 8:
            continue
        if (
            stem_key.startswith(name_key + "-")
            or stem_c.startswith(name_c)
            or (len(stem_c) >= 12 and name_c.startswith(stem_c))
        ):
            prefix_hits.append((abs(len(stem_c) - len(name_c)), path))
    if exact:
        return exact
    if prefix_hits:
        prefix_hits.sort()
        return prefix_hits[0][1]
    return None


def attach_export_product_images(
    db: Session,
    *,
    images_dir: Path | None = None,
) -> dict[str, int]:
    src = (images_dir or DEFAULT_PRODUCT_IMAGES).resolve()
    if not src.is_dir():
        raise FileNotFoundError(f"Product images folder not found: {src}")

    files = [p for p in src.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTS]
    dest_dir = Path(settings.UPLOAD_DIR) / "products"
    dest_dir.mkdir(parents=True, exist_ok=True)

    linked = skipped = copied = 0
    used_files: set[Path] = set()
    products = sorted(db.query(Product).all(), key=lambda p: len(p.name or ""), reverse=True)
    for product in products:
        hit = _find_export_image(product.product_code, product.name or "", files)
        if hit is None or hit in used_files:
            product.image_path = None
            skipped += 1
            continue
        used_files.add(hit)
        ext = hit.suffix.lower() or ".png"
        dest = dest_dir / f"{product.product_code}{ext}"
        shutil.copy2(hit, dest)
        product.image_path = f"/uploads/products/{product.product_code}{ext}"
        linked += 1
        copied += 1
        logger.info("Image %s <- %s", product.product_code, hit.name)

    db.commit()
    return {
        "images_available": len(files),
        "images_linked": linked,
        "images_copied": copied,
        "products_without_image": skipped,
    }


def attach_export_category_images(
    db: Session,
    *,
    images_dir: Path | None = None,
) -> dict[str, int]:
    from app.db.seed_ctgs_categories import LABELS

    src = (images_dir or DEFAULT_CATEGORY_IMAGES).resolve()
    if not src.is_dir():
        raise FileNotFoundError(f"Category images folder not found: {src}")

    files = [p for p in src.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTS]
    by_compact: dict[str, Path] = {}
    for path in files:
        by_compact[_compact(path.stem)] = path
        label = LABELS.get(path.stem.lower())
        if label:
            by_compact[_compact(label)] = path

    dest_dir = Path(settings.UPLOAD_DIR) / "categories"
    dest_dir.mkdir(parents=True, exist_ok=True)

    linked = skipped = 0
    for cat in db.query(CatalogCategorie).all():
        hit = by_compact.get(_compact(cat.name or ""))
        if hit is None:
            cat.image_path = None
            skipped += 1
            continue
        ext = hit.suffix.lower() or ".png"
        dest = dest_dir / f"{hit.stem}{ext}"
        shutil.copy2(hit, dest)
        cat.image_path = f"/uploads/categories/{hit.stem}{ext}"
        linked += 1
        logger.info("Category image %s <- %s", cat.name, hit.name)

    db.commit()
    return {
        "category_images_available": len(files),
        "categories_with_image": linked,
        "categories_without_image": skipped,
    }


def _get_or_create_categorie(
    db: Session, cache: dict[str, CatalogCategorie], name: str, sort_order: int
) -> tuple[CatalogCategorie, bool]:
    key = name.lower()
    if key in cache:
        return cache[key], False
    existing = (
        db.query(CatalogCategorie)
        .filter(func.lower(CatalogCategorie.name) == key)
        .first()
    )
    if existing:
        cache[key] = existing
        return existing, False
    row = CatalogCategorie(name=_clip(name, 100), sort_order=sort_order, is_active=True)
    db.add(row)
    db.flush()
    cache[key] = row
    return row, True


def _get_or_create_sous(
    db: Session,
    cache: dict[tuple[int, str], CatalogSousCategorie],
    categorie: CatalogCategorie,
    name: str,
    sort_order: int,
) -> tuple[CatalogSousCategorie, bool]:
    key = (categorie.id, name.lower())
    if key in cache:
        return cache[key], False
    existing = (
        db.query(CatalogSousCategorie)
        .filter(
            CatalogSousCategorie.categorie_id == categorie.id,
            func.lower(CatalogSousCategorie.name) == name.lower(),
        )
        .first()
    )
    if existing:
        cache[key] = existing
        return existing, False
    row = CatalogSousCategorie(
        categorie_id=categorie.id,
        name=_clip(name, 100),
        sort_order=sort_order,
        is_active=True,
    )
    db.add(row)
    db.flush()
    cache[key] = row
    return row, True


def _get_or_create_type(
    db: Session,
    cache: dict[tuple[int, str], CatalogType],
    sous: CatalogSousCategorie,
    name: str,
    sort_order: int,
) -> tuple[CatalogType, bool]:
    key = (sous.id, name.lower())
    if key in cache:
        return cache[key], False
    existing = (
        db.query(CatalogType)
        .filter(
            CatalogType.sous_categorie_id == sous.id,
            func.lower(CatalogType.name) == name.lower(),
        )
        .first()
    )
    if existing:
        cache[key] = existing
        return existing, False
    row = CatalogType(
        sous_categorie_id=sous.id,
        name=_clip(name, 100),
        sort_order=sort_order,
        is_active=True,
    )
    db.add(row)
    db.flush()
    cache[key] = row
    return row, True


def load_wf_rows(path: Path) -> list[dict[str, str]]:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]
        last_cat = last_sous = last_type = None
        out: list[dict[str, str]] = []
        for i, raw in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                continue
            cat = _clean(raw[0] if len(raw) > 0 else None) or last_cat
            sous = _clean(raw[1] if len(raw) > 1 else None) or last_sous
            typ = _clean(raw[2] if len(raw) > 2 else None) or last_type
            code = _clean(raw[3] if len(raw) > 3 else None)
            name = _clean(raw[4] if len(raw) > 4 else None)
            # Marque is per-row — do not copy the previous product's brand.
            marque = _clean(raw[5] if len(raw) > 5 else None)
            contenance = _clean(raw[6] if len(raw) > 6 else None)
            if cat:
                last_cat = cat
            if sous:
                last_sous = sous
            if typ:
                last_type = typ
            if not code:
                continue
            out.append(
                {
                    "categorie": last_cat or "Non classé",
                    "sous_categorie": last_sous or last_cat or "Général",
                    "type_produit": last_type or "",
                    "product_code": code,
                    "name": name or "",
                    "marque": marque or "",
                    "contenance": contenance or "",
                }
            )
        return out
    finally:
        wb.close()


def import_wf_xlsx(
    db: Session,
    *,
    xlsx_path: Path | None = None,
    images_dir: Path | None = None,
) -> dict[str, int]:
    path = (xlsx_path or DEFAULT_XLSX).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Excel not found: {path}")

    rows = load_wf_rows(path)
    if not rows:
        raise RuntimeError(f"No product rows in {path}")

    cat_cache: dict[str, CatalogCategorie] = {}
    sous_cache: dict[tuple[int, str], CatalogSousCategorie] = {}
    type_cache: dict[tuple[int, str], CatalogType] = {}
    cat_order: dict[str, int] = {}
    sous_order: dict[tuple[int, str], int] = {}
    type_order: dict[tuple[int, str], int] = {}

    created = updated = skipped = 0
    cats_created = sous_created = types_created = 0
    product_sort = 0

    existing_codes = {
        p.product_code: p
        for p in db.query(Product)
        .filter(Product.product_code.in_([r["product_code"] for r in rows]))
        .all()
    }

    for row in rows:
        cat_name = row["categorie"]
        sous_name = row["sous_categorie"]
        type_name = row["type_produit"]
        code = _clip(row["product_code"], 100)
        if not code:
            skipped += 1
            continue

        cat_key = cat_name.lower()
        if cat_key not in cat_order:
            cat_order[cat_key] = len(cat_order)
        cat, is_new_cat = _get_or_create_categorie(db, cat_cache, cat_name, cat_order[cat_key])
        if is_new_cat:
            cats_created += 1

        sous_key = (cat.id, sous_name.lower())
        if sous_key not in sous_order:
            sous_order[sous_key] = sum(1 for k in sous_order if k[0] == cat.id)
        sous, is_new_sous = _get_or_create_sous(db, sous_cache, cat, sous_name, sous_order[sous_key])
        if is_new_sous:
            sous_created += 1

        if type_name:
            type_key = (sous.id, type_name.lower())
            if type_key not in type_order:
                type_order[type_key] = sum(1 for k in type_order if k[0] == sous.id)
            _, is_new_type = _get_or_create_type(db, type_cache, sous, type_name, type_order[type_key])
            if is_new_type:
                types_created += 1

        marque = _clip(row["marque"], 100) or None
        product_sort += 10
        designation = _clip(row["name"], 255) or code

        payload = dict(
            name=designation,
            unit=_clip(row["contenance"], 20),
            type_produit=_clip(type_name, 100) or None,
            sort_order=product_sort,
            gamme=marque,
            famille=_clip(cat_name, 100),
            sous_famille=_clip(sous_name, 100),
            categorie=_clip(cat_name, 100),
            sous_categorie=_clip(sous_name, 100),
            productsalesgroup_code="FOOD",
            society_code="MADEC",
            base_price=50.65,
            discount_rate=0,
            is_active=True,
            synced_from_intermediate=False,
        )

        existing = existing_codes.get(code)
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            updated += 1
        else:
            product = Product(product_code=code, **payload)
            db.add(product)
            existing_codes[code] = product
            created += 1

    from app.models.order import OrderLine

    xlsx_codes = {r["product_code"] for r in rows}
    extras = [p for p in db.query(Product).all() if p.product_code not in xlsx_codes]
    extra_ids = [p.id for p in extras]
    extras_deleted = 0
    order_lines_deleted = 0
    if extra_ids:
        order_lines_deleted = (
            db.query(OrderLine)
            .filter(OrderLine.product_id.in_(extra_ids))
            .delete(synchronize_session=False)
        )
        extras_deleted = (
            db.query(Product)
            .filter(Product.id.in_(extra_ids))
            .delete(synchronize_session=False)
        )

    image_stats = attach_export_product_images(db, images_dir=images_dir)
    category_stats = attach_export_category_images(db)
    # attach_export_product_images already commits
    return {
        "rows_in_file": len(rows),
        "products_created": created,
        "products_updated": updated,
        "products_skipped": skipped,
        "extras_deleted": extras_deleted,
        "order_lines_deleted": order_lines_deleted,
        "categories_created": cats_created,
        "sous_categories_created": sous_created,
        "types_created": types_created,
        "categories_total": db.query(CatalogCategorie).count(),
        "sous_categories_total": db.query(CatalogSousCategorie).count(),
        "types_total": db.query(CatalogType).count(),
        "products_total": db.query(Product).count(),
        **image_stats,
        **category_stats,
    }
