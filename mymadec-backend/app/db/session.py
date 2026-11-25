from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings


def _make_engine():
    url = settings.db_url
    # echo=False — SQL is logged once via logging config (echo=True duplicates every line)
    kwargs: dict = {"pool_pre_ping": True, "echo": False}

    if url.startswith("sqlite"):
        # SQLite (tests / local dev without SQL Server)
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # SQL Server via pyodbc
        kwargs["pool_size"] = 10
        kwargs["max_overflow"] = 20
        kwargs["connect_args"] = {"timeout": 30}
        # Legacy "SQL Server" driver + SQLAlchemy 2 → HY104 without this
        if settings.odbc_driver == "SQL Server":
            kwargs["use_setinputsizes"] = False

    return create_engine(url, **kwargs)


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
