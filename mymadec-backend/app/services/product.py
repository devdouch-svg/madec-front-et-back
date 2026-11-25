from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.catalog import CatalogCategorie, CatalogSousCategorie, CatalogType
from app.models.product import Product
from app.schemas.product import ProductAssign, ProductBulkAssign, ProductCreate, ProductSyncItem, ProductUpdate
from app.services import catalog as catalog_svc


def _resolve_catalog_name(
    db: Session,
    value: Optional[str],
    *,
    kind: str,
    parent_name: Optional[str] = None,
) -> Optional[str]:
    """Accept catalog name or numeric id from mobile clients.

    Mobile often sends categorie=1 instead of the label; exact string match then
    returns zero products. Resolve ids to names when possible.
    """
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if not raw.isdigit():
        return raw

    row_id = int(raw)
    if kind == "categorie":
        row = db.get(CatalogCategorie, row_id)
        return row.name if row else raw
    if kind == "sous_categorie":
        row = db.get(CatalogSousCategorie, row_id)
        if not row:
            return raw
        if parent_name:
            cat = row.categorie
            if cat and cat.name.casefold() != parent_name.casefold():
                # Id belongs to another category — keep as-is (likely wrong client input)
                return raw
        return row.name
    if kind == "type_produit":
        row = db.get(CatalogType, row_id)
        return row.name if row else raw
    return raw


