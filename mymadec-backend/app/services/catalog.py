from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictException, NotFoundException
from app.models.catalog import (
    CatalogCategorie,
    CatalogFamille,
    CatalogGamme,
    CatalogSousCategorie,
    CatalogSousFamille,
    CatalogType,
    OrgAgence,
    OrgSociete,
    OrgVille,
)
from app.models.product import Product
from app.models.user import User
from app.schemas.catalog import (
    CatalogCategorieCreate,
    CatalogCategorieUpdate,
    CatalogFamilleCreate,
    CatalogFamilleUpdate,
    CatalogGammeCreate,
    CatalogGammeUpdate,
    CatalogImportResult,
    CatalogSousCategorieCreate,
    CatalogSousCategorieUpdate,
    CatalogSousFamilleCreate,
    CatalogSousFamilleUpdate,
    CatalogTypeCreate,
    CatalogTypeUpdate,
    OrgAgenceCreate,
    OrgAgenceUpdate,
    OrgSocieteCreate,
    OrgSocieteUpdate,
    OrgVilleCreate,
    OrgVilleUpdate,
)


def _active_filter(q, model, include_inactive: bool):
    if not include_inactive:
        q = q.filter(model.is_active == True)
    return q


# ── Gammes ────────────────────────────────────────────────────────────────────

def list_gammes(db: Session, *, include_inactive: bool = False) -> List[CatalogGamme]:
    q = _active_filter(db.query(CatalogGamme), CatalogGamme, include_inactive)
    return q.order_by(CatalogGamme.sort_order, CatalogGamme.name).all()


