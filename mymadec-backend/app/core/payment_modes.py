"""Payment mode helpers: multi-select per user, legacy-compatible storage."""
from __future__ import annotations

from typing import Iterable

ATOMIC_MODES = ("especes", "carte", "deduction_salaire")
ATOMIC_SET = set(ATOMIC_MODES)


def expand_payment_modes(raw: str | None) -> list[str]:
    """Return the list of atomic modes a user may use at checkout."""
    if not raw:
        return ["especes"]
    value = raw.strip()
    if value == "les_deux":
        return ["especes", "carte"]
    if "," in value:
        parts = {p.strip() for p in value.split(",") if p.strip()}
        return [m for m in ATOMIC_MODES if m in parts]
    if value in ATOMIC_SET:
        return [value]
    return ["especes"]


def normalize_payment_modes(modes: Iterable[str]) -> str:
    """Persist modes as a single DB string (legacy les_deux when especes+carte only)."""
    cleaned = {m.strip() for m in modes if m and m.strip() in ATOMIC_SET}
    if not cleaned:
        raise ValueError("Au moins un mode de paiement est requis")
    ordered = [m for m in ATOMIC_MODES if m in cleaned]
    if ordered == ["especes", "carte"]:
        return "les_deux"
    if len(ordered) == 1:
        return ordered[0]
    return ",".join(ordered)


def payment_modes_label(raw: str | None) -> str:
    labels = {
        "especes": "Espèces",
        "carte": "Carte",
        "deduction_salaire": "Déduction salaire",
    }
    return " + ".join(labels[m] for m in expand_payment_modes(raw))
