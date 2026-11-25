"""Seed 4 promotions (3 liquidations + 1 promo classique).

Usage (from backend/):
    python -m scripts.seed_promo_liquidations
    python -m scripts.seed_promo_liquidations --clear
"""
from __future__ import annotations

import argparse
import sys

from app.db.seed_promo_liquidations import clear_promo_liquidations, seed_promo_liquidations
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed promo + liquidation demo products")
    parser.add_argument("--clear", action="store_true", help="Remove SEED-PROMO-* products")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.clear:
            n = clear_promo_liquidations(db)
            print(f"Removed {n} seed product(s).")
            return

        result = seed_promo_liquidations(db)
        print(
            f"Done — {result['created']} created, {result['updated']} updated "
            f"({result['promotions']} promos, {result['liquidations']} liquidations)"
        )
        print("Codes: SEED-PROMO-001 … SEED-PROMO-004")
        print("Liquidations API: GET /api/v1/products/mobile?is_liquidation=true")
        print("Promos API:       GET /api/v1/products/mobile?has_discount=true")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
