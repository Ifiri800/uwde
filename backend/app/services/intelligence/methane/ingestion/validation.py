from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from .models import (
    GeospatialReference,
    IngestionBatch,
    IngestionMetadata,
    IngestionRecord,
    IngestionSourceType,
    ObservationStatus,
    TemporalReference,
    UnitValue,
)
from .registry import IngestionRegistry


class IngestionValidationError(ValueError):
    """Raised when ingestion data violates validation rules."""


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def issue_count(self) -> int:
        return len(self.issues)


def _issue(field: str, message: str) -> ValidationIssue:
    return ValidationIssue(field=field, message=message)


def validate_metadata(
    metadata: IngestionMetadata,
) -> ValidationResult:
    issues: list[ValidationIssue] = []

    if not isinstance(metadata, IngestionMetadata):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "metadata",
                    "must be IngestionMetadata",
                ),
            ),
        )

    if not metadata.source_id.strip():
        issues.append(_issue("source_id", "is required"))

    if not metadata.source_name.strip():
        issues.append(_issue("source_name", "is required"))

    if not isinstance(metadata.source_type, IngestionSourceType):
        issues.append(
            _issue(
                "source_type",
                "must be IngestionSourceType",
            )
        )

    if not isinstance(metadata.acquired_at, datetime):
        issues.append(
            _issue(
                "acquired_at",
                "must be datetime",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_temporal(
    temporal: TemporalReference | None,
) -> ValidationResult:
    if temporal is None:
        return ValidationResult(valid=True)

    if not isinstance(temporal, TemporalReference):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "temporal",
                    "must be TemporalReference",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not isinstance(temporal.observed_at, datetime):
        issues.append(
            _issue(
                "temporal.observed_at",
                "must be datetime",
            )
        )

    if (
        temporal.duration_seconds is not None
        and temporal.duration_seconds < 0
    ):
        issues.append(
            _issue(
                "temporal.duration_seconds",
                "cannot be negative",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_geospatial(
    geospatial: GeospatialReference | None,
) -> ValidationResult:
    if geospatial is None:
        return ValidationResult(valid=True)

    if not isinstance(geospatial, GeospatialReference):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "geospatial",
                    "must be GeospatialReference",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if (
        geospatial.latitude is not None
        and not -90.0 <= geospatial.latitude <= 90.0
    ):
        issues.append(
            _issue(
                "geospatial.latitude",
                "must be between -90 and 90",
            )
        )

    if (
        geospatial.longitude is not None
        and not -180.0 <= geospatial.longitude <= 180.0
    ):
        issues.append(
            _issue(
                "geospatial.longitude",
                "must be between -180 and 180",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_unit_value(
    measurement: UnitValue,
) -> ValidationResult:
    if not isinstance(measurement, UnitValue):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "measurement",
                    "must be UnitValue",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not isinstance(measurement.value, (int, float)):
        issues.append(
            _issue(
                "measurement.value",
                "must be numeric",
            )
        )

    if not isinstance(measurement.unit, str):
        issues.append(
            _issue(
                "measurement.unit",
                "must be a string",
            )
        )
    elif not measurement.unit.strip():
        issues.append(
            _issue(
                "measurement.unit",
                "is required",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_record(
    record: IngestionRecord,
    registry: IngestionRegistry | None = None,
) -> ValidationResult:
    if not isinstance(record, IngestionRecord):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "record",
                    "must be IngestionRecord",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not record.record_id.strip():
        issues.append(
            _issue("record_id", "is required")
        )

    if not isinstance(record.data, Mapping):
        issues.append(
            _issue("data", "must be a mapping")
        )

    issues.extend(
        validate_metadata(record.metadata).issues
    )

    issues.extend(
        validate_temporal(record.temporal).issues
    )

    issues.extend(
        validate_geospatial(record.geospatial).issues
    )

    if not isinstance(record.status, ObservationStatus):
        issues.append(
            _issue(
                "status",
                "must be ObservationStatus",
            )
        )

    if not isinstance(record.schema_version, str):
        issues.append(
            _issue(
                "schema_version",
                "must be a string",
            )
        )
    elif not record.schema_version.strip():
        issues.append(
            _issue(
                "schema_version",
                "is required",
            )
        )

    if record.record_version < 1:
        issues.append(
            _issue(
                "record_version",
                "must be >= 1",
            )
        )

    if registry is not None:
        if not registry.contains(record.metadata.source_id):
            issues.append(
                _issue(
                    "metadata.source_id",
                    "source is not registered",
                )
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_batch(
    batch: IngestionBatch,
    registry: IngestionRegistry | None = None,
) -> ValidationResult:
    if not isinstance(batch, IngestionBatch):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "batch",
                    "must be IngestionBatch",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not batch.batch_id.strip():
        issues.append(
            _issue("batch_id", "is required")
        )

    if not isinstance(batch.created_at, datetime):
        issues.append(
            _issue(
                "created_at",
                "must be datetime",
            )
        )

    if not isinstance(
        batch.source_type,
        IngestionSourceType,
    ):
        issues.append(
            _issue(
                "source_type",
                "must be IngestionSourceType",
            )
        )

    record_ids: set[str] = set()

    for index, record in enumerate(batch.records):
        result = validate_record(
            record,
            registry=registry,
        )

        issues.extend(
            _issue(
                f"records[{index}].{issue.field}",
                issue.message,
            )
            for issue in result.issues
        )

        if isinstance(record, IngestionRecord):
            if record.record_id in record_ids:
                issues.append(
                    _issue(
                        f"records[{index}].record_id",
                        "duplicate record_id in batch",
                    )
                )

            record_ids.add(record.record_id)

            if (
                isinstance(
                    record.metadata.source_type,
                    IngestionSourceType,
                )
                and record.metadata.source_type
                != batch.source_type
            ):
                issues.append(
                    _issue(
                        f"records[{index}].metadata.source_type",
                        "does not match batch source_type",
                    )
                )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_ingestion(
    records: tuple[IngestionRecord, ...],
    registry: IngestionRegistry | None = None,
) -> ValidationResult:
    """
    Top-level validation entry point for ingestion records.
    """
    if not isinstance(records, tuple):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "records",
                    "must be a tuple of IngestionRecord",
                ),
            ),
        )

    issues: list[ValidationIssue] = []
    record_ids: set[str] = set()

    for index, record in enumerate(records):
        result = validate_record(
            record,
            registry=registry,
        )

        issues.extend(
            _issue(
                f"records[{index}].{issue.field}",
                issue.message,
            )
            for issue in result.issues
        )

        if isinstance(record, IngestionRecord):
            if record.record_id in record_ids:
                issues.append(
                    _issue(
                        f"records[{index}].record_id",
                        "duplicate record_id",
                    )
                )

            record_ids.add(record.record_id)

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def require_valid(
    result: ValidationResult,
) -> None:
    """Raise IngestionValidationError when validation fails."""
    if not result.valid:
        messages = "; ".join(
            f"{issue.field}: {issue.message}"
            for issue in result.issues
        )

        raise IngestionValidationError(messages)
def validate_ingestion_batch(
    batch: IngestionBatch,
    registry: IngestionRegistry | None = None,
) -> ValidationResult:
    """
    Validate a complete ingestion batch.

    Public batch-level validation entry point.
    """
    return validate_batch(
        batch,
        registry=registry,
    )

def validate_ingestion_record(
    record: IngestionRecord,
    registry: IngestionRegistry | None = None,
) -> ValidationResult:
    """
    Validate a complete ingestion record.

    Public record-level validation entry point.
    """
    return validate_record(
        record,
        registry=registry,
    )
