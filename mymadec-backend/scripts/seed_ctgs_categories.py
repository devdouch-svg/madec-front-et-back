"""Seed mobile categories from ctgs/*.png (no manual SQL).

Usage (local, from my-madec-backend-test/):
    python -m scripts.seed_ctgs_categories
    python -m scripts.seed_ctgs_categories --ctgs-dir D:\\Mymadic\\ctgs

Usage (Docker on VPS, after scp ctgs to /tmp/ctgs):
    docker exec backend-api-1 python -m scripts.seed_ctgs_categories --ctgs-dir /tmp/ctgs
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.db.seed_ctgs_categories import seed_ctgs_categories
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset + seed catalog categories from ctgs/")
    parser.add_argument(
        "--ctgs-dir",
        type=Path,
        default=None,
        help="Folder with *.png (default: CTGS_DIR env or ../ctgs)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = seed_ctgs_categories(db, ctgs_dir=args.ctgs_dir)
        print("Categories CTGS importées :")
        for k, v in result.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
