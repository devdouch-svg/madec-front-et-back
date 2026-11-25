"""
FastAPI-dependency-based rate limiting.

We avoid @limiter.limit() decorators because slowapi's functools.wraps wrapper
breaks FastAPI body-parameter injection in Python 3.13.  Closure-based
dependencies have no such issue.
"""
import logging
from typing import Callable

from fastapi import HTTPException, Request
from limits import parse as parse_limit           # type: ignore[import-untyped]
from limits.storage import MemoryStorage, storage_from_string  # type: ignore[import-untyped]
from limits.strategies import MovingWindowRateLimiter  # type: ignore[import-untyped]
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger("mymadec.ratelimit")


def _build_storage():
    """Redis when REDIS_URL is set (shared across workers), else in-memory.

    A shared backend is REQUIRED for multi-worker deployments — with in-memory
    storage each worker keeps its own counters, defeating brute-force protection.
    """
    if settings.REDIS_URL:
        try:
            storage = storage_from_string(settings.REDIS_URL)
            if storage.check():
                logger.info("Rate limiter storage: Redis (%s)", settings.REDIS_URL.split("@")[-1])
                return storage
            logger.error("Redis rate-limit storage check failed — falling back to in-memory")
        except Exception as exc:  # noqa: BLE001
            logger.error("Redis rate-limit storage unavailable (%s) — falling back to in-memory", exc)
    else:
        logger.warning(
            "REDIS_URL not set — rate limiter using in-memory storage (single-worker only)"
        )
    return MemoryStorage()


_storage = _build_storage()
_window = MovingWindowRateLimiter(_storage)


def make_rate_limit(limit_string: str, endpoint_key: str) -> Callable:
    """Return a FastAPI dependency function that enforces a rate limit."""
    limit_item = parse_limit(limit_string)

    def _dep(request: Request) -> None:
        identifier = f"{endpoint_key}:{get_remote_address(request)}"
        try:
            allowed = _window.hit(limit_item, identifier)
        except Exception as exc:  # noqa: BLE001
            # Fail open: a storage blip must not lock everyone out. Log for alerting.
            logger.error("Rate-limit check failed (%s) — allowing request", exc)
            return
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit_string}). Try again later.",
            )

    return _dep


# Pre-built dependency callables — use as Depends(login_rate_limit)
# Values come from settings so they can be overridden via env vars (e.g. "1000/minute" in tests).

login_rate_limit           = make_rate_limit(settings.RATE_LIMIT_LOGIN,          "login")
reset_password_rate_limit  = make_rate_limit(settings.RATE_LIMIT_RESET_PASSWORD,  "reset_password")
change_password_rate_limit = make_rate_limit(settings.RATE_LIMIT_CHANGE_PASSWORD, "change_password")
refresh_rate_limit         = make_rate_limit(settings.RATE_LIMIT_REFRESH,         "refresh")
reset_confirm_rate_limit   = make_rate_limit(settings.RATE_LIMIT_RESET_CONFIRM,   "reset_confirm")
sync_rate_limit            = make_rate_limit(settings.RATE_LIMIT_SYNC,            "sync")
