"""Shared email validation — allows demo TLDs (.test, .local) used in seeds."""
from __future__ import annotations

from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import BeforeValidator


def _validate_app_email(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Email invalide")
    raw = value.strip()
    if not raw:
        raise ValueError("Email invalide")
    try:
        result = validate_email(
            raw,
            check_deliverability=False,
            test_environment=True,
        )
        return result.normalized
    except EmailNotValidError as exc:
        raise ValueError(str(exc)) from exc


AppEmailStr = Annotated[str, BeforeValidator(_validate_app_email)]
