from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .cleaner import clean_record
from .normalizer import normalize_record
from .validators import FieldRule, ValidationResult, validate_record


@dataclass
class PreprocessingResult:
    """Result produced by the preprocessing pipeline."""

    record: dict[str, Any]
    validation: ValidationResult

    @property
    def valid(self) -> bool:
        """Return True when the processed record is valid."""
        return self.validation.valid

    @property
    def errors(self) -> list[str]:
        """Return validation errors."""
        return self.validation.errors

    @property
    def error_count(self) -> int:
        """Return the number of validation errors."""
        return len(self.validation.errors)


def preprocess_record(
    record: dict[str, Any],
    *,
    schema: dict[str, str] | None = None,
    validation_schema: dict[str, FieldRule] | None = None,
    remove_empty: bool = False,
) -> PreprocessingResult:
    """
    Clean, normalize, and validate one extracted record.
    """

    cleaned = clean_record(
        record,
        remove_empty=remove_empty,
    )

    normalized = normalize_record(
        cleaned,
        schema=schema,
    )

    validation = validate_record(
        normalized,
        validation_schema or {},
    )

    return PreprocessingResult(
        record=normalized,
        validation=validation,
    )


def preprocess_records(
    records: list[dict[str, Any]],
    *,
    schema: dict[str, str] | None = None,
    validation_schema: dict[str, FieldRule] | None = None,
    remove_empty: bool = False,
) -> list[PreprocessingResult]:
    """
    Process multiple extracted records.

    Each record is processed independently so that one invalid
    record does not prevent other records from being processed.
    """

    return [
        preprocess_record(
            record,
            schema=schema,
            validation_schema=validation_schema,
            remove_empty=remove_empty,
        )
        for record in records
    ]