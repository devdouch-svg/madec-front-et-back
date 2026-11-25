from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_reset_token,
    hash_password,
    verify_password,
)
from app.core.config import settings
from app.models.user import PasswordResetToken, User
from app.services.user import get_user_by_email, get_user_by_login


def authenticate(db: Session, login: str, password: str) -> User:
    """Authenticate with Assabil USER_LOGIN, matricule, or email."""
    user = get_user_by_login(db, login)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedException("Identifiant ou mot de passe incorrect")
    if not user.is_active:
        raise UnauthorizedException("Account is disabled")
    if user.role == "service":
        raise UnauthorizedException("Service accounts must use the ETL API token, not the web login")
    return user


def issue_tokens(user: User) -> dict:
    extra = {"role": user.role, "email": user.email}
    return {
        "access_token": create_access_token(user.id, extra),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")
        user_id = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise UnauthorizedException("Invalid or expired refresh token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")
    if user.role == "service":
        raise UnauthorizedException("Service accounts cannot use refresh tokens")
    return issue_tokens(user)


# ── Password reset ────────────────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_reset_token(db: Session, email: str) -> Optional[tuple[User, str]]:
    """
    Create a password-reset token for the given email.
    Returns (user, plain_token) or None if email not found.
    We return None (not an error) to avoid user enumeration.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None

    # Invalidate previous tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == False,
    ).update({"used": True})

    plain = generate_reset_token()
    token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(plain),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
    )
    db.add(token)
    db.commit()
    return user, plain


def confirm_reset_token(db: Session, plain_token: str, new_password: str) -> User:
    token_hash = _hash_token(plain_token)
    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
        )
        .first()
    )
    if not record:
        raise BadRequestException("Invalid or expired reset token")

    now = datetime.now(timezone.utc)
    expires = record.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        raise BadRequestException("Reset token has expired")

    user = db.get(User, record.user_id)
    if not user:
        raise BadRequestException("User not found")

    user.hashed_password = hash_password(new_password)
    record.used = True
    db.commit()
    db.refresh(user)
    return user
