"""
Central authorization helpers — enforce role-based access at the API layer.
"""
from __future__ import annotations

from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenException
from fastapi import Depends

HUMAN_ROLES = frozenset({"admin", "gestionnaire", "acheteur"})
STAFF_ROLES = frozenset({"admin", "gestionnaire"})


def require_human_user(current_user=Depends(get_current_user)):
    """Block ETL service accounts from interactive (JWT) application APIs."""
    if current_user.role == "service":
        raise ForbiddenException("Service accounts cannot access this resource")
    if current_user.role not in HUMAN_ROLES:
        raise ForbiddenException("Access denied")
    return current_user


def require_acheteur(current_user=Depends(require_human_user)):
    if current_user.role != "acheteur":
        raise ForbiddenException("Only buyer accounts can perform this action")
    return current_user


def require_staff(current_user=Depends(require_human_user)):
    if current_user.role not in STAFF_ROLES:
        raise ForbiddenException("Requires admin or gestionnaire role")
    return current_user
