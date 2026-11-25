from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.permissions import require_human_user
from app.core.rate_limits import (
    change_password_rate_limit,
    login_rate_limit,
    refresh_rate_limit,
    reset_confirm_rate_limit,
    reset_password_rate_limit,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth as auth_svc
from app.services.email import send_password_reset_email, send_password_changed_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(login_rate_limit),
):
    user = auth_svc.authenticate(db, login_data.matricule, login_data.password)
    return auth_svc.issue_tokens(user)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user=Depends(require_human_user)):
    # JWT is stateless — client discards tokens.
    # Extend here if you implement a token denylist.
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(refresh_rate_limit),
):
    return auth_svc.refresh_access_token(db, refresh_data.refresh_token)


@router.post("/reset-password/request", response_model=MessageResponse)
def reset_password_request(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db),
    _rl: None = Depends(reset_password_rate_limit),
):
    result = auth_svc.create_reset_token(db, reset_data.email)
    if result:
        user, token = result
        sent = send_password_reset_email(user.email, user.full_name, token)
        if not sent:
            from app.core.logging import logger
            logger.error("Password reset token created for %s but email was not sent", user.email)
    # Always return success to prevent user enumeration
    return {"message": "If that email is registered, a reset code has been sent"}


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    change_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_human_user),
    _rl: None = Depends(change_password_rate_limit),
):
    """Logged-in user changes their own password."""
    from app.core.security import verify_password, hash_password
    from app.core.exceptions import UnauthorizedException
    if not verify_password(change_data.current_password, current_user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")
    current_user.hashed_password = hash_password(change_data.new_password)
    db.commit()
    from app.services.email import send_password_changed_email
    send_password_changed_email(current_user.email, current_user.full_name)
    return {"message": "Password changed successfully"}


@router.post("/reset-password/confirm", response_model=MessageResponse)
def reset_password_confirm(
    confirm_data: PasswordResetConfirm,
    db: Session = Depends(get_db),
    _rl: None = Depends(reset_confirm_rate_limit),
):
    user = auth_svc.confirm_reset_token(db, confirm_data.token, confirm_data.new_password)
    send_password_changed_email(user.email, user.full_name)
    return {"message": "Password reset successfully"}
