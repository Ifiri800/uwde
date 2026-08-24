from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalize text while preserving its semantic content."""
    return _WHITESPACE_RE.sub(" ", value.strip())


def normalize_number(value: Any) -> int | float | Decimal:
    """Normalize a numeric value into an appropriate numeric type."""
    if isinstance(value, bool):
        raise TypeError("Boolean values are not valid numeric values")

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return value

    if isinstance(value, Decimal):
        return value

    if isinstance(value, str):
        text = normalize_text(value)

        if not text:
            raise ValueError("Cannot normalize an empty string as a number")

        try:
            decimal_value = Decimal(text)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid numeric value: {value!r}") from exc

        if decimal_value == decimal_value.to_integral_value():
            return int(decimal_value)

        return decimal_value

    raise TypeError(f"Unsupported numeric value: {type(value).__name__}")


def normalize_boolean(value: Any) -> bool:
    """Normalize common boolean representations."""
    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    if isinstance(value, str):
        normalized = normalize_text(value).lower()

        if normalized in {"true", "yes", "y", "1", "on"}:
            return True

        if normalized in {"false", "no", "n", "0", "off"}:
            return False

    raise ValueError(f"Invalid boolean value: {value!r}")


def normalize_date(value: Any) -> date:
    """Normalize common ISO date representations."""
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise TypeError(
            f"Unsupported date value: {type(value).__name__}"
        )

    text = normalize_text(value)

    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date value: {value!r}") from exc


def normalize_datetime(value: Any) -> datetime:
    """Normalize common ISO datetime representations."""
    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise TypeError(
            f"Unsupported datetime value: {type(value).__name__}"
        )

    text = normalize_text(value)

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(
            f"Invalid ISO datetime value: {value!r}"
        ) from exc


def normalize_url(value: str) -> str:
    """Normalize a URL without changing its destination semantics."""
    if not isinstance(value, str):
        raise TypeError("URL value must be a string")

    value = normalize_text(value)

    if not value:
        raise ValueError("URL cannot be empty")

    parsed = urlsplit(value)

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError(
            "Only HTTP and HTTPS URLs can be normalized"
        )

    if not parsed.netloc:
        raise ValueError("URL must contain a hostname")

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    if not hostname:
        raise ValueError("URL must contain a valid hostname")

    netloc = hostname

    if parsed.port is not None:
        default_port = (
            (scheme == "http" and parsed.port == 80)
            or (scheme == "https" and parsed.port == 443)
        )

        if not default_port:
            netloc = f"{netloc}:{parsed.port}"

    query_pairs = parse_qsl(
        parsed.query,
        keep_blank_values=True,
    )
    normalized_query = urlencode(query_pairs, doseq=True)

    return urlunsplit(
        (
            scheme,
            netloc,
            parsed.path or "",
            normalized_query,
            parsed.fragment,
        )
    )


def normalize_value(
    value: Any,
    *,
    value_type: str | None = None,
) -> Any:
    """
    Normalize a value according to an optional target type.

    Supported target types:
    - text
    - number
    - boolean
    - date
    - datetime
    - url
    """

    if value is None:
        return None

    if value_type is None:
        if isinstance(value, str):
            return normalize_text(value)

        return value

    normalized_type = value_type.lower().strip()

    if normalized_type == "text":
        return normalize_text(str(value))

    if normalized_type == "number":
        return normalize_number(value)

    if normalized_type == "boolean":
        return normalize_boolean(value)

    if normalized_type == "date":
        return normalize_date(value)

    if normalized_type == "datetime":
        return normalize_datetime(value)

    if normalized_type == "url":
        return normalize_url(value)

    raise ValueError(
        f"Unsupported normalization type: {value_type!r}"
    )


def normalize_record(
    record: dict[str, Any],
    schema: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Normalize an extracted record.

    `schema` maps field names to normalization types.
    Fields without a schema entry receive basic text normalization.
    """
    if not isinstance(record, dict):
        raise TypeError("normalize_record() expects a dictionary")

    result: dict[str, Any] = {}

    for field, value in record.items():
        value_type = schema.get(field) if schema else None
        result[field] = normalize_value(
            value,
            value_type=value_type,
        )

    return result