from __future__ import annotations

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


# ── Custom HTTP exceptions ────────────────────────────────────────────────────

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class PlafondExceededException(HTTPException):
    def __init__(self, available: float, requested: float):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "PLAFOND_EXCEEDED",
                "message": "Monthly spending limit exceeded",
                "available": available,
                "requested": requested,
            },
        )


# ── Exception handlers (register on the FastAPI app) ─────────────────────────
# All error responses use FastAPI's standard {"detail": ...} envelope so that
# the frontend and any API clients only need to read response.data.detail.

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Standard shape: {"detail": <str | dict>}.
    The WWW-Authenticate header (401) is forwarded when present."""
    headers = getattr(exc, "headers", None) or {}
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for e in exc.errors():
        msg = e["msg"]
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        errors.append({
            "field": ".".join(str(loc) for loc in e["loc"][1:]),
            "message": msg,
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "fields": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging
    logging.getLogger("mymadec").exception(
        "Unhandled error on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"},
    )