def list_products(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    gamme: Optional[str] = None,
    famille: Optional[str] = None,
    sous_famille: Optional[str] = None,
    categorie: Optional[str] = None,
    sous_categorie: Optional[str] = None,
    missing_mobile_category: bool = False,
    society_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_discount: Optional[bool] = None,
    is_liquidation: Optional[bool] = None,
    include_liquidations: bool = False,
    type_produit: Optional[str] = None,
) -> tuple[List[Product], int]:
    categorie = _resolve_catalog_name(db, categorie, kind="categorie")
    sous_categorie = _resolve_catalog_name(
        db, sous_categorie, kind="sous_categorie", parent_name=categorie
    )
    type_produit = _resolve_catalog_name(db, type_produit, kind="type_produit")

    q = db.query(Product)
    if gamme:
        if include_liquidations:
            q = q.filter(or_(Product.gamme == gamme, Product.is_liquidation == True))  # noqa: E712
        else:
            q = q.filter(Product.gamme == gamme)
    if famille:
        q = q.filter(Product.famille == famille)
    if sous_famille:
        q = q.filter(Product.sous_famille == sous_famille)
    if categorie:
        q = q.filter(Product.categorie == categorie)
    if sous_categorie:
        q = q.filter(Product.sous_categorie == sous_categorie)
    if type_produit:
        q = q.filter(Product.type_produit == type_produit)
    if missing_mobile_category:
        q = q.filter(or_(Product.categorie == None, Product.categorie == ""))
    if society_code:
        q = q.filter(Product.society_code == society_code)
    if is_active is not None:
        q = q.filter(Product.is_active == is_active)
    if price_min is not None:
        q = q.filter(Product.final_price >= price_min)
    if price_max is not None:
        q = q.filter(Product.final_price <= price_max)
    if has_discount is True:
        q = q.filter(Product.discount_rate > 0)
    elif has_discount is False:
        q = q.filter(Product.discount_rate == 0)
    if is_liquidation is True:
        q = q.filter(Product.is_liquidation == True)  # noqa: E712
    elif is_liquidation is False:
        q = q.filter(Product.is_liquidation == False)  # noqa: E712
    if search:
        from app.core.strings import ilike_pattern
        like = ilike_pattern(search)
        q = q.filter(
            or_(
                Product.name.ilike(like),
                Product.product_code.ilike(like),
                Product.description.ilike(like),
            )
        )
    total = q.count()
    items = (
        q.order_by(Product.sort_order, Product.name, Product.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def _sync_mobile_refs(
    db: Session,
    categorie: Optional[str],
    sous_categorie: Optional[str],
    type_produit: Optional[str] = None,
) -> None:
    catalog_svc.ensure_mobile_catalog_refs(db, categorie, sous_categorie, type_produit)


def _next_product_sort_order(
    db: Session,
    *,
    categorie: Optional[str],
    sous_categorie: Optional[str],
    type_produit: Optional[str],
) -> int:
    q = db.query(func.coalesce(func.max(Product.sort_order), 0))
    if categorie:
        q = q.filter(Product.categorie == categorie)
    if sous_categorie:
        q = q.filter(Product.sous_categorie == sous_categorie)
    if type_produit:
        q = q.filter(Product.type_produit == type_produit)
    return int(q.scalar() or 0) + 10


def _norm_label(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _mobile_label_changed(old: Optional[str], new: Optional[str]) -> bool:
    a = _norm_label(old)
    b = _norm_label(new)
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    return a.casefold() != b.casefold()


def _apply_mobile_category_updates(
    product: Product,
    *,
    categorie: Optional[str],
    sous_categorie: Optional[str],
    categorie_set: bool,
    sous_categorie_set: bool,
) -> None:
    if categorie_set:
        if _mobile_label_changed(product.categorie, categorie) and not sous_categorie_set:
            product.sous_categorie = None
        product.categorie = _norm_label(categorie)
    if sous_categorie_set:
        product.sous_categorie = _norm_label(sous_categorie)


def get_product(db: Session, product_id: int, *, allow_inactive: bool = False) -> Product:
    product = db.get(Product, product_id)
    if not product or (not allow_inactive and not product.is_active):
        raise NotFoundException(f"Product {product_id} not found")
    return product


def get_product_by_code(db: Session, product_code: str) -> Optional[Product]:
    return db.query(Product).filter(Product.product_code == product_code).first()


def create_product(db: Session, data: ProductCreate) -> Product:
    if get_product_by_code(db, data.product_code):
        raise ConflictException(f"Product code {data.product_code!r} already exists")
    _sync_mobile_refs(db, data.categorie, data.sous_categorie, data.type_produit)
    payload = data.model_dump()
    payload["sort_order"] = _next_product_sort_order(
        db,
        categorie=data.categorie,
        sous_categorie=data.sous_categorie,
        type_produit=data.type_produit,
    )
    product = Product(**payload)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session, product_id: int, data: ProductUpdate, *, allow_inactive: bool = False
) -> Product:
    product = get_product(db, product_id, allow_inactive=allow_inactive)
    updates = data.model_dump(exclude_unset=True)
    if "categorie" in updates and _mobile_label_changed(product.categorie, updates["categorie"]):
        if "sous_categorie" not in updates:
            updates["sous_categorie"] = None
    if "categorie" in updates or "sous_categorie" in updates or "type_produit" in updates:
        cat = updates.get("categorie", product.categorie)
        sc = updates.get("sous_categorie", product.sous_categorie)
        tp = updates.get("type_produit", product.type_produit)
        _sync_mobile_refs(db, cat, sc, tp)
    # Liquidation is an independent merchandising flag: it may be toggled even
    # when the promotion (discount_rate) is 0. (Client remark 2026-08-07.)
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def toggle_product(db: Session, product_id: int, *, allow_inactive: bool = False) -> Product:
    product = get_product(db, product_id, allow_inactive=allow_inactive)
    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    return product


def assign_product(
    db: Session,
    product_id: int,
    data: ProductAssign,
    *,
    allow_inactive: bool = False,
) -> Product:
    product = get_product(db, product_id, allow_inactive=allow_inactive)
    fields = data.model_fields_set
    if "gamme" in fields and data.gamme is not None:
        product.gamme = data.gamme
    if "famille" in fields and data.famille is not None:
        product.famille = data.famille
    if "sous_famille" in fields and data.sous_famille is not None:
        product.sous_famille = data.sous_famille
    _apply_mobile_category_updates(
        product,
        categorie=data.categorie,
        sous_categorie=data.sous_categorie,
        categorie_set="categorie" in fields,
        sous_categorie_set="sous_categorie" in fields,
    )
    if "categorie" in fields or "sous_categorie" in fields:
        _sync_mobile_refs(db, product.categorie, product.sous_categorie)
    db.commit()
    db.refresh(product)
    return product


def bulk_assign_products(
    db: Session,
    data: ProductBulkAssign,
    *,
    allow_inactive: bool = False,
) -> int:
    fields = data.model_fields_set
    if not any(f in fields for f in ("gamme", "famille", "sous_famille", "categorie", "sous_categorie")):
        return 0
    if "categorie" in fields or "sous_categorie" in fields:
        _sync_mobile_refs(db, data.categorie, data.sous_categorie)
    products = db.query(Product).filter(Product.id.in_(data.product_ids)).all()
    found = {p.id: p for p in products}
    missing = [pid for pid in data.product_ids if pid not in found]
    if missing:
        raise BadRequestException(f"Products not found: {missing[:5]}")

    updated = 0
    for product_id in data.product_ids:
        product = found[product_id]
        if "gamme" in fields and data.gamme is not None:
            product.gamme = data.gamme
        if "famille" in fields and data.famille is not None:
            product.famille = data.famille
        if "sous_famille" in fields and data.sous_famille is not None:
            product.sous_famille = data.sous_famille
        _apply_mobile_category_updates(
            product,
            categorie=data.categorie,
            sous_categorie=data.sous_categorie,
            categorie_set="categorie" in fields,
            sous_categorie_set="sous_categorie" in fields,
        )
        updated += 1
    db.commit()
    return updated


def count_missing_mobile_category(db: Session) -> int:
    return (
        db.query(Product)
        .filter(or_(Product.categorie == None, Product.categorie == ""))
        .count()
    )


def list_uncategorized_products(db: Session) -> List[Product]:
    return (
        db.query(Product)
        .filter(or_(Product.categorie == None, Product.categorie == ""))
        .order_by(Product.product_code)
        .all()
    )


def uncategorized_products_csv(db: Session) -> str:
    import csv
    import io

    rows = list_uncategorized_products(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "product_code", "name", "gamme", "famille", "sous_famille",
        "synced_from_intermediate", "is_active", "base_price",
    ])
    for p in rows:
        writer.writerow([
            p.product_code,
            p.name,
            p.gamme or "",
            p.famille or "",
            p.sous_famille or "",
            "oui" if p.synced_from_intermediate else "non",
            "oui" if p.is_active else "non",
            float(p.base_price) if p.base_price is not None else "",
        ])
    return buf.getvalue()


def distinct_values(db: Session, column) -> List[str]:
    rows = db.query(column).distinct().filter(column != None, column != "").all()
    return sorted({r[0].strip() for r in rows if r[0] and str(r[0]).strip()}, key=str.casefold)


# ── ETL sync ──────────────────────────────────────────────────────────────────

def sync_bulk_products(db: Session, items: List[ProductSyncItem]) -> dict:
    """
    CDC §7.4 rules:
    - New product   → full insert
    - Existing      → update price + discount + is_active only (not name/description/catalogue)
    - Both          → mark synced_from_intermediate = True
    """
    created = updated = 0
    for item in items:
        existing = get_product_by_code(db, item.product_code)
        if existing:
            # Price-only update per CDC (catalogue fields are managed manually in back-office)
            existing.base_price = item.base_price
            existing.discount_rate = item.discount_rate
            # CDC §3.2: a product stays inactive until a mobile category is assigned
            # in the back-office — even if Assabil marks it available (HOLD=0).
            existing.is_active = item.is_active and existing.categorie is not None
            existing.synced_from_intermediate = True
            updated += 1
        else:
            data = item.model_dump()
            # New synced products have no mobile category yet → inactive until the
            # back-office assigns one (CDC §3.2).
            data["is_active"] = False
            product = Product(**data)
            db.add(product)
            created += 1
    db.commit()
    return {"created": created, "updated": updated}


def deactivate_products_without_price(db: Session) -> int:
    """Auto-deactivate products with no base price."""
    result = (
        db.query(Product)
        .filter(Product.base_price == None, Product.is_active == True)
        .update({"is_active": False})
    )
    db.commit()
    return result
