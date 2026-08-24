from __future__ import annotations

import re
from typing import Any


_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    """
    Clean a text value without changing its semantic content.

    Operations:
    - Converts Unicode whitespace sequences to a single space.
    - Removes leading and trailing whitespace.
    """
    value = value.strip()
    value = _WHITESPACE_RE.sub(" ", value)
    return value


def clean_value(
    value: Any,
    *,
    remove_empty: bool = False,
) -> Any:
    """
    Recursively clean an extracted value.

    Strings are normalized.
    Dictionaries and lists are processed recursively.
    Numbers, booleans, and other scalar values are preserved.
    """

    if isinstance(value, str):
        cleaned = clean_text(value)

        if remove_empty and not cleaned:
            return None

        return cleaned

    if isinstance(value, dict):
        cleaned_dict: dict[Any, Any] = {}

        for key, item in value.items():
            cleaned_item = clean_value(
                item,
                remove_empty=remove_empty,
            )

            if remove_empty and cleaned_item is None:
                continue

            cleaned_dict[key] = cleaned_item

        return cleaned_dict

    if isinstance(value, list):
        cleaned_list = []

        for item in value:
            cleaned_item = clean_value(
                item,
                remove_empty=remove_empty,
            )

            if remove_empty and cleaned_item is None:
                continue

            cleaned_list.append(cleaned_item)

        return cleaned_list

    return value


def clean_record(
    record: dict[str, Any],
    *,
    remove_empty: bool = False,
) -> dict[str, Any]:
    """
    Clean a single extracted record.
    """
    result = clean_value(
        record,
        remove_empty=remove_empty,
    )

    if not isinstance(result, dict):
        raise TypeError("clean_record() expects a dictionary record")

    return result