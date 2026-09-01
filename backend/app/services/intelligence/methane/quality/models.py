from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    DUPLICATES = "duplicates"
    MISSING = "missing"
    OUTLIERS = "outliers"
    CALIBRATION = "calibration"
    CUSTODY = "custody"
    AUDIT = "audit"
    EVIDENCE = "evidence"


class QualityStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    NOT_ASSESSED = "not_assessed"


@dataclass(frozen=True)
class QualityIssue:
    """
    A single data-quality or QA/QC issue.
    """

    dimension: QualityDimension
    code: str
    message: str
    record_id: str | None = None
    field: str | None = None
    severity: str = "warning"
    details: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )


@dataclass(frozen=True)
class QualityAssessment:
    """
    Result of one quality assessment.
    """

    dimension: QualityDimension
    status: QualityStatus
    score: float | None = None
    issues: tuple[QualityIssue, ...] = ()

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def passed(self) -> bool:
        return self.status == QualityStatus.PASS


@dataclass(frozen=True)
class QualityScore:
    """
    Aggregated data-quality score.
    """

    overall: float
    dimensions: Mapping[
        QualityDimension,
        float,
    ] = dataclass_field(default_factory=dict)

    @property
    def dimension_count(self) -> int:
        return len(self.dimensions)


@dataclass(frozen=True)
class AuditEvent:
    """
    Immutable audit-trail event.
    """

    event_id: str
    event_type: str
    timestamp: datetime
    actor: str
    action: str
    description: str = ""
    record_id: str | None = None
    batch_id: str | None = None
    details: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EvidenceRecord:
    """
    Evidence supporting a QA/QC decision.
    """

    evidence_id: str
    evidence_type: str
    source: str
    captured_at: datetime
    description: str = ""
    record_id: str | None = None
    uri: str | None = None
    checksum: str | None = None
    metadata: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )


@dataclass(frozen=True)
class CalibrationRecord:
    """
    Instrument calibration record.
    """

    calibration_id: str
    instrument_id: str
    calibrated_at: datetime
    performed_by: str
    valid_until: datetime | None = None
    method: str | None = None
    certificate_reference: str | None = None
    passed: bool = True
    details: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )


@dataclass(frozen=True)
class CustodyEvent:
    """
    Chain-of-custody event for data or evidence.
    """

    event_id: str
    item_id: str
    timestamp: datetime
    actor: str
    action: str
    location: str | None = None
    checksum: str | None = None
    details: Mapping[str, Any] = dataclass_field(
        default_factory=dict
    )
