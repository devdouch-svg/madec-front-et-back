"""Reset products + catalog tables with MADEC food / non-food data.

Usage (from backend/):
    python -m scripts.reset_madec_catalog
"""
from __future__ import annotations

from app.db.reset_madec_catalog import reset_madec_catalog
from app.db.session import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        counts = reset_madec_catalog(db)
        print("MADEC catalogue réinitialisé :")
        for k, v in counts.items():
            print(f"  {k}: {v}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
