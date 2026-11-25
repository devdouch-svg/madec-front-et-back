"""Load Figma product catalog (CSV + images) and map to CTGS categories."""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
from pathlib import Path

from app.db.figma_sous_categories_data import resolve_ctgs_category_name
from app.db.product_pricing import pricing_row_score

_SAFE = re.compile(r"^[\w.\-]+$")

OLD_FIGMA_CAT_TO_PARENT: dict[str, int] = {
    "Biscuiterie": 7,
    "Boissons chaudes": 2,
    "Chocolats": 7,
    "Confiserie": 7,
    "CREMERIE": 6,
    "Crémerie": 6,
    "Epicerie": 7,
    "GRETA": 7,
    "Sauces et condiments": 9,
}

INVALID_SOUS = {
    "frame 1171275037",
    "ajouter une nouvelle carte",
    "greta",
    "cremerie",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_catalog_csv() -> Path:
    if env := os.getenv("MADEC_CATALOG_CSV", "").strip():
        return Path(env)
    return repo_root() / "my-madic-catalog.csv"


def default_product_images_dir() -> Path:
    if env := os.getenv("PRODUCT_IMAGES_DIR", "").strip():
        return Path(env)
    return repo_root() / "product-images"


def safe_code(name: str) -> str:
    code = re.sub(r"[^\w.\-]", "-", name.strip())
    code = re.sub(r"-+", "-", code).strip("-")
    return code[:100] or "produit"


def sql_safe_code(name: str) -> str | None:
    code = safe_code(name)
    return code if _SAFE.fullmatch(code) else None


def map_product_to_ctgs(old_categorie: str, sous_categorie: str | None, product_name: str) -> str:
    old = (old_categorie or "Epicerie").strip()
    if old in ("Biscuiterie", "Chocolats", "Confiserie"):
        return "Biscuiterie, Confiserie & Snacks"

    parent = OLD_FIGMA_CAT_TO_PARENT.get(old, 7)
    sous = (sous_categorie or "").strip()
    if sous.lower() in INVALID_SOUS:
        sous = ""
    label = sous or old or product_name
    return resolve_ctgs_category_name(label, parent)


def row_score(row: dict[str, str]) -> int:
    score = pricing_row_score(row)
    if row.get("image_path", "").strip():
        score += 4
    if row.get("sous_categorie", "").strip():
        score += 2
    if row.get("marque", "").strip():
        score += 1
    return score


def pick_products(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    picked: dict[str, dict[str, str]] = {}
    scores: dict[str, int] = {}
    for row in rows:
        name = row.get("produit", "").strip()
        if not name:
            continue
        key = name.upper()
        s = row_score(row)
        if key not in picked or s > scores[key]:
            picked[key] = row
            scores[key] = s
    return picked


def load_image_index(images_dir: Path, uploads_dir: Path) -> dict[str, str]:
    """product name (upper) -> /uploads/products/{code}.ext"""
    by_product: dict[str, str] = {}
    index_path = images_dir / "index.json"
    if index_path.exists():
        for row in json.loads(index_path.read_text(encoding="utf-8")):
            produit = row.get("produit", "").strip()
            fichier = row.get("fichier", "")
            if not produit or not fichier:
                continue
            code = safe_code(produit)
            ext = Path(fichier).suffix.lower() or ".png"
            src = images_dir / fichier
            if _SAFE.fullmatch(code) and src.is_file():
                by_product[produit.upper()] = (code, ext, src)

    if images_dir.is_dir():
        for path in images_dir.iterdir():
            if not path.is_file() or path.name == "index.json":
                continue
            stem = path.stem
            by_product.setdefault(stem.upper(), (path.stem, path.suffix.lower(), path))
    return by_product


def copy_product_images(
    images_dir: Path,
    uploads_dir: Path,
) -> tuple[dict[str, str], int]:
    """
    Copy images to uploads/products/.
    Returns (name_upper -> image_path, copied_count).
    """
    uploads_dir.mkdir(parents=True, exist_ok=True)
    raw = load_image_index(images_dir, uploads_dir)
    paths: dict[str, str] = {}
    copied = 0

    for name_upper, (code, ext, src) in raw.items():
        if not _SAFE.fullmatch(code):
            continue
        dest = uploads_dir / f"{code}{ext}"
        if not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime:
            shutil.copy2(src, dest)
            copied += 1
        paths[name_upper] = f"/uploads/products/{code}{ext}"

    return paths, copied


def image_path_for(name: str, by_product: dict[str, str], uploads_dir: Path) -> str | None:
    key = name.strip().upper()
    if key in by_product:
        return by_product[key]

    code = safe_code(name)
    if not _SAFE.fullmatch(code):
        return None
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        if (uploads_dir / f"{code}{ext}").is_file():
            return f"/uploads/products/{code}{ext}"
    return None


def load_catalog_rows(catalog_csv: Path) -> list[dict[str, str]]:
    text = catalog_csv.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))
