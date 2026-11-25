from __future__ import annotations

from typing import Generator, Optional

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token, verify_service_token
from app.db.session import SessionLocal


# ── Database session ──────────────────────────────────────────────────────────

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Auth dependencies ─────────────────────────────────────────────────────────

def _extract_bearer(authorization: str) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1]


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Validate JWT access token and return the authenticated User."""
    from app.models.user import User

    token = _extract_bearer(authorization)
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type")
        user_id: int = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise UnauthorizedException("Invalid or expired token")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    if not current_user.is_active:
        raise ForbiddenException("Inactive account")
    return current_user


# ── Role guards ───────────────────────────────────────────────────────────────

def require_role(*roles: str):
    """Factory: returns a dependency that requires one of the given roles."""

    def _guard(current_user=Depends(get_current_user)):
        if current_user.role == "service":
            raise ForbiddenException("Service accounts cannot access this resource")
        if current_user.role not in roles:
            raise ForbiddenException(
                f"Requires one of the following roles: {', '.join(roles)}"
            )
        return current_user

    return _guard


require_admin        = require_role("admin")
require_admin_or_gest = require_role("admin", "gestionnaire")


# ── Service-token auth (for ETL) ──────────────────────────────────────────────

def get_service_auth(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """Validate a static service bearer token (used by ETL service)."""
    from app.models.user import ServiceToken

    token = _extract_bearer(authorization)
    service = (
        db.query(ServiceToken)
        .filter(ServiceToken.is_active == True)
        .all()
    )
    for svc in service:
        if verify_service_token(token, svc.token_hash):
            # update last_used_at
            from datetime import datetime, timezone
            svc.last_used_at = datetime.now(timezone.utc)
            db.commit()
            return svc
    raise UnauthorizedException("Invalid service token")
