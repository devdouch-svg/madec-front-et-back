"""Resolve product unit (contenance) and price from catalog CSV + product name."""
from __future__ import annotations

import re
import zlib
from typing import Iterable

CONTENANCE_RE = re.compile(
    r"(\d+(?:[,.]\d+)?\s*(?:CL|ML|L|G|KG|PCS|U|PIÈCES?|PIECES?)(?:\s*\*\s*\d+U)?|\d+\s*PCS\s*\d+\s*G)",
    re.I,
)

INVALID_UNITS = {"", "0", "0G", "0ML", "0 L", "N/A", "NA"}


def _norm_unit(value: str | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip().upper().replace(" ", "").replace(",", ".")
    if not s or s in {x.replace(" ", "") for x in INVALID_UNITS}:
        return None
    return s


def pricing_row_score(row: dict[str, str]) -> int:
    score = 0
    if str(row.get("prix_unitaire_dh", "")).strip():
        score += 8
    if _norm_unit(row.get("contenance")):
        score += 4
    if _norm_unit(row.get("unite")):
        score += 2
    return score


def pick_pricing_rows(rows: Iterable[dict[str, str]]) -> dict[str, dict[str, str]]:
    picked: dict[str, dict[str, str]] = {}
    scores: dict[str, int] = {}
    for row in rows:
        name = row.get("produit", "").strip()
        if not name:
            continue
        key = name.upper()
        s = pricing_row_score(row)
        if key not in picked or s > scores[key]:
            picked[key] = row
            scores[key] = s
    return picked


def parse_price(value: str | None) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        p = float(str(value).replace(",", ".").strip())
        return p if p > 0 else None
    except ValueError:
        return None


def fake_price(product_code: str) -> float:
    """Demo price when CSV has no prix (same range as update_products_price_contenance.sql)."""
    checksum = zlib.crc32(product_code.encode("utf-8")) & 0xFFFFFFFF
    if checksum >= 0x80000000:
        checksum -= 0x100000000
    return round((abs(checksum) % 2400 + 300) / 20.0, 2)


def unit_from_name(name: str) -> str | None:
    m = CONTENANCE_RE.search(name)
    if m:
        return _norm_unit(m.group(0))
    upper = name.upper()
    if re.search(r"\d+ML", upper):
        m = re.search(r"(\d+)ML", upper)
        return f"{m.group(1)}ML" if m else "500ML"
    if re.search(r"\d+G\b", upper) or re.search(r"\d+G\*", upper):
        m = re.search(r"(\d+)G", upper)
        return f"{m.group(1)}G" if m else "250G"
    if re.search(r"\d+KG", upper):
        m = re.search(r"(\d+)KG", upper)
        return f"{m.group(1)}KG" if m else "1KG"
    if re.search(r"\d+L\b", upper):
        m = re.search(r"(\d+)L", upper)
        return f"{m.group(1)}L" if m else "1L"
    if "PCS" in upper or re.search(r"\d+U\b", upper):
        m = re.search(r"(\d+)PCS", upper) or re.search(r"(\d+)U", upper)
        return f"{m.group(1)}U" if m else "12U"
    return None


def fake_unit(product_code: str) -> str:
    checksum = zlib.crc32(product_code.encode("utf-8")) & 0xFFFFFFFF
    if checksum >= 0x80000000:
        checksum -= 0x100000000
    options = ("250G", "500G", "1KG", "330ML", "500ML", "12U")
    return options[abs(checksum) % len(options)]


def resolve_product_unit(
    product_name: str,
    *,
    csv_contenance: str | None = None,
    csv_unite: str | None = None,
    product_code: str | None = None,
) -> str:
    from_csv = _norm_unit(csv_contenance)
    if from_csv:
        return from_csv

    cont = (csv_contenance or "").strip()
    unite = (csv_unite or "").strip()
    if cont and unite:
        combined = _norm_unit(f"{cont}{unite}")
        if combined:
            return combined

    from_name = unit_from_name(product_name)
    if from_name:
        return from_name

    if product_code:
        return fake_unit(product_code)
    return "250G"


def resolve_product_price(
    product_code: str,
    *,
    csv_prix: str | None = None,
    use_fake_if_missing: bool = True,
) -> float | None:
    price = parse_price(csv_prix)
    if price is not None:
        return price
    if use_fake_if_missing:
        return fake_price(product_code)
    return None
