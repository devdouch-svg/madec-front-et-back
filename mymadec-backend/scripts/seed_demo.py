"""Standalone script to seed or re-seed demo data.

Usage (from backend/):
    python -m scripts.seed_demo          # seed if missing
    python -m scripts.seed_demo --force  # delete demo data and re-seed
"""
from __future__ import annotations

import argparse
import sys

from app.db.session import SessionLocal
from app.db.init_db import seed_database
from app.models.notification import Notification
from app.models.order import Order, OrderLine, OrderStatusHistory
from app.models.product import Product
from app.models.user import User
from app.db.seed_demo import MARKER_EMAIL, seed_demo_data


def _clear_demo(db) -> None:
    """Remove demo rows (identified by @mymadec.test emails and demo products)."""
    demo_users = db.query(User).filter(User.email.like("%@mymadec.test")).all()
    demo_ids = [u.id for u in demo_users]

    if demo_ids:
        db.query(Notification).filter(Notification.user_id.in_(demo_ids)).delete(synchronize_session=False)
        order_ids = [o.id for o in db.query(Order).filter(Order.user_id.in_(demo_ids)).all()]
        if order_ids:
            db.query(OrderLine).filter(OrderLine.order_id.in_(order_ids)).delete(synchronize_session=False)
            db.query(OrderStatusHistory).filter(OrderStatusHistory.order_id.in_(order_ids)).delete(synchronize_session=False)
            db.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)

    db.query(User).filter(User.email.like("%@mymadec.test")).delete(synchronize_session=False)
    db.query(Product).filter(Product.product_code.like("PLO-%")).delete(synchronize_session=False)
    db.query(Product).filter(Product.product_code.like("ELE-%")).delete(synchronize_session=False)
    db.query(Product).filter(Product.product_code.like("QUI-%")).delete(synchronize_session=False)
    db.query(Product).filter(Product.product_code.like("OUT-%")).delete(synchronize_session=False)
    db.commit()
    print("Demo data cleared.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed My Madec demo data")
    parser.add_argument("--force", action="store_true", help="Clear existing demo data and re-seed")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.force:
            _clear_demo(db)
        elif db.query(User).filter(User.email == MARKER_EMAIL).first():
            print("Demo data already exists. Use --force to re-seed.")
            sys.exit(0)

        seed_demo_data(db)
        print("\nDone! Login with any @mymadec.test account — password: Test1234!")
        print("Admin: admin@mymadec.com — password: Test1234!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
