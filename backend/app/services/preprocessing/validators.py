from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit


@dataclass(frozen=True)
class FieldRule:
    """Validation rules for a single dataset field."""

    field_type: str
    required: bool = False
    nullable: bool = True
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | int | Decimal | None = None
    maximum: float | int | Decimal | None = None
    allowed_values: tuple[Any, ...] | None = None


@dataclass
class ValidationResult:
    """Result returned by record validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Return the number of validation errors."""
        return len(self.errors)


def _validate_type(
    value: Any,
    field_type: str,
) -> bool:
    """Check whether a value matches the expected field type."""

    if field_type == "text":
        return isinstance(value, str)

    if field_type == "number":
        return (
            isinstance(value, (int, float, Decimal))
            and not isinstance(value, bool)
        )

    if field_type == "boolean":
        return isinstance(value, bool)

    if field_type == "date":
        return isinstance(value, date) and not isinstance(value, datetime)

    if field_type == "datetime":
        return isinstance(value, datetime)

    if field_type == "url":
        if not isinstance(value, str):
            return False

        parsed = urlsplit(value)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
        )

    return False


def validate_value(
    field_name: str,
    value: Any,
    rule: FieldRule,
) -> list[str]:
    """Validate one field against its configured rule."""

    errors: list[str] = []

    if value is None:
        if not rule.nullable:
            errors.append(
                f"{field_name}: value cannot be null"
            )

        return errors

    if not _validate_type(value, rule.field_type):
        errors.append(
            f"{field_name}: expected type "
            f"{rule.field_type}"
        )
        return errors

    if rule.field_type == "text":
        length = len(value)

        if (
            rule.min_length is not None
            and length < rule.min_length
        ):
            errors.append(
                f"{field_name}: length must be at least "
                f"{rule.min_length}"
            )

        if (
            rule.max_length is not None
            and length > rule.max_length
        ):
            errors.append(
                f"{field_name}: length must be at most "
                f"{rule.max_length}"
            )

    if rule.field_type == "number":
        if (
            rule.minimum is not None
            and value < rule.minimum
        ):
            errors.append(
                f"{field_name}: value must be at least "
                f"{rule.minimum}"
            )

        if (
            rule.maximum is not None
            and value > rule.maximum
        ):
            errors.append(
                f"{field_name}: value must be at most "
                f"{rule.maximum}"
            )

    if (
        rule.allowed_values is not None
        and value not in rule.allowed_values
    ):
        errors.append(
            f"{field_name}: value is not an allowed value"
        )

    return errors


def validate_record(
    record: dict[str, Any],
    schema: dict[str, FieldRule],
) -> ValidationResult:
    """
    Validate a complete extracted record against a schema.
    """

    if not isinstance(record, dict):
        return ValidationResult(
            valid=False,
            errors=["record: expected a dictionary"],
        )

    errors: list[str] = []

    for field_name, rule in schema.items():
        if field_name not in record:
            if rule.required:
                errors.append(
                    f"{field_name}: required field is missing"
                )

            continue

        errors.extend(
            validate_value(
                field_name,
                record[field_name],
                rule,
            )
        )

    return ValidationResult(
        valid=not errors,
        errors=errors,
    )