def create_gamme(db: Session, data: CatalogGammeCreate) -> CatalogGamme:
    name = data.name.strip()
    if db.query(CatalogGamme).filter(func.lower(CatalogGamme.name) == name.lower()).first():
        raise ConflictException(f"Gamme {name!r} already exists")
    row = CatalogGamme(name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_gamme(db: Session, gamme_id: int, data: CatalogGammeUpdate) -> CatalogGamme:
    row = db.get(CatalogGamme, gamme_id)
    if not row:
        raise NotFoundException(f"Gamme {gamme_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogGamme)
            .filter(func.lower(CatalogGamme.name) == name.lower(), CatalogGamme.id != gamme_id)
            .first()
        )
        if clash:
            raise ConflictException(f"Gamme {name!r} already exists")
        row.name = name
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Familles ──────────────────────────────────────────────────────────────────

def list_familles(
    db: Session, *, gamme_id: Optional[int] = None, include_inactive: bool = False
) -> List[CatalogFamille]:
    q = db.query(CatalogFamille).options(joinedload(CatalogFamille.gamme))
    q = _active_filter(q, CatalogFamille, include_inactive)
    if gamme_id is not None:
        q = q.filter(CatalogFamille.gamme_id == gamme_id)
    return q.order_by(CatalogFamille.sort_order, CatalogFamille.name).all()


def create_famille(db: Session, data: CatalogFamilleCreate) -> CatalogFamille:
    if not db.get(CatalogGamme, data.gamme_id):
        raise NotFoundException(f"Gamme {data.gamme_id} not found")
    name = data.name.strip()
    existing = (
        db.query(CatalogFamille)
        .filter(CatalogFamille.gamme_id == data.gamme_id, func.lower(CatalogFamille.name) == name.lower())
        .first()
    )
    if existing:
        raise ConflictException(f"Famille {name!r} already exists for this gamme")
    row = CatalogFamille(gamme_id=data.gamme_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_famille(db: Session, famille_id: int, data: CatalogFamilleUpdate) -> CatalogFamille:
    row = db.get(CatalogFamille, famille_id)
    if not row:
        raise NotFoundException(f"Famille {famille_id} not found")
    gamme_id = data.gamme_id if data.gamme_id is not None else row.gamme_id
    if data.gamme_id is not None and not db.get(CatalogGamme, data.gamme_id):
        raise NotFoundException(f"Gamme {data.gamme_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogFamille)
            .filter(
                CatalogFamille.gamme_id == gamme_id,
                func.lower(CatalogFamille.name) == name.lower(),
                CatalogFamille.id != famille_id,
            )
            .first()
        )
        if clash:
            raise ConflictException(f"Famille {name!r} already exists for this gamme")
        row.name = name
    if data.gamme_id is not None:
        row.gamme_id = data.gamme_id
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Sous-familles ─────────────────────────────────────────────────────────────

def list_sous_familles(
    db: Session, *, famille_id: Optional[int] = None, include_inactive: bool = False
) -> List[CatalogSousFamille]:
    q = (
        db.query(CatalogSousFamille)
        .options(joinedload(CatalogSousFamille.famille).joinedload(CatalogFamille.gamme))
    )
    q = _active_filter(q, CatalogSousFamille, include_inactive)
    if famille_id is not None:
        q = q.filter(CatalogSousFamille.famille_id == famille_id)
    return q.order_by(CatalogSousFamille.sort_order, CatalogSousFamille.name).all()


def create_sous_famille(db: Session, data: CatalogSousFamilleCreate) -> CatalogSousFamille:
    if not db.get(CatalogFamille, data.famille_id):
        raise NotFoundException(f"Famille {data.famille_id} not found")
    name = data.name.strip()
    existing = (
        db.query(CatalogSousFamille)
        .filter(
            CatalogSousFamille.famille_id == data.famille_id,
            func.lower(CatalogSousFamille.name) == name.lower(),
        )
        .first()
    )
    if existing:
        raise ConflictException(f"Sous-famille {name!r} already exists for this famille")
    row = CatalogSousFamille(famille_id=data.famille_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_sous_famille(db: Session, sous_famille_id: int, data: CatalogSousFamilleUpdate) -> CatalogSousFamille:
    row = db.get(CatalogSousFamille, sous_famille_id)
    if not row:
        raise NotFoundException(f"Sous-famille {sous_famille_id} not found")
    famille_id = data.famille_id if data.famille_id is not None else row.famille_id
    if data.famille_id is not None and not db.get(CatalogFamille, data.famille_id):
        raise NotFoundException(f"Famille {data.famille_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogSousFamille)
            .filter(
                CatalogSousFamille.famille_id == famille_id,
                func.lower(CatalogSousFamille.name) == name.lower(),
                CatalogSousFamille.id != sous_famille_id,
            )
            .first()
        )
        if clash:
            raise ConflictException(f"Sous-famille {name!r} already exists for this famille")
        row.name = name
    if data.famille_id is not None:
        row.famille_id = data.famille_id
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Catégories (mobile app) ─────────────────────────────────────────────────

def list_categories(db: Session, *, include_inactive: bool = False) -> List[CatalogCategorie]:
    q = _active_filter(db.query(CatalogCategorie), CatalogCategorie, include_inactive)
    return q.order_by(CatalogCategorie.sort_order, CatalogCategorie.name).all()


def create_categorie(db: Session, data: CatalogCategorieCreate) -> CatalogCategorie:
    name = data.name.strip()
    if db.query(CatalogCategorie).filter(func.lower(CatalogCategorie.name) == name.lower()).first():
        raise ConflictException(f"Catégorie {name!r} already exists")
    row = CatalogCategorie(name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_categorie(db: Session, categorie_id: int, data: CatalogCategorieUpdate) -> CatalogCategorie:
    row = db.get(CatalogCategorie, categorie_id)
    if not row:
        raise NotFoundException(f"Catégorie {categorie_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogCategorie)
            .filter(func.lower(CatalogCategorie.name) == name.lower(), CatalogCategorie.id != categorie_id)
            .first()
        )
        if clash:
            raise ConflictException(f"Catégorie {name!r} already exists")
        old_name = row.name
        row.name = name
        if old_name != name:
            db.query(Product).filter(Product.categorie == old_name).update(
                {"categorie": name}, synchronize_session=False
            )
    if data.is_active is not None:
        row.is_active = data.is_active
        if data.is_active is False:
            db.query(CatalogSousCategorie).filter(
                CatalogSousCategorie.categorie_id == categorie_id,
                CatalogSousCategorie.is_active == True,  # noqa: E712
            ).update({"is_active": False}, synchronize_session=False)
        else:
            db.query(CatalogSousCategorie).filter(
                CatalogSousCategorie.categorie_id == categorie_id,
            ).update({"is_active": True}, synchronize_session=False)
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


def list_sous_categories(
    db: Session, *, categorie_id: Optional[int] = None, include_inactive: bool = False
) -> List[CatalogSousCategorie]:
    q = db.query(CatalogSousCategorie).options(joinedload(CatalogSousCategorie.categorie))
    q = _active_filter(q, CatalogSousCategorie, include_inactive)
    if categorie_id is not None:
        q = q.filter(CatalogSousCategorie.categorie_id == categorie_id)
    return q.order_by(CatalogSousCategorie.sort_order, CatalogSousCategorie.name).all()


def create_sous_categorie(db: Session, data: CatalogSousCategorieCreate) -> CatalogSousCategorie:
    if not db.get(CatalogCategorie, data.categorie_id):
        raise NotFoundException(f"Catégorie {data.categorie_id} not found")
    name = data.name.strip()
    existing = (
        db.query(CatalogSousCategorie)
        .filter(
            CatalogSousCategorie.categorie_id == data.categorie_id,
            func.lower(CatalogSousCategorie.name) == name.lower(),
        )
        .first()
    )
    if existing:
        raise ConflictException(f"Sous-catégorie {name!r} already exists for this catégorie")
    row = CatalogSousCategorie(categorie_id=data.categorie_id, name=name)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_sous_categorie(
    db: Session, sous_categorie_id: int, data: CatalogSousCategorieUpdate
) -> CatalogSousCategorie:
    row = db.get(CatalogSousCategorie, sous_categorie_id)
    if not row:
        raise NotFoundException(f"Sous-catégorie {sous_categorie_id} not found")
    categorie_id = data.categorie_id if data.categorie_id is not None else row.categorie_id
    if data.categorie_id is not None and not db.get(CatalogCategorie, data.categorie_id):
        raise NotFoundException(f"Catégorie {data.categorie_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogSousCategorie)
            .filter(
                CatalogSousCategorie.categorie_id == categorie_id,
                func.lower(CatalogSousCategorie.name) == name.lower(),
                CatalogSousCategorie.id != sous_categorie_id,
            )
            .first()
        )
        if clash:
            raise ConflictException(f"Sous-catégorie {name!r} already exists for this catégorie")
        old_name = row.name
        cat_name = row.categorie.name if row.categorie else None
        if cat_name is None:
            cat = db.get(CatalogCategorie, row.categorie_id)
            cat_name = cat.name if cat else None
        row.name = name
        if old_name != name and cat_name:
            db.query(Product).filter(
                Product.categorie == cat_name,
                Product.sous_categorie == old_name,
            ).update({"sous_categorie": name}, synchronize_session=False)
    if data.categorie_id is not None:
        row.categorie_id = data.categorie_id
    if data.is_active is not None:
        row.is_active = data.is_active
        type_q = db.query(CatalogType).filter(CatalogType.sous_categorie_id == sous_categorie_id)
        if data.is_active is False:
            type_q.update({"is_active": False}, synchronize_session=False)
        else:
            type_q.update({"is_active": True}, synchronize_session=False)
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


def list_types(
    db: Session, *, sous_categorie_id: Optional[int] = None, include_inactive: bool = False
) -> List[CatalogType]:
    if sous_categorie_id is not None:
        _ensure_types_from_products(db, sous_categorie_id)
    q = (
        db.query(CatalogType)
        .options(joinedload(CatalogType.sous_categorie).joinedload(CatalogSousCategorie.categorie))
    )
    q = _active_filter(q, CatalogType, include_inactive)
    if sous_categorie_id is not None:
        q = q.filter(CatalogType.sous_categorie_id == sous_categorie_id)
    return q.order_by(CatalogType.sort_order, CatalogType.name).all()


def create_type(db: Session, data: CatalogTypeCreate) -> CatalogType:
    if not db.get(CatalogSousCategorie, data.sous_categorie_id):
        raise NotFoundException(f"Sous-catégorie {data.sous_categorie_id} not found")
    name = data.name.strip()
    existing = (
        db.query(CatalogType)
        .filter(
            CatalogType.sous_categorie_id == data.sous_categorie_id,
            func.lower(CatalogType.name) == name.lower(),
        )
        .first()
    )
    if existing:
        raise ConflictException(f"Type {name!r} already exists for this sous-catégorie")
    max_order = (
        db.query(func.coalesce(func.max(CatalogType.sort_order), 0))
        .filter(CatalogType.sous_categorie_id == data.sous_categorie_id)
        .scalar()
        or 0
    )
    row = CatalogType(sous_categorie_id=data.sous_categorie_id, name=name, sort_order=max_order + 10)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_type(db: Session, type_id: int, data: CatalogTypeUpdate) -> CatalogType:
    row = db.get(CatalogType, type_id)
    if not row:
        raise NotFoundException(f"Type {type_id} not found")
    sous_categorie_id = data.sous_categorie_id if data.sous_categorie_id is not None else row.sous_categorie_id
    if data.sous_categorie_id is not None and not db.get(CatalogSousCategorie, data.sous_categorie_id):
        raise NotFoundException(f"Sous-catégorie {data.sous_categorie_id} not found")
    if data.name is not None:
        name = data.name.strip()
        clash = (
            db.query(CatalogType)
            .filter(
                CatalogType.sous_categorie_id == sous_categorie_id,
                func.lower(CatalogType.name) == name.lower(),
                CatalogType.id != type_id,
            )
            .first()
        )
        if clash:
            raise ConflictException(f"Type {name!r} already exists for this sous-catégorie")
        old_name = row.name
        sc = row.sous_categorie or db.get(CatalogSousCategorie, row.sous_categorie_id)
        cat_name = sc.categorie.name if sc and sc.categorie else None
        if sc and cat_name is None:
            cat = db.get(CatalogCategorie, sc.categorie_id)
            cat_name = cat.name if cat else None
        sc_name = sc.name if sc else None
        row.name = name
        if old_name != name and cat_name and sc_name:
            db.query(Product).filter(
                Product.categorie == cat_name,
                Product.sous_categorie == sc_name,
                Product.type_produit == old_name,
            ).update({"type_produit": name}, synchronize_session=False)
    if data.sous_categorie_id is not None:
        row.sous_categorie_id = data.sous_categorie_id
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


def _apply_sort_order(rows_by_id: dict[int, object], ids: list[int]) -> int:
    for index, row_id in enumerate(ids):
        row = rows_by_id[row_id]
        row.sort_order = (index + 1) * 10
    return len(ids)


def reorder_categories(db: Session, ids: list[int]) -> int:
    rows = db.query(CatalogCategorie).filter(CatalogCategorie.id.in_(ids)).all()
    if len(rows) != len(ids):
        raise NotFoundException("Une ou plusieurs catégories sont introuvables")
    updated = _apply_sort_order({r.id: r for r in rows}, ids)
    db.commit()
    return updated


def reorder_sous_categories(db: Session, ids: list[int], *, categorie_id: int) -> int:
    rows = (
        db.query(CatalogSousCategorie)
        .filter(CatalogSousCategorie.id.in_(ids), CatalogSousCategorie.categorie_id == categorie_id)
        .all()
    )
    if len(rows) != len(ids):
        raise NotFoundException("Les sous-catégories doivent appartenir à la catégorie sélectionnée")
    updated = _apply_sort_order({r.id: r for r in rows}, ids)
    db.commit()
    return updated


def reorder_types(db: Session, ids: list[int], *, sous_categorie_id: int) -> int:
    rows = (
        db.query(CatalogType)
        .filter(CatalogType.id.in_(ids), CatalogType.sous_categorie_id == sous_categorie_id)
        .all()
    )
    if len(rows) != len(ids):
        raise NotFoundException("Les types doivent appartenir à la sous-catégorie sélectionnée")
    updated = _apply_sort_order({r.id: r for r in rows}, ids)
    db.commit()
    return updated


def reorder_products(db: Session, ids: list[int]) -> int:
    rows = db.query(Product).filter(Product.id.in_(ids)).all()
    if len(rows) != len(ids):
        raise NotFoundException("Un ou plusieurs produits sont introuvables")
    updated = _apply_sort_order({r.id: r for r in rows}, ids)
    db.commit()
    return updated


def _ensure_types_from_products(db: Session, sous_categorie_id: int) -> None:
    sc = (
        db.query(CatalogSousCategorie)
        .options(joinedload(CatalogSousCategorie.categorie))
        .filter(CatalogSousCategorie.id == sous_categorie_id)
        .first()
    )
    if not sc or not sc.categorie:
        return
    labels = [
        name.strip()
        for (name,) in (
            db.query(Product.type_produit)
            .filter(
                Product.categorie == sc.categorie.name,
                Product.sous_categorie == sc.name,
                Product.type_produit != None,  # noqa: E711
                Product.type_produit != "",
            )
            .distinct()
            .all()
        )
        if name and name.strip()
    ]
    if not labels:
        return
    existing = {
        t.name.lower()
        for t in db.query(CatalogType).filter(CatalogType.sous_categorie_id == sous_categorie_id).all()
    }
    max_order = (
        db.query(func.coalesce(func.max(CatalogType.sort_order), 0))
        .filter(CatalogType.sous_categorie_id == sous_categorie_id)
        .scalar()
        or 0
    )
    added = False
    for name in labels:
        if name.lower() in existing:
            continue
        max_order += 10
        db.add(CatalogType(sous_categorie_id=sous_categorie_id, name=name, sort_order=max_order))
        existing.add(name.lower())
        added = True
    if added:
        db.commit()


def type_product_counts(db: Session, *, categorie_name: str, sous_categorie_name: str) -> dict[str, int]:
    return {
        (name or ""): count
        for name, count in (
            db.query(Product.type_produit, func.count(Product.id))
            .filter(
                Product.categorie == categorie_name,
                Product.sous_categorie == sous_categorie_name,
                Product.type_produit != None,  # noqa: E711
                Product.type_produit != "",
            )
            .group_by(Product.type_produit)
            .all()
        )
    }


def ensure_mobile_catalog_refs(
    db: Session,
    categorie: Optional[str],
    sous_categorie: Optional[str],
    type_produit: Optional[str] = None,
) -> None:
    """Ensure product mobile labels exist in referential tables (idempotent upsert)."""
    cat_name = (categorie or "").strip()
    sc_name = (sous_categorie or "").strip()
    if not cat_name:
        return
    cat_row = (
        db.query(CatalogCategorie)
        .filter(func.lower(CatalogCategorie.name) == cat_name.lower())
        .first()
    )
    if not cat_row:
        cat_row = CatalogCategorie(name=cat_name)
        db.add(cat_row)
        db.flush()
    if not sc_name:
        return
    existing = (
        db.query(CatalogSousCategorie)
        .filter(
            CatalogSousCategorie.categorie_id == cat_row.id,
            func.lower(CatalogSousCategorie.name) == sc_name.lower(),
        )
        .first()
    )
    if not existing:
        existing = CatalogSousCategorie(categorie_id=cat_row.id, name=sc_name)
        db.add(existing)
        db.flush()
    type_name = (type_produit or "").strip()
    if not type_name:
        return
    type_row = (
        db.query(CatalogType)
        .filter(
            CatalogType.sous_categorie_id == existing.id,
            func.lower(CatalogType.name) == type_name.lower(),
        )
        .first()
    )
    if not type_row:
        db.add(CatalogType(sous_categorie_id=existing.id, name=type_name))
        db.flush()


def get_categories_tree(db: Session, *, include_inactive: bool = False) -> list[dict]:
    """Nested catégories + sous-catégories with live product counts (mobile browse)."""
    cat_counts = {
        name: count
        for name, count in (
            db.query(Product.categorie, func.count(Product.id))
            .filter(Product.categorie != None, Product.categorie != "")
            .group_by(Product.categorie)
            .all()
        )
    }
    sc_counts = {
        (cat, sc): count
        for cat, sc, count in (
            db.query(Product.categorie, Product.sous_categorie, func.count(Product.id))
            .filter(
                Product.categorie != None,
                Product.categorie != "",
                Product.sous_categorie != None,
                Product.sous_categorie != "",
            )
            .group_by(Product.categorie, Product.sous_categorie)
            .all()
        )
    }

    type_counts = {
        (cat, sc, tp): count
        for cat, sc, tp, count in (
            db.query(Product.categorie, Product.sous_categorie, Product.type_produit, func.count(Product.id))
            .filter(
                Product.categorie != None,
                Product.categorie != "",
                Product.sous_categorie != None,
                Product.sous_categorie != "",
                Product.type_produit != None,
                Product.type_produit != "",
            )
            .group_by(Product.categorie, Product.sous_categorie, Product.type_produit)
            .all()
        )
    }

    all_sous = list_sous_categories(db, include_inactive=include_inactive)
    sous_by_cat: dict[int, list] = {}
    for sc in all_sous:
        sous_by_cat.setdefault(sc.categorie_id, []).append(sc)

    all_types = list_types(db, include_inactive=include_inactive)
    types_by_sc: dict[int, list] = {}
    for tp in all_types:
        types_by_sc.setdefault(tp.sous_categorie_id, []).append(tp)

    tree: list[dict] = []
    for cat in list_categories(db, include_inactive=include_inactive):
        sous = sous_by_cat.get(cat.id, [])
        tree.append(
            {
                "id": cat.id,
                "name": cat.name,
                "is_active": cat.is_active,
                "sort_order": cat.sort_order,
                "image_path": cat.image_path,
                "updated_at": cat.updated_at,
                "product_count": cat_counts.get(cat.name, 0),
                "sous_categories": [
                    {
                        "id": sc.id,
                        "name": sc.name,
                        "is_active": sc.is_active,
                        "sort_order": sc.sort_order,
                        "product_count": sc_counts.get((cat.name, sc.name), 0),
                        "types": [
                            {
                                "id": tp.id,
                                "name": tp.name,
                                "is_active": tp.is_active,
                                "sort_order": tp.sort_order,
                                "product_count": type_counts.get((cat.name, sc.name, tp.name), 0),
                            }
                            for tp in types_by_sc.get(sc.id, [])
                        ],
                    }
                    for sc in sous
                ],
            }
        )
    return tree


# ── Sociétés ──────────────────────────────────────────────────────────────────

def list_societes(db: Session, *, include_inactive: bool = False) -> List[OrgSociete]:
    q = _active_filter(db.query(OrgSociete), OrgSociete, include_inactive)
    return q.order_by(OrgSociete.sort_order, OrgSociete.label).all()


def create_societe(db: Session, data: OrgSocieteCreate) -> OrgSociete:
    code = data.code.strip()
    if db.query(OrgSociete).filter(func.lower(OrgSociete.code) == code.lower()).first():
        raise ConflictException(f"Société {code!r} already exists")
    row = OrgSociete(code=code, label=data.label.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_societe(db: Session, societe_id: int, data: OrgSocieteUpdate) -> OrgSociete:
    row = db.get(OrgSociete, societe_id)
    if not row:
        raise NotFoundException(f"Société {societe_id} not found")
    if data.code is not None:
        code = data.code.strip()
        clash = (
            db.query(OrgSociete)
            .filter(func.lower(OrgSociete.code) == code.lower(), OrgSociete.id != societe_id)
            .first()
        )
        if clash:
            raise ConflictException(f"Société {code!r} already exists")
        row.code = code
    if data.label is not None:
        row.label = data.label.strip()
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Agences ───────────────────────────────────────────────────────────────────

def list_agences(
    db: Session, *, societe_id: Optional[int] = None, include_inactive: bool = False
) -> List[OrgAgence]:
    q = db.query(OrgAgence).options(joinedload(OrgAgence.societe))
    q = _active_filter(q, OrgAgence, include_inactive)
    if societe_id is not None:
        q = q.filter(OrgAgence.societe_id == societe_id)
    return q.order_by(OrgAgence.sort_order, OrgAgence.label).all()


def create_agence(db: Session, data: OrgAgenceCreate) -> OrgAgence:
    if not db.get(OrgSociete, data.societe_id):
        raise NotFoundException(f"Société {data.societe_id} not found")
    code = data.code.strip()
    existing = (
        db.query(OrgAgence)
        .filter(OrgAgence.societe_id == data.societe_id, func.lower(OrgAgence.code) == code.lower())
        .first()
    )
    if existing:
        raise ConflictException(f"Agence {code!r} already exists for this société")
    row = OrgAgence(societe_id=data.societe_id, code=code, label=data.label.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_agence(db: Session, agence_id: int, data: OrgAgenceUpdate) -> OrgAgence:
    row = db.get(OrgAgence, agence_id)
    if not row:
        raise NotFoundException(f"Agence {agence_id} not found")
    societe_id = data.societe_id if data.societe_id is not None else row.societe_id
    if data.societe_id is not None and not db.get(OrgSociete, data.societe_id):
        raise NotFoundException(f"Société {data.societe_id} not found")
    if data.code is not None:
        code = data.code.strip()
        clash = (
            db.query(OrgAgence)
            .filter(
                OrgAgence.societe_id == societe_id,
                func.lower(OrgAgence.code) == code.lower(),
                OrgAgence.id != agence_id,
            )
            .first()
        )
        if clash:
            raise ConflictException(f"Agence {code!r} already exists for this société")
        row.code = code
    if data.label is not None:
        row.label = data.label.strip()
    if data.societe_id is not None:
        row.societe_id = data.societe_id
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Villes ────────────────────────────────────────────────────────────────────

def list_villes(db: Session, *, include_inactive: bool = False) -> List[OrgVille]:
    q = _active_filter(db.query(OrgVille), OrgVille, include_inactive)
    return q.order_by(OrgVille.sort_order, OrgVille.label).all()


def create_ville(db: Session, data: OrgVilleCreate) -> OrgVille:
    code = data.code.strip()
    if db.query(OrgVille).filter(func.lower(OrgVille.code) == code.lower()).first():
        raise ConflictException(f"Ville {code!r} already exists")
    row = OrgVille(code=code, label=data.label.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_ville(db: Session, ville_id: int, data: OrgVilleUpdate) -> OrgVille:
    row = db.get(OrgVille, ville_id)
    if not row:
        raise NotFoundException(f"Ville {ville_id} not found")
    if data.code is not None:
        code = data.code.strip()
        clash = (
            db.query(OrgVille)
            .filter(func.lower(OrgVille.code) == code.lower(), OrgVille.id != ville_id)
            .first()
        )
        if clash:
            raise ConflictException(f"Ville {code!r} already exists")
        row.code = code
    if data.label is not None:
        row.label = data.label.strip()
    if data.is_active is not None:
        row.is_active = data.is_active
    if data.sort_order is not None:
        row.sort_order = data.sort_order
    db.commit()
    db.refresh(row)
    return row


# ── Import from existing denormalized data ────────────────────────────────────

def import_from_existing_data(db: Session) -> CatalogImportResult:
    """Seed reference tables from distinct product/user values (idempotent)."""
    counts = dict(
        gammes=0, familles=0, sous_familles=0,
        categories=0, sous_categories=0, types=0,
        societes=0, agences=0, villes=0,
    )

    for name, in db.query(Product.gamme).distinct().filter(Product.gamme != None, Product.gamme != "").all():
        n = name.strip()
        if not n or db.query(CatalogGamme).filter(func.lower(CatalogGamme.name) == n.lower()).first():
            continue
        db.add(CatalogGamme(name=n))
        counts["gammes"] += 1

    db.flush()

    gamme_by_name = {g.name.lower(): g for g in db.query(CatalogGamme).all()}
    seen_familles: set[tuple[int, str]] = set()
    for gamme_name, famille_name in (
        db.query(Product.gamme, Product.famille)
        .distinct()
        .filter(Product.gamme != None, Product.famille != None)
        .all()
    ):
        g = gamme_by_name.get((gamme_name or "").strip().lower())
        f = (famille_name or "").strip()
        if not g or not f:
            continue
        key = (g.id, f.lower())
        if key in seen_familles:
            continue
        if db.query(CatalogFamille).filter(CatalogFamille.gamme_id == g.id, func.lower(CatalogFamille.name) == f.lower()).first():
            seen_familles.add(key)
            continue
        db.add(CatalogFamille(gamme_id=g.id, name=f))
        seen_familles.add(key)
        counts["familles"] += 1

    db.flush()

    famille_index: dict[tuple[str, str], CatalogFamille] = {}
    for fam in db.query(CatalogFamille).options(joinedload(CatalogFamille.gamme)).all():
        if fam.gamme:
            famille_index[(fam.gamme.name.lower(), fam.name.lower())] = fam

    seen_sf: set[tuple[int, str]] = set()
    for gamme_name, famille_name, sf_name in (
        db.query(Product.gamme, Product.famille, Product.sous_famille)
        .distinct()
        .filter(Product.sous_famille != None, Product.sous_famille != "")
        .all()
    ):
        fam = famille_index.get(((gamme_name or "").strip().lower(), (famille_name or "").strip().lower()))
        sf = (sf_name or "").strip()
        if not fam or not sf:
            continue
        key = (fam.id, sf.lower())
        if key in seen_sf:
            continue
        if db.query(CatalogSousFamille).filter(
            CatalogSousFamille.famille_id == fam.id, func.lower(CatalogSousFamille.name) == sf.lower()
        ).first():
            seen_sf.add(key)
            continue
        db.add(CatalogSousFamille(famille_id=fam.id, name=sf))
        seen_sf.add(key)
        counts["sous_familles"] += 1

    for name, in db.query(Product.categorie).distinct().filter(Product.categorie != None, Product.categorie != "").all():
        n = name.strip()
        if not n or db.query(CatalogCategorie).filter(func.lower(CatalogCategorie.name) == n.lower()).first():
            continue
        db.add(CatalogCategorie(name=n))
        counts["categories"] += 1

    db.flush()

    categorie_by_name = {c.name.lower(): c for c in db.query(CatalogCategorie).all()}
    seen_sc: set[tuple[int, str]] = set()
    for categorie_name, sc_name in (
        db.query(Product.categorie, Product.sous_categorie)
        .distinct()
        .filter(Product.sous_categorie != None, Product.sous_categorie != "")
        .all()
    ):
        cat = categorie_by_name.get((categorie_name or "").strip().lower())
        sc = (sc_name or "").strip()
        if not cat or not sc:
            continue
        key = (cat.id, sc.lower())
        if key in seen_sc:
            continue
        if db.query(CatalogSousCategorie).filter(
            CatalogSousCategorie.categorie_id == cat.id,
            func.lower(CatalogSousCategorie.name) == sc.lower(),
        ).first():
            seen_sc.add(key)
            continue
        db.add(CatalogSousCategorie(categorie_id=cat.id, name=sc))
        seen_sc.add(key)
        counts["sous_categories"] += 1

    db.flush()
    sc_index: dict[tuple[str, str], CatalogSousCategorie] = {}
    for sc_row in db.query(CatalogSousCategorie).options(joinedload(CatalogSousCategorie.categorie)).all():
        if sc_row.categorie:
            sc_index[(sc_row.categorie.name.lower(), sc_row.name.lower())] = sc_row
    seen_types: set[tuple[int, str]] = set()
    for categorie_name, sc_name, type_name in (
        db.query(Product.categorie, Product.sous_categorie, Product.type_produit)
        .distinct()
        .filter(Product.type_produit != None, Product.type_produit != "")
        .all()
    ):
        sc_row = sc_index.get(((categorie_name or "").strip().lower(), (sc_name or "").strip().lower()))
        tn = (type_name or "").strip()
        if not sc_row or not tn:
            continue
        key = (sc_row.id, tn.lower())
        if key in seen_types:
            continue
        if db.query(CatalogType).filter(
            CatalogType.sous_categorie_id == sc_row.id,
            func.lower(CatalogType.name) == tn.lower(),
        ).first():
            seen_types.add(key)
            continue
        db.add(CatalogType(sous_categorie_id=sc_row.id, name=tn))
        seen_types.add(key)
        counts["types"] += 1

    for code, in db.query(Product.society_code).distinct().filter(Product.society_code != None, Product.society_code != "").all():
        c = code.strip()
        if not c or db.query(OrgSociete).filter(func.lower(OrgSociete.code) == c.lower()).first():
            continue
        db.add(OrgSociete(code=c, label=c))
        counts["societes"] += 1

    for societe_name, in db.query(User.societe).distinct().filter(User.societe != None, User.societe != "").all():
        c = societe_name.strip()
        if not c or db.query(OrgSociete).filter(func.lower(OrgSociete.code) == c.lower()).first():
            continue
        db.add(OrgSociete(code=c, label=c))
        counts["societes"] += 1

    db.flush()

    societe_by_code = {s.code.lower(): s for s in db.query(OrgSociete).all()}
    seen_ag: set[tuple[int, str]] = set()
    for societe_name, agence_code in (
        db.query(User.societe, User.agence).distinct().filter(User.agence != None, User.agence != "").all()
    ):
        soc = societe_by_code.get((societe_name or "").strip().lower())
        code = (agence_code or "").strip()
        if not code:
            continue
        societe_id = soc.id if soc else None
        if societe_id is None:
            # orphan agence — attach to a generic société bucket
            generic = db.query(OrgSociete).filter(OrgSociete.code == "_DEFAULT").first()
            if not generic:
                generic = OrgSociete(code="_DEFAULT", label="Non rattaché")
                db.add(generic)
                db.flush()
                counts["societes"] += 1
                societe_by_code["_default"] = generic
            societe_id = generic.id
        key = (societe_id, code.lower())
        if key in seen_ag:
            continue
        if db.query(OrgAgence).filter(OrgAgence.societe_id == societe_id, func.lower(OrgAgence.code) == code.lower()).first():
            seen_ag.add(key)
            continue
        db.add(OrgAgence(societe_id=societe_id, code=code, label=code))
        seen_ag.add(key)
        counts["agences"] += 1

    if hasattr(User, "ville"):
        for ville_name, in db.query(User.ville).distinct().filter(User.ville != None, User.ville != "").all():
            c = ville_name.strip()
            if not c or db.query(OrgVille).filter(func.lower(OrgVille.code) == c.lower()).first():
                continue
            db.add(OrgVille(code=c, label=c))
            counts["villes"] += 1

    db.commit()
    return CatalogImportResult(**counts)
