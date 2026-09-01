from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class NormalizedValue:
    value: float
    unit: str
    currency: str | None = None
    year: int | None = None
    original_value: object | None = None


def normalize_numeric(
    value: int | float | Decimal,
    *,
    unit: str = "value",
    currency: str | None = None,
    year: int | None = None,
) -> NormalizedValue:
    """Normalize numeric research values without changing their meaning."""

    numeric_value = float(value)

    if numeric_value != numeric_value:
        raise ValueError("value cannot be NaN")

    if numeric_value in (
        float("inf"),
        float("-inf"),
    ):
        raise ValueError("value must be finite")

    if not unit.strip():
        raise ValueError("unit is required")

    return NormalizedValue(
        value=numeric_value,
        unit=unit.strip(),
        currency=currency.upper() if currency else None,
        year=year,
        original_value=value,
    )


def normalize_year(value: int | datetime) -> int:
    """Return a four-digit research year."""

    if isinstance(value, datetime):
        year = value.year
    else:
        year = int(value)

    if year < 1900 or year > 2200:
        raise ValueError("year must be between 1900 and 2200")

    return year
