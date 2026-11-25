from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level = logging.DEBUG if settings.DEBUG else logging.INFO

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)

    root = logging.getLogger()
    if "pytest" not in sys.modules:
        root.handlers.clear()
    root.setLevel(level)
    root.addHandler(console)

    if settings.LOG_TO_FILE:
        file_handler = RotatingFileHandler(
            "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root.addHandler(file_handler)

    # Single SQL log stream (avoid echo=True + propagate duplicate lines)
    for name in ("sqlalchemy", "sqlalchemy.engine", "sqlalchemy.engine.Engine"):
        log = logging.getLogger(name)
        log.handlers.clear()
        log.propagate = True
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("uvicorn.access").setLevel(
        logging.INFO if settings.show_docs else logging.WARNING
    )
    uvicorn_err = logging.getLogger("uvicorn.error")
    uvicorn_err.setLevel(logging.INFO)
    uvicorn_err.propagate = True
    logging.getLogger("mymadec").setLevel(level)
    logging.getLogger("mymadec.email").setLevel(level)

    _CONFIGURED = True


logger = logging.getLogger("mymadec")
