from __future__ import annotations

import logging
import os
import time

from sqlalchemy import text
from sqlalchemy.exc import InterfaceError, OperationalError

from app.core.config import settings
from app.db.session import SessionLocal, engine

logger = logging.getLogger("mymadec.bootstrap")


def _installed_odbc_drivers() -> list[str]:
    try:
        import pyodbc

        return list(pyodbc.drivers())
    except Exception:
        return []


def wait_for_database(
    *,
    max_attempts: int | None = None,
    delay_seconds: float | None = None,
) -> None:
    """Block until SQL Server accepts connections (Docker / cold start)."""
    if settings.db_url.startswith("sqlite"):
        return

    attempts = max_attempts or int(os.getenv("DB_WAIT_ATTEMPTS", "60"))
    delay = delay_seconds or float(os.getenv("DB_WAIT_DELAY", "2"))

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection OK (attempt %s/%s)", attempt, attempts)
            return
        except InterfaceError as exc:
            logger.error(
                "ODBC driver %r is not available. Installed drivers: %s. "
                "Install 'ODBC Driver 17/18 for SQL Server' or set DB_DRIVER "
                "to an installed driver.",
                settings.odbc_driver,
                _installed_odbc_drivers(),
            )
            raise
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "Database not ready (%s/%s) — retry in %ss: %s",
                attempt,
                attempts,
                delay,
                exc.orig if hasattr(exc, "orig") else exc,
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Could not connect to database at {settings.DB_HOST}:{settings.DB_PORT} "
        f"after {attempts} attempts"
    ) from last_error


def run_startup_seed() -> None:
    """Idempotent seed (admin, service token, banners, optional demo data)."""
    from app.db.init_db import seed_database

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


def run_alembic_migrations() -> None:
    """Apply pending Alembic revisions (idempotent)."""
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations up to date")


def check_database() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
