from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.limiter import limiter          # ← single shared instance
from app.core.logging import setup_logging

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.show_docs else None,
    redoc_url="/redoc" if settings.show_docs else None,
    openapi_url="/openapi.json" if settings.show_docs else None,
)

# Attach limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors = {
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type", "Accept"],
}
if settings.DEBUG:
    # Phone / LAN (Expo, Flutter web, etc.) — any http(s) origin while developing
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        **_cors,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        **_cors,
    )


# ── Security headers middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)

# Uploaded images (products, banners)
_uploads = Path(settings.UPLOAD_DIR)
_uploads.mkdir(parents=True, exist_ok=True)
if _uploads.is_dir():
    app.mount("/uploads", StaticFiles(directory=str(_uploads)), name="uploads")

_static = Path(__file__).resolve().parent / "static"
_static.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    from app.core.logging import logger
    from app.db.bootstrap import run_alembic_migrations, run_startup_seed, wait_for_database
    from app.services.email import is_email_enabled, send_startup_test_email
    from app.models.base import Base
    from app.db.session import engine

    # Import all models so Alembic / create_all can see them
    import app.models.user        # noqa
    import app.models.product     # noqa
    import app.models.order       # noqa
    import app.models.notification # noqa
    import app.models.banner      # noqa
    import app.models.sync_log    # noqa

    if not settings.DEBUG and settings.SECRET_KEY in ("change-me-in-production", ""):
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")

    logger.info("Starting %s v%s [%s]", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV)

    # Docker entrypoint waits + migrates; local dev may start before SQL Server is up
    if os.getenv("SKIP_DB_WAIT") != "1":
        wait_for_database()

    if os.getenv("SKIP_MIGRATIONS") != "1":
        try:
            run_alembic_migrations()
        except Exception as exc:
            logger.error("Alembic migration failed: %s", exc)
            raise

    # Legacy "SQL Server" ODBC driver breaks SQLAlchemy table reflection (HY104).
    # Remote/staging DBs already have schema — skip create_all in that case.
    if settings.DEBUG and settings.odbc_driver != "SQL Server":
        Base.metadata.create_all(bind=engine)

    run_startup_seed()

    if is_email_enabled():
        # Do not block API startup on SMTP — a hung DNS/TLS check would leave
        # old zombie listeners answering reset requests without sending mail.
        logger.info(
            "Email enabled — SMTP %s:%s as %s (connection verified on first send)",
            settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USER,
        )
        test_to = settings.STARTUP_TEST_EMAIL.strip()
        if test_to:
            try:
                if send_startup_test_email(test_to):
                    logger.info("Startup test email sent to %s", test_to)
                else:
                    logger.error("Startup test email FAILED for %s — check SMTP logs above", test_to)
            except Exception as exc:
                logger.error("Startup test email error for %s: %s", test_to, exc)
    else:
        logger.warning(
            "Email disabled — DISABLE_EMAIL=%s, SMTP_USER set=%s",
            settings.DISABLE_EMAIL,
            bool(settings.SMTP_USER),
        )


def _frontend_redirect_url(request: Request) -> str:
    """Prefer FRONTEND_BASE_URL; else same host on the Vite port (5173)."""
    configured = settings.FRONTEND_BASE_URL.strip().rstrip("/")
    if configured:
        return configured
    host = (request.headers.get("x-forwarded-host") or request.url.hostname or "localhost").split(",")[0].strip()
    # Keep localhost / 127.0.0.1 as-is; LAN IP stays so phones open the right front
    if host in ("127.0.0.1", "localhost"):
        return "http://localhost:5173"
    return f"http://{host}:5173"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root_landing(request: Request):
    """Splash page when someone hits the API host — then redirect to the admin front."""
    front = _frontend_redirect_url(request)
    delay_sec = 1
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="{delay_sec};url={front}" />
  <title>My Madec</title>
  <style>
    :root {{
      --madec: #5156be;
      --madec-mid: #6266c9;
      --madec-light: #7478cb;
      --tint: #eef0fa;
      --text: #313533;
      --muted: #74788d;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: "Segoe UI", system-ui, sans-serif;
      color: var(--text);
      background:
        radial-gradient(ellipse 70% 50% at 15% 0%, rgba(81,86,190,.22), transparent 55%),
        radial-gradient(ellipse 60% 45% at 100% 100%, rgba(116,120,203,.18), transparent 50%),
        linear-gradient(165deg, #f8f9fa 0%, var(--tint) 45%, #e5e6f6 100%);
    }}
    main {{
      text-align: center;
      padding: 2rem 1.5rem;
      max-width: 26rem;
      animation: fade .35s ease-out both;
    }}
    @keyframes fade {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: none; }}
    }}
    .logo {{
      width: min(220px, 70vw);
      height: auto;
      object-fit: contain;
      filter: drop-shadow(0 8px 20px rgba(81,86,190,.18));
    }}
  </style>
</head>
<body>
  <main>
    <a href="{front}" aria-label="My Madec">
      <img class="logo" src="/static/madec-logo.png" alt="MADEC" />
    </a>
  </main>
</body>
</html>
"""
    return HTMLResponse(content=html)


@app.get("/health", tags=["health"])
def health():
    from app.db.bootstrap import check_database

    db_ok = check_database()
    body = {"status": "ok" if db_ok else "degraded"}
    if not db_ok:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
    return body
