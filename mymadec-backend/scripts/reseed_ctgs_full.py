"""Delete + re-seed CTGS categories, Figma sous-categories, and products.

Same flow as before (3 scripts in order). Each step wipes its target tables first.

Usage (local, from my-madec-backend-test/):
    python -m scripts.reseed_ctgs_full
    python -m scripts.reseed_ctgs_full --ctgs-dir D:\\Mymadic\\ctgs

Docker (VPS):
    docker exec backend-api-1 python -m scripts.reseed_ctgs_full --ctgs-dir /tmp/seed-data/ctgs \\
        --catalog-csv /tmp/seed-data/my-madic-catalog.csv \\
        --images-dir /tmp/seed-data/product-images
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.db.seed_ctgs_categories import default_ctgs_dir, seed_ctgs_categories
from app.db.seed_figma_products import seed_figma_products
from app.db.seed_figma_sous_categories import seed_figma_sous_categories
from app.db.figma_product_catalog import default_catalog_csv, default_product_images_dir
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe + re-import CTGS catalog (cat, sous-cat, products)")
    parser.add_argument("--ctgs-dir", type=Path, default=None)
    parser.add_argument("--catalog-csv", type=Path, default=None)
    parser.add_argument("--images-dir", type=Path, default=None)
    parser.add_argument("--no-copy-images", action="store_true")
    args = parser.parse_args()

    ctgs = args.ctgs_dir or default_ctgs_dir()
    csv_path = args.catalog_csv or default_catalog_csv()
    img_dir = args.images_dir or default_product_images_dir()

    db = SessionLocal()
    try:
        print("==> 1/3 CTGS categories (delete all + re-import)...")
        r1 = seed_ctgs_categories(db, ctgs_dir=ctgs)
        for k, v in r1.items():
            print(f"    {k}: {v}")

        print("==> 2/3 Figma sous-categories (delete all + re-import)...")
        r2 = seed_figma_sous_categories(db)
        for k, v in r2.items():
            print(f"    {k}: {v}")

        print("==> 3/3 Figma products (delete all + re-import)...")
        r3 = seed_figma_products(
            db,
            catalog_csv=csv_path,
            images_dir=img_dir,
            copy_images=not args.no_copy_images,
        )
        for k, v in r3.items():
            print(f"    {k}: {v}")

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
