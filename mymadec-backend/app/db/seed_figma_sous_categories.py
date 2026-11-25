"""Insert Figma sous-categories under existing CTGS categories (no category reset)."""
from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.figma_sous_categories_data import FIGMA_SOUS_CATEGORIES, resolve_ctgs_category_name
from app.models.catalog import CatalogCategorie, CatalogSousCategorie

logger = logging.getLogger("mymadec.seed_figma_sous")


def seed_figma_sous_categories(db: Session) -> dict[str, int]:
    """
    Keep existing catalog_categories (CTGS).
    DELETE + INSERT catalog_sous_categories from Figma (73 rows), mapped to CTGS parents.
    """
    cats_by_name = {c.name.lower(): c for c in db.query(CatalogCategorie).all()}
    if not cats_by_name:
        raise RuntimeError("No catalog_categories in DB — run seed_ctgs_categories first")

    deleted = db.query(CatalogSousCategorie).delete(synchronize_session=False)
    db.flush()

    inserted = 0
    skipped = 0
    per_cat: dict[str, int] = {}

    # Recompute sort_order per target category
    buckets: dict[str, list[tuple[str, int]]] = {}
    for figma_parent_id, name, _old_order in FIGMA_SOUS_CATEGORIES:
        target = resolve_ctgs_category_name(name, figma_parent_id)
        buckets.setdefault(target, []).append((name, _old_order))

    for target_name, items in buckets.items():
        cat = cats_by_name.get(target_name.lower())
        if not cat:
            logger.warning("CTGS category not found, skip %s (%s sous-cats)", target_name, len(items))
            skipped += len(items)
            continue
        for sort_order, (name, _) in enumerate(sorted(items, key=lambda x: x[1])):
            exists = (
                db.query(CatalogSousCategorie)
                .filter(
                    CatalogSousCategorie.categorie_id == cat.id,
                    func.lower(CatalogSousCategorie.name) == name.lower(),
                )
                .first()
            )
            if exists:
                skipped += 1
                continue
            db.add(
                CatalogSousCategorie(
                    categorie_id=cat.id,
                    name=name,
                    sort_order=sort_order,
                    is_active=True,
                )
            )
            inserted += 1
            per_cat[target_name] = per_cat.get(target_name, 0) + 1
            logger.info("Sous-cat %r -> %r (id=%s)", name, target_name, cat.id)

    db.commit()

    return {
        "sous_categories_deleted": deleted,
        "sous_categories_inserted": inserted,
        "sous_categories_skipped": skipped,
        "by_category": per_cat,
    }
