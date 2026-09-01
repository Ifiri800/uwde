from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Any, Mapping

from .models import (
    AuditEvent,
    CalibrationRecord,
    CustodyEvent,
    EvidenceRecord,
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityScore,
    QualityStatus,
)


class QualityValidationError(ValueError):
    """Raised when Layer 6 quality data fails validation."""


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


def _issue(
    field: str,
    message: str,
) -> ValidationIssue:
    return ValidationIssue(
        field=field,
        message=message,
    )


def _validate_non_empty(
    value: object,
    field: str,
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(value, str):
        issues.append(
            _issue(field, "must be a string")
        )
    elif not value.strip():
        issues.append(
            _issue(field, "is required")
        )


def validate_quality_issue(
    issue: QualityIssue,
) -> ValidationResult:
    if not isinstance(issue, QualityIssue):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "issue",
                    "must be QualityIssue",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not isinstance(
        issue.dimension,
        QualityDimension,
    ):
        issues.append(
            _issue(
                "dimension",
                "must be QualityDimension",
            )
        )

    _validate_non_empty(
        issue.code,
        "code",
        issues,
    )

    _validate_non_empty(
        issue.message,
        "message",
        issues,
    )

    if issue.record_id is not None:
        _validate_non_empty(
            issue.record_id,
            "record_id",
            issues,
        )

    if issue.field is not None:
        _validate_non_empty(
            issue.field,
            "field",
            issues,
        )

    _validate_non_empty(
        issue.severity,
        "severity",
        issues,
    )

    if not isinstance(issue.details, Mapping):
        issues.append(
            _issue(
                "details",
                "must be a mapping",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_quality_assessment(
    assessment: QualityAssessment,
) -> ValidationResult:
    if not isinstance(
        assessment,
        QualityAssessment,
    ):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "assessment",
                    "must be QualityAssessment",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not isinstance(
        assessment.dimension,
        QualityDimension,
    ):
        issues.append(
            _issue(
                "dimension",
                "must be QualityDimension",
            )
        )

    if not isinstance(
        assessment.status,
        QualityStatus,
    ):
        issues.append(
            _issue(
                "status",
                "must be QualityStatus",
            )
        )

    if assessment.score is not None:
        if not isinstance(
            assessment.score,
            (int, float),
        ):
            issues.append(
                _issue(
                    "score",
                    "must be numeric",
                )
            )
        elif not isfinite(float(assessment.score)):
            issues.append(
                _issue(
                    "score",
                    "must be finite",
                )
            )
        elif not 0.0 <= float(assessment.score) <= 1.0:
            issues.append(
                _issue(
                    "score",
                    "must be between 0 and 1",
                )
            )

    if not isinstance(assessment.issues, tuple):
        issues.append(
            _issue(
                "issues",
                "must be a tuple",
            )
        )
    else:
        for index, issue in enumerate(
            assessment.issues
        ):
            result = validate_quality_issue(issue)

            issues.extend(
                _issue(
                    f"issues[{index}].{item.field}",
                    item.message,
                )
                for item in result.issues
            )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_quality_score(
    score: QualityScore,
) -> ValidationResult:
    if not isinstance(score, QualityScore):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "score",
                    "must be QualityScore",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    if not isinstance(
        score.overall,
        (int, float),
    ):
        issues.append(
            _issue(
                "overall",
                "must be numeric",
            )
        )
    elif not isfinite(float(score.overall)):
        issues.append(
            _issue(
                "overall",
                "must be finite",
            )
        )
    elif not 0.0 <= float(score.overall) <= 1.0:
        issues.append(
            _issue(
                "overall",
                "must be between 0 and 1",
            )
        )

    if not isinstance(
        score.dimensions,
        Mapping,
    ):
        issues.append(
            _issue(
                "dimensions",
                "must be a mapping",
            )
        )
    else:
        for dimension, value in score.dimensions.items():
            if not isinstance(
                dimension,
                QualityDimension,
            ):
                issues.append(
                    _issue(
                        "dimensions",
                        "keys must be QualityDimension",
                    )
                )

            if not isinstance(
                value,
                (int, float),
            ):
                issues.append(
                    _issue(
                        "dimensions",
                        "values must be numeric",
                    )
                )
            elif not isfinite(float(value)):
                issues.append(
                    _issue(
                        "dimensions",
                        "values must be finite",
                    )
                )
            elif not 0.0 <= float(value) <= 1.0:
                issues.append(
                    _issue(
                        "dimensions",
                        "values must be between 0 and 1",
                    )
                )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_audit_event(
    event: AuditEvent,
) -> ValidationResult:
    if not isinstance(event, AuditEvent):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "event",
                    "must be AuditEvent",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    _validate_non_empty(
        event.event_id,
        "event_id",
        issues,
    )

    _validate_non_empty(
        event.event_type,
        "event_type",
        issues,
    )

    if not isinstance(
        event.timestamp,
        datetime,
    ):
        issues.append(
            _issue(
                "timestamp",
                "must be datetime",
            )
        )

    _validate_non_empty(
        event.actor,
        "actor",
        issues,
    )

    _validate_non_empty(
        event.action,
        "action",
        issues,
    )

    if not isinstance(event.details, Mapping):
        issues.append(
            _issue(
                "details",
                "must be a mapping",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_evidence_record(
    evidence: EvidenceRecord,
) -> ValidationResult:
    if not isinstance(
        evidence,
        EvidenceRecord,
    ):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "evidence",
                    "must be EvidenceRecord",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    _validate_non_empty(
        evidence.evidence_id,
        "evidence_id",
        issues,
    )

    _validate_non_empty(
        evidence.evidence_type,
        "evidence_type",
        issues,
    )

    _validate_non_empty(
        evidence.source,
        "source",
        issues,
    )

    if not isinstance(
        evidence.captured_at,
        datetime,
    ):
        issues.append(
            _issue(
                "captured_at",
                "must be datetime",
            )
        )

    if not isinstance(
        evidence.metadata,
        Mapping,
    ):
        issues.append(
            _issue(
                "metadata",
                "must be a mapping",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_calibration_record(
    calibration: CalibrationRecord,
) -> ValidationResult:
    if not isinstance(
        calibration,
        CalibrationRecord,
    ):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "calibration",
                    "must be CalibrationRecord",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    _validate_non_empty(
        calibration.calibration_id,
        "calibration_id",
        issues,
    )

    _validate_non_empty(
        calibration.instrument_id,
        "instrument_id",
        issues,
    )

    if not isinstance(
        calibration.calibrated_at,
        datetime,
    ):
        issues.append(
            _issue(
                "calibrated_at",
                "must be datetime",
            )
        )

    _validate_non_empty(
        calibration.performed_by,
        "performed_by",
        issues,
    )

    if calibration.valid_until is not None:
        if not isinstance(
            calibration.valid_until,
            datetime,
        ):
            issues.append(
                _issue(
                    "valid_until",
                    "must be datetime",
                )
            )
        elif isinstance(
            calibration.calibrated_at,
            datetime,
        ) and calibration.valid_until < calibration.calibrated_at:
            issues.append(
                _issue(
                    "valid_until",
                    "cannot precede calibrated_at",
                )
            )

    if not isinstance(
        calibration.passed,
        bool,
    ):
        issues.append(
            _issue(
                "passed",
                "must be boolean",
            )
        )

    if not isinstance(
        calibration.details,
        Mapping,
    ):
        issues.append(
            _issue(
                "details",
                "must be a mapping",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def validate_custody_event(
    event: CustodyEvent,
) -> ValidationResult:
    if not isinstance(
        event,
        CustodyEvent,
    ):
        return ValidationResult(
            valid=False,
            issues=(
                _issue(
                    "event",
                    "must be CustodyEvent",
                ),
            ),
        )

    issues: list[ValidationIssue] = []

    _validate_non_empty(
        event.event_id,
        "event_id",
        issues,
    )

    _validate_non_empty(
        event.item_id,
        "item_id",
        issues,
    )

    if not isinstance(
        event.timestamp,
        datetime,
    ):
        issues.append(
            _issue(
                "timestamp",
                "must be datetime",
            )
        )

    _validate_non_empty(
        event.actor,
        "actor",
        issues,
    )

    _validate_non_empty(
        event.action,
        "action",
        issues,
    )

    if not isinstance(event.details, Mapping):
        issues.append(
            _issue(
                "details",
                "must be a mapping",
            )
        )

    return ValidationResult(
        valid=not issues,
        issues=tuple(issues),
    )


def require_valid(
    result: ValidationResult,
) -> None:
    """Raise QualityValidationError when validation fails."""
    if not result.valid:
        message = "; ".join(
            f"{issue.field}: {issue.message}"
            for issue in result.issues
        )
        raise QualityValidationError(message)
