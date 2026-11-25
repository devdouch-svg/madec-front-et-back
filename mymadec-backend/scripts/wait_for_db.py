#!/usr/bin/env python3
"""CLI: wait for SQL Server before migrations / uvicorn (used in Docker entrypoint)."""
from __future__ import annotations

import sys
from pathlib import Path

# Allow `python scripts/wait_for_db.py` from /app
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.logging import setup_logging
from app.db.bootstrap import wait_for_database

if __name__ == "__main__":
    setup_logging()
    try:
        wait_for_database()
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
