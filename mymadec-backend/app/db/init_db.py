from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import generate_service_token, hash_password, hash_service_token, generate_password
from app.core.config import settings
from app.models.banner import Banner
from app.models.user import ServiceToken, User

logger = logging.getLogger("mymadec.init_db")


def seed_database(db: Session) -> None:
    _seed_admin(db)
    _seed_service_token(db)
    _seed_banners(db)
    if settings.SEED_DEMO or settings.DEBUG:
        from app.db.seed_demo import seed_demo_data
        seed_demo_data(db)
    logger.info("Database seeded successfully")


def _resolve_admin_password() -> str:
    """Predictable passwords in dev; production uses ADMIN_INITIAL_PASSWORD secret."""
    if settings.SEED_DEMO or settings.DEBUG:
        return "Test1234!"
    if settings.ADMIN_INITIAL_PASSWORD:
        return settings.ADMIN_INITIAL_PASSWORD
    logger.warning(
        "ADMIN_INITIAL_PASSWORD is not set — generating a one-time random admin password. "
        "Set ADMIN_INITIAL_PASSWORD in GitHub secrets for a fixed login."
    )
    return generate_password()


def _seed_admin(db: Session) -> None:
    email = settings.ADMIN_EMAIL.strip().lower()
    existing = db.query(User).filter(User.email == email).first()

    if existing:
        return

    password = _resolve_admin_password()
    admin = User(
        email=email,
        matricule="ADMIN001",
        hashed_password=hash_password(password),
        first_name="Admin",
        last_name="My Madec",
        role="admin",
        is_active=True,
    )
    try:
        db.add(admin)
        db.commit()
    except IntegrityError:
        # Another uvicorn worker created admin first (race on cold start)
        db.rollback()
        logger.info("Admin account already created by another worker — skipping")
        return

    logger.warning("=" * 60)
    logger.warning("DEFAULT ADMIN CREATED")
    logger.warning("  Email   : %s", email)
    logger.warning("  Password: %s", password)
    logger.warning("  ⚠  Save this password — it will not be shown again after this startup!")
    logger.warning("=" * 60)

    from app.services.email import send_welcome_email
    if not send_welcome_email(email, admin.full_name, password):
        logger.warning("Welcome email not sent — use the password logged above to log in")


def _seed_service_token(db: Session) -> None:
    if db.query(ServiceToken).count() > 0:
        return

    plain = settings.ETL_SERVICE_TOKEN or generate_service_token()
    token = ServiceToken(name="ETL Service", token_hash=hash_service_token(plain))
    db.add(token)
    db.commit()
    if settings.ETL_SERVICE_TOKEN:
        logger.info("ETL service token loaded from ETL_SERVICE_TOKEN env var")
        return
    logger.warning("=" * 60)
    logger.warning("ETL SERVICE TOKEN GENERATED")
    logger.warning("  Token: %s", plain)
    logger.warning("  Store this in ETL_SERVICE_TOKEN GitHub secret — shown only once!")
    logger.warning("=" * 60)


def _seed_banners(db: Session) -> None:
    if db.query(Banner).count() > 0:
        return
    for pos in range(3):
        db.add(Banner(position=pos, is_active=False))
    db.commit()
    logger.info("3 empty banners seeded")
