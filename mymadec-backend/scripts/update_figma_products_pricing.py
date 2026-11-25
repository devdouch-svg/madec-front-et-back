"""Met a jour prix + contenance (unit) pour tous les produits.

Sources: my-madic-catalog.csv puis nom produit, sinon valeurs demo.

Usage:
    python -m scripts.update_figma_products_pricing
    python -m scripts.update_figma_products_pricing --only-missing

Docker:
    docker exec backend-api-1 python -m scripts.update_figma_products_pricing
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.db.session import SessionLocal
from app.db.update_figma_products_pricing import update_figma_products_pricing


def main() -> None:
    parser = argparse.ArgumentParser(description="Update product prices and contenance (unit)")
    parser.add_argument("--catalog-csv", type=Path, default=None)
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Ne remplir que prix/unite vides (defaut: tout recalculer)",
    )
    parser.add_argument(
        "--no-fake-prices",
        action="store_true",
        help="Ne pas generer de prix demo si CSV vide",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = update_figma_products_pricing(
            db,
            catalog_csv=args.catalog_csv,
            only_missing=args.only_missing,
            use_fake_prices=not args.no_fake_prices,
        )
        print("Prix / contenance mis a jour :")
        for k, v in result.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
