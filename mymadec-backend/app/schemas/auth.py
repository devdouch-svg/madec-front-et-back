from __future__ import annotations

import re

from pydantic import BaseModel, field_validator

from app.schemas.email_types import AppEmailStr


def _validate_password_strength(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule")
    if not re.search(r"[a-z]", v):
        raise ValueError("Le mot de passe doit contenir au moins une minuscule")
    if not re.search(r"\d", v):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre")
    return v


class LoginRequest(BaseModel):
    """`matricule` kept for API compat — value is Assabil USER_LOGIN (or matricule/email)."""

    matricule: str
    password: str

    model_config = {"str_strip_whitespace": True}

    @field_validator("matricule")
    @classmethod
    def validate_login(cls, v: str) -> str:
        if not v:
            raise ValueError("L'identifiant de connexion est requis")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: AppEmailStr

    model_config = {"str_strip_whitespace": True}


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    model_config = {"str_strip_whitespace": True}

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v:
            raise ValueError("Le code de réinitialisation est requis")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    model_config = {"str_strip_whitespace": True}

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)
