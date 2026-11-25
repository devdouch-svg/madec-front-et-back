"""Reset mobile catalog categories from ctgs/*.png (sous-cat then cat, with images)."""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.catalog import CatalogCategorie, CatalogSousCategorie

logger = logging.getLogger("mymadec.seed_ctgs")

LABELS: dict[str, str] = {
    "biscuiterie_confiserie_snacks": "Biscuiterie, Confiserie & Snacks",
    "boulangerie": "Boulangerie",
    "charcuterie": "Charcuterie",
    "entretien_nettoyage": "Entretien & Nettoyage",
    "epicerie": "Epicerie",
    "fromagerie_cremerie": "Fromagerie & Crémerie",
    "hygiene_beaute": "Hygiène & Beauté",
    "liquidations": "Liquidations",
    "monde_du_bebe": "Monde du Bébé",
    "petit_dejeuner": "Petit déjeuner",
    "poissonnerie": "Poissonnerie",
    "promotions": "Promotions",
}


def default_ctgs_dir() -> Path:
    if env := os.getenv("CTGS_DIR", "").strip():
        return Path(env)
    # repo layout: Mymadic/ctgs next to my-madec-backend-test/
    return Path(__file__).resolve().parents[3] / "ctgs"


def title_from_stem(stem: str) -> str:
    if stem in LABELS:
        return LABELS[stem]
    return " ".join(w.capitalize() for w in stem.replace("_", " ").split())


def seed_ctgs_categories(db: Session, *, ctgs_dir: Path | None = None) -> dict[str, int]:
    """
    1) DELETE sous-categories
    2) DELETE categories
    3) COPY ctgs/*.png -> uploads/categories/
    4) INSERT catalog_categories with image_path
    """
    src = (ctgs_dir or default_ctgs_dir()).resolve()
    if not src.is_dir():
        raise FileNotFoundError(f"CTGS directory not found: {src}")

    png_files = sorted(src.glob("*.png"))
    if not png_files:
        raise FileNotFoundError(f"No PNG files in {src}")

    upload_dir = Path(settings.UPLOAD_DIR) / "categories"
    upload_dir.mkdir(parents=True, exist_ok=True)

    sous_deleted = db.query(CatalogSousCategorie).delete(synchronize_session=False)
    cats_deleted = db.query(CatalogCategorie).delete(synchronize_session=False)
    db.flush()

    copied = 0
    inserted = 0
    for i, png in enumerate(png_files):
        dest = upload_dir / png.name
        shutil.copy2(png, dest)
        copied += 1

        image_path = f"/uploads/categories/{png.name}"
        db.add(
            CatalogCategorie(
                name=title_from_stem(png.stem),
                sort_order=i,
                is_active=True,
                image_path=image_path,
            )
        )
        inserted += 1
        logger.info("Category %s -> %s", title_from_stem(png.stem), image_path)

    db.commit()

    return {
        "sous_categories_deleted": sous_deleted,
        "categories_deleted": cats_deleted,
        "images_copied": copied,
        "categories_inserted": inserted,
        "upload_dir": str(upload_dir),
        "source_dir": str(src),
    }
