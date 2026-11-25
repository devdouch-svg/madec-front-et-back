from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


def _parse_mssql_datetime_string(value: str) -> datetime:
    # Legacy ODBC SQL Server driver returns e.g. '2026-06-06 12:37:09.0672250 +00:00'
    s = value.strip()
    s = re.sub(r"\s+([+-]\d{2}:\d{2})$", r"\1", s)
    s = re.sub(r"(\.\d{6})\d+", r"\1", s)
    return datetime.fromisoformat(s)


class UtcDateTime(TypeDecorator):
    """Timezone-aware DateTime; coerces legacy ODBC string timestamps on read."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return _parse_mssql_datetime_string(value)
        return value
