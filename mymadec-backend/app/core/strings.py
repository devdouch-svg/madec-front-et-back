"""Shared string helpers for safe SQL LIKE patterns."""


def escape_like(term: str) -> str:
    """Escape SQL LIKE wildcards so user input is matched literally."""
    return (
        term.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def ilike_pattern(term: str) -> str:
    return f"%{escape_like(term)}%"
