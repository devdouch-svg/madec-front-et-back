from __future__ import annotations

"""Read/write helpers for global admin-editable business settings.

Settings live in the ``app_settings`` table (key/value). Cash fee surcharge
is disabled — order totals use Sabile prices as-is.
"""

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

# ── Setting keys ──────────────────────────────────────────────────────────────
KEY_CASH_FEE_RATE = "cash_fee_rate"
KEY_DEFAULT_PLAFOND = "default_plafond_mensuel"


def _get_raw(db: Session, key: str) -> str | None:
    row = db.get(AppSetting, key)
    return row.value if row else None


def _set_raw(db: Session, key: str, value: str) -> None:
    row = db.get(AppSetting, key)
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


# ── Cash fee rate ─────────────────────────────────────────────────────────────
# Historically applied on espèces orders. Disabled: prices come from Sabile as-is.

def get_cash_fee_rate(db: Session) -> float:
    """Always 0 — no fee is added on top of Sabile prices."""
    _ = db
    return 0.0


def set_cash_fee_rate(db: Session, rate: float) -> float:
    """Persist is a no-op for compatibility; effective rate stays 0."""
    _ = db, rate
    return 0.0


# ── Default monthly plafond (applied on new acheteur creation / ETL sync) ─────

def get_default_plafond(db: Session) -> float | None:
    """None = unlimited for new users."""
    raw = _get_raw(db, KEY_DEFAULT_PLAFOND)
    if raw is None or raw.strip() == "" or raw.strip().lower() in ("null", "none", "unlimited"):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def set_default_plafond(db: Session, plafond: float | None) -> float | None:
    if plafond is None:
        _set_raw(db, KEY_DEFAULT_PLAFOND, "")
        return None
    if plafond < 0:
        raise ValueError("Le plafond par défaut doit être >= 0")
    _set_raw(db, KEY_DEFAULT_PLAFOND, str(plafond))
    return plafond
