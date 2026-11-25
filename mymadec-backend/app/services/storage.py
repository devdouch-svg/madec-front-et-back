from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import BadRequestException

_SAFE_CODE = re.compile(r"^[\w.\-]+$")


def _to_url_path(dest: Path) -> str:
    """Return a public URL path like `/uploads/banners/foo.jpg`."""
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    rel = dest.resolve().relative_to(upload_root)
    return f"/uploads/{rel.as_posix()}"


def _validate_image(file: UploadFile) -> None:
    """Check content-type and file size."""
    if file.content_type not in settings.allowed_image_types:
        raise BadRequestException(
            f"Invalid file type '{file.content_type}'. "
            f"Allowed: {', '.join(settings.allowed_image_types)}"
        )


def _safe_upload_dest(upload_dir: Path, basename: str, ext: str) -> Path:
    safe = Path(basename).name
    if not _SAFE_CODE.fullmatch(safe):
        raise BadRequestException("Invalid filename component")
    dest = (upload_dir / f"{safe}{ext}").resolve()
    root = upload_dir.resolve()
    if not dest.is_relative_to(root):
        raise BadRequestException("Invalid upload path")
    return dest


async def _save_image(file: UploadFile, upload_dir: Path, basename: str) -> str:
    _validate_image(file)

    ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = _safe_upload_dest(upload_dir, basename, ext)

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise BadRequestException(
            f"File too large. Max allowed: {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    _check_magic_bytes(contents, file.content_type)

    with open(dest, "wb") as f:
        f.write(contents)

    return _to_url_path(dest)


async def save_product_image(file: UploadFile, product_code: str) -> str:
    """Save uploaded image for a product. Returns the relative path."""
    return await _save_image(file, Path(settings.UPLOAD_DIR) / "products", product_code)


async def save_banner_image(file: UploadFile, banner_id: int) -> str:
    """Save uploaded image for a banner. Returns the relative path."""
    return await _save_image(file, Path(settings.UPLOAD_DIR) / "banners", f"banner_{banner_id}")


async def save_categorie_image(file: UploadFile, categorie_id: int) -> str:
    """Save uploaded image for a mobile catalog category."""
    return await _save_image(
        file, Path(settings.UPLOAD_DIR) / "categories", f"categorie_{categorie_id}"
    )


def delete_file(path: Optional[str]) -> None:
    if not path:
        return
    normalized = path.replace("\\", "/").lstrip("/")
    if normalized.startswith("app/"):
        normalized = normalized[len("app/") :]
    if ".." in normalized.split("/") or not normalized.startswith("uploads/"):
        return
    target = Path(normalized)
    if target.exists():
        os.remove(target)


# ── Magic-byte validation ─────────────────────────────────────────────────────

_MAGIC = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png":  [b"\x89PNG"],
    "image/webp": [b"RIFF"],
}


def _check_magic_bytes(data: bytes, content_type: str) -> None:
    if content_type == "image/webp":
        if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return
        raise BadRequestException("File content does not match declared type 'image/webp'")

    signatures = _MAGIC.get(content_type, [])
    for sig in signatures:
        if data[: len(sig)] == sig:
            return
    raise BadRequestException(
        f"File content does not match declared type '{content_type}'"
    )
