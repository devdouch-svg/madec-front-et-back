"""Seed Figma sous-categories (73) under existing CTGS categories.

Prerequis: python -m scripts.seed_ctgs_categories deja execute.

Usage:
    python -m scripts.seed_figma_sous_categories

Docker:
    docker exec backend-api-1 python -m scripts.seed_figma_sous_categories
"""
from __future__ import annotations

from app.db.seed_figma_sous_categories import seed_figma_sous_categories
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        result = seed_figma_sous_categories(db)
        print("Sous-categories Figma importees :")
        for k, v in result.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
