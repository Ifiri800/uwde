from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class NormalizationResult:
    original: Mapping[str, Any]
    standardized: Mapping[str, Any]
    changed_fields: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return bool(self.changed_fields)


def normalize_field_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("field name must be a string")

    normalized = name.strip().lower()

    for character in (" ", "-", "/", "."):
        normalized = normalized.replace(character, "_")

    while "__" in normalized:
        normalized = normalized.replace("__", "_")

    return normalized.strip("_")


def normalize_record(
    record: Mapping[str, Any],
    field_mapping: Mapping[str, str] | None = None,
) -> NormalizationResult:
    if not isinstance(record, Mapping):
        raise TypeError("record must be a mapping")

    field_mapping = field_mapping or {}

    standardized: dict[str, Any] = {}
    changed: list[str] = []

    for key, value in record.items():
        normalized_key = field_mapping.get(
            key,
            normalize_field_name(key),
        )

        standardized[normalized_key] = value

        if normalized_key != key:
            changed.append(key)

    return NormalizationResult(
        original=dict(record),
        standardized=standardized,
        changed_fields=tuple(changed),
    )


def normalize_records(
    records: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    field_mapping: Mapping[str, str] | None = None,
) -> tuple[NormalizationResult, ...]:
    return tuple(
        normalize_record(record, field_mapping)
        for record in records
    )
