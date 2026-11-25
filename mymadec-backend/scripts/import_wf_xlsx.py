"""Import LISTE BASE APPLI SALARIE WF Excel into catalog + products.

Usage (from mymadec-backend):
    python -m scripts.import_wf_xlsx
    python -m scripts.import_wf_xlsx --xlsx "D:\\Mymadec\\LISTE BASE APPLI SALARIE WF_ Brief Dev 2026.xlsx"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.db.import_wf_xlsx import (
    DEFAULT_XLSX,
    attach_export_category_images,
    attach_export_product_images,
    import_wf_xlsx,
)
from app.db.session import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Import WF product Excel into the database")
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--images-dir", type=Path, default=None)
    parser.add_argument("--images-only", action="store_true", help="Only attach export images")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.images_only:
            result = attach_export_product_images(db, images_dir=args.images_dir)
            result.update(attach_export_category_images(db))
            print("Images WF OK:")
        else:
            result = import_wf_xlsx(db, xlsx_path=args.xlsx, images_dir=args.images_dir)
            print("Import WF OK:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
