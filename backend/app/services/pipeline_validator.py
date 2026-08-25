from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationIssue:
    """
    A single pipeline validation issue.
    """

    code: str
    message: str
    severity: str = "error"
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "field": self.field,
        }


@dataclass
class PipelineValidationResult:
    """
    Result of validating a pipeline output.
    """

    valid: bool
    record_count: int
    issues: list[ValidationIssue] = field(
        default_factory=list
    )

    @property
    def errors(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "error"
        ]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [
            issue
            for issue in self.issues
            if issue.severity == "warning"
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "record_count": self.record_count,
            "issues": [
                issue.to_dict()
                for issue in self.issues
            ],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


def validate_pipeline_input(
    url: str,
    instruction: str,
) -> PipelineValidationResult:
    """
    Validate basic pipeline inputs.
    """

    issues: list[ValidationIssue] = []

    if not str(url).strip():
        issues.append(
            ValidationIssue(
                code="EMPTY_URL",
                message="URL is required.",
            )
        )

    if not str(instruction).strip():
        issues.append(
            ValidationIssue(
                code="EMPTY_INSTRUCTION",
                message="Instruction is required.",
            )
        )

    return PipelineValidationResult(
        valid=not any(
            issue.severity == "error"
            for issue in issues
        ),
        record_count=0,
        issues=issues,
    )


def validate_pipeline_records(
    records: list[dict[str, Any]],
    required_fields: set[str] | None = None,
) -> PipelineValidationResult:
    """
    Validate extracted records.

    Checks:

    - records must be a list
    - every record must be a dictionary
    - records must not be empty when supplied
    - required fields must exist
    - required fields must not contain empty values
    """

    issues: list[ValidationIssue] = []

    if not isinstance(records, list):
        issues.append(
            ValidationIssue(
                code="INVALID_RECORD_CONTAINER",
                message="Records must be provided as a list.",
            )
        )

        return PipelineValidationResult(
            valid=False,
            record_count=0,
            issues=issues,
        )

    if not records:
        issues.append(
            ValidationIssue(
                code="NO_RECORDS",
                message="Extraction returned no records.",
                severity="warning",
            )
        )

    required_fields = required_fields or set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(
                ValidationIssue(
                    code="INVALID_RECORD",
                    message=(
                        f"Record {index} is not a dictionary."
                    ),
                )
            )
            continue

        for field_name in required_fields:
            if field_name not in record:
                issues.append(
                    ValidationIssue(
                        code="MISSING_REQUIRED_FIELD",
                        message=(
                            f"Record {index} is missing "
                            f"required field '{field_name}'."
                        ),
                        field=field_name,
                    )
                )
                continue

            value = record.get(field_name)

            if value is None or (
                isinstance(value, str)
                and not value.strip()
            ):
                issues.append(
                    ValidationIssue(
                        code="EMPTY_REQUIRED_FIELD",
                        message=(
                            f"Record {index} has an empty "
                            f"required field '{field_name}'."
                        ),
                        field=field_name,
                    )
                )

    return PipelineValidationResult(
        valid=not any(
            issue.severity == "error"
            for issue in issues
        ),
        record_count=len(records),
        issues=issues,
    )


def validate_pipeline_output(
    records: list[dict[str, Any]],
    required_fields: set[str] | None = None,
) -> PipelineValidationResult:
    """
    Public validation entry point for pipeline output.
    """

    return validate_pipeline_records(
        records=records,
        required_fields=required_fields,
    )