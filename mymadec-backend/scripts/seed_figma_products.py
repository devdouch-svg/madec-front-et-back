"""Reset products + import Figma catalog (images, CTGS categories, sous-categories).

Prerequis:
    python -m scripts.seed_ctgs_categories
    python -m scripts.seed_figma_sous_categories

Usage:
    python -m scripts.seed_figma_products
    python -m scripts.seed_figma_products --no-copy-images

Docker:
    docker exec backend-api-1 python -m scripts.seed_figma_products
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.db.seed_figma_products import seed_figma_products
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete products + import Figma catalog with CTGS mapping")
    parser.add_argument("--catalog-csv", type=Path, default=None, help="my-madic-catalog.csv path")
    parser.add_argument("--images-dir", type=Path, default=None, help="product-images/ folder")
    parser.add_argument(
        "--no-copy-images",
        action="store_true",
        help="Skip copying images (use existing uploads/products/)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = seed_figma_products(
            db,
            catalog_csv=args.catalog_csv,
            images_dir=args.images_dir,
            copy_images=not args.no_copy_images,
        )
        print("Produits Figma importes :")
        for k, v in result.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
