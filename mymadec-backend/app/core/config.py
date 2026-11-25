from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Prefer modern Microsoft drivers; fall back to whatever is installed on Windows.
_PREFERRED_MSSQL_ODBC_DRIVERS = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
)


def resolve_mssql_odbc_driver(configured: str) -> str:
    """Use the configured driver if installed, otherwise the best available one."""
    name = (configured or "").strip().strip('"').strip("'")
    try:
        import pyodbc

        installed = list(pyodbc.drivers())
    except Exception:
        return name

    if name and name in installed:
        return name
    for candidate in _PREFERRED_MSSQL_ODBC_DRIVERS:
        if candidate in installed:
            return candidate
    return name or (installed[0] if installed else "ODBC Driver 18 for SQL Server")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Application ───────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "My Madec API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENABLE_DOCS: bool = True
    LOG_TO_FILE: bool = True
    SECRET_KEY: str = "change-me-in-production"

    @property
    def show_docs(self) -> bool:
        return self.DEBUG and self.ENABLE_DOCS

    # ── Database ──────────────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 1433
    DB_NAME: str = "mymadec"
    DB_USER: str = "sa"
    DB_PASSWORD: str = ""
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DATABASE_URL: str = ""  # optional full override

    @property
    def odbc_driver(self) -> str:
        return resolve_mssql_odbc_driver(self.DB_DRIVER)

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        driver = self.odbc_driver

        # Named instance (e.g. "localhost\SQLEXPRESS") — don't append port,
        # use Trusted_Connection if no credentials supplied.
        named_instance = "\\" in self.DB_HOST

        if named_instance:
            # Use ODBC connect string to avoid SQLAlchemy URL parsing issues
            # with backslashes.
            # TrustServerCertificate=yes is required for Driver 18 with
            # SQL Server Express (self-signed cert).
            odbc = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.DB_HOST};"
                f"DATABASE={self.DB_NAME};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=yes;"
                f"LoginTimeout=60;"
            )
            if self.DB_USER:
                odbc += f"UID={self.DB_USER};PWD={self.DB_PASSWORD};"
            else:
                odbc += "Trusted_Connection=yes;"
            import urllib.parse
            return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}"

        # Standard host:port — use ODBC connect string to avoid URL-parsing
        # issues when the password contains special chars like @, /, +, etc.
        if driver == "SQL Server":
            tls = "Encrypt=no;"
        else:
            tls = "TrustServerCertificate=yes;Encrypt=yes;"
        odbc = (
            f"DRIVER={{{driver}}};"
            f"SERVER={self.DB_HOST},{self.DB_PORT};"
            f"DATABASE={self.DB_NAME};"
            f"{tls}"
            f"LoginTimeout=60;"
        )
        if self.DB_USER:
            odbc += f"UID={self.DB_USER};PWD={self.DB_PASSWORD};"
        else:
            odbc += "Trusted_Connection=yes;"
        import urllib.parse
        return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc)}"

    # ── Auth ──────────────────────────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    ADMIN_EMAIL: str = "admin@mymadec.com"
    # Set in production via GitHub secret ADMIN_INITIAL_PASSWORD (never rotated on redeploy)
    ADMIN_INITIAL_PASSWORD: str = ""

    # ── CORS / frontend links (emails) ────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    FRONTEND_BASE_URL: str = ""
    # Deep link opened by mobile password-reset emails (not the admin web URL)
    MOBILE_RESET_DEEP_LINK: str = "mymadec://reset-password"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def frontend_base_url(self) -> str:
        if self.FRONTEND_BASE_URL.strip():
            return self.FRONTEND_BASE_URL.strip().rstrip("/")
        origins = self.cors_origins
        return origins[0].rstrip("/") if origins else "http://localhost:3000"

    def mobile_password_reset_url(self, token: str) -> str:
        base = (self.MOBILE_RESET_DEEP_LINK or "mymadec://reset-password").strip().rstrip("?&")
        sep = "&" if "?" in base else "?"
        from urllib.parse import quote

        return f"{base}{sep}token={quote(token, safe='')}"

    # ── File uploads ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    @property
    def allowed_image_types(self) -> List[str]:
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ── Email ─────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "My Madec"
    SMTP_TLS: bool = True
    DISABLE_EMAIL: bool = False
    # Optional: send a test email on API startup (remove in production)
    STARTUP_TEST_EMAIL: str = ""

    @field_validator("DB_DRIVER", mode="before")
    @classmethod
    def strip_db_driver(cls, v):
        if v is None:
            return v
        return str(v).strip().strip('"').strip("'")

    @field_validator(
        "SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM_NAME",
        "STARTUP_TEST_EMAIL", "FRONTEND_BASE_URL", "MOBILE_RESET_DEEP_LINK", "ALLOWED_ORIGINS",
        mode="before",
    )
    @classmethod
    def strip_string_fields(cls, v):
        if v is None:
            return v
        return str(v).strip()

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.strip().lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _enforce_env_security(self) -> "Settings":
        """Fail fast on insecure production/staging configuration."""
        env = self.APP_ENV.strip().lower()
        is_dev = env in {"development", "dev", "local", "test", "testing"}
        if not is_dev:
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == "change-me-in-production"
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "SECRET_KEY must be a strong, unique value (>= 32 chars) outside "
                    "development. Set it via the APP_SECRET_KEY secret."
                )
        if self.is_production and self.DEBUG:
            raise ValueError("DEBUG must be false when APP_ENV=production.")
        return self

    # ── Firebase ──────────────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"
    FIREBASE_CREDENTIALS_JSON: str = ""

    # ── ETL ───────────────────────────────────────────────────────────────────
    ETL_SERVICE_TOKEN: str = ""

    # ── Business rules ────────────────────────────────────────────────────────
    # Fallback fee rate applied to especes orders (e.g. 0.05 = 5%).
    # Admin-editable at runtime from the dashboard (app_settings.cash_fee_rate);
    # this env value is only used until the admin sets it once.
    FIXEDTAX_RATE: float = 0.0

    # ── Demo / seed data ──────────────────────────────────────────────────────
    SEED_DEMO: bool = False
    # Staging: reload MADEC food/non-food products + référentiels on container start
    RESET_MADEC_CATALOG: bool = False

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_RESET_PASSWORD: str = "3/minute"
    RATE_LIMIT_CHANGE_PASSWORD: str = "5/minute"
    RATE_LIMIT_REFRESH: str = "10/minute"
    RATE_LIMIT_RESET_CONFIRM: str = "5/minute"
    # ETL service endpoints (/sync/*) — generous, protects against a runaway/abusive caller.
    RATE_LIMIT_SYNC: str = "120/minute"
    # Shared storage for rate limits — REQUIRED for multi-worker (UVICORN_WORKERS > 1).
    # e.g. redis://redis:6379/0 . Empty → in-process memory (single-worker dev only).
    REDIS_URL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
