from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quality.models import (
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
from backend.app.services.intelligence.methane.quality.validation import (
    QualityValidationError,
    require_valid,
    validate_audit_event,
    validate_calibration_record,
    validate_custody_event,
    validate_evidence_record,
    validate_quality_assessment,
    validate_quality_issue,
    validate_quality_score,
)


NOW = datetime.now(timezone.utc)


def issue() -> QualityIssue:
    return QualityIssue(
        dimension=QualityDimension.ACCURACY,
        code="ACC001",
        message="Measurement within expected tolerance",
    )


def test_validate_quality_issue_accepts_valid_issue():
    result = validate_quality_issue(issue())

    assert result.valid
    assert result.issue_count == 0


def test_validate_quality_issue_rejects_wrong_type():
    result = validate_quality_issue("invalid")

    assert not result.valid


def test_validate_quality_issue_rejects_missing_code():
    value = QualityIssue(
        dimension=QualityDimension.ACCURACY,
        code="",
        message="message",
    )

    result = validate_quality_issue(value)

    assert not result.valid
    assert any(
        item.field == "code"
        for item in result.issues
    )


def test_validate_quality_assessment_accepts_valid():
    value = QualityAssessment(
        dimension=QualityDimension.ACCURACY,
        status=QualityStatus.PASS,
        score=0.95,
        issues=(issue(),),
    )

    result = validate_quality_assessment(value)

    assert result.valid


def test_validate_quality_assessment_rejects_score_above_one():
    value = QualityAssessment(
        dimension=QualityDimension.ACCURACY,
        status=QualityStatus.PASS,
        score=1.1,
    )

    result = validate_quality_assessment(value)

    assert not result.valid


def test_validate_quality_score_accepts_valid():
    value = QualityScore(
        overall=0.9,
        dimensions={
            QualityDimension.ACCURACY: 0.9,
            QualityDimension.COMPLETENESS: 0.95,
        },
    )

    result = validate_quality_score(value)

    assert result.valid


def test_validate_quality_score_rejects_invalid_dimension_key():
    value = QualityScore(
        overall=0.9,
        dimensions={"accuracy": 0.9},
    )

    result = validate_quality_score(value)

    assert not result.valid


def test_validate_audit_event_accepts_valid():
    value = AuditEvent(
        event_id="audit-001",
        event_type="quality_assessment",
        timestamp=NOW,
        actor="system",
        action="assess",
    )

    result = validate_audit_event(value)

    assert result.valid


def test_validate_evidence_record_accepts_valid():
    value = EvidenceRecord(
        evidence_id="evidence-001",
        evidence_type="measurement",
        source="sensor-001",
        captured_at=NOW,
    )

    result = validate_evidence_record(value)

    assert result.valid


def test_validate_calibration_record_accepts_valid():
    value = CalibrationRecord(
        calibration_id="cal-001",
        instrument_id="instrument-001",
        calibrated_at=NOW,
        performed_by="technician",
    )

    result = validate_calibration_record(value)

    assert result.valid


def test_validate_calibration_rejects_reverse_dates():
    value = CalibrationRecord(
        calibration_id="cal-001",
        instrument_id="instrument-001",
        calibrated_at=NOW,
        performed_by="technician",
        valid_until=NOW.replace(
            year=NOW.year - 1
        ),
    )

    result = validate_calibration_record(value)

    assert not result.valid


def test_validate_custody_event_accepts_valid():
    value = CustodyEvent(
        event_id="custody-001",
        item_id="sample-001",
        timestamp=NOW,
        actor="operator",
        action="transfer",
    )

    result = validate_custody_event(value)

    assert result.valid


def test_require_valid_raises_for_invalid_result():
    result = validate_quality_issue("invalid")

    with pytest.raises(QualityValidationError):
        require_valid(result)


def test_require_valid_accepts_valid_result():
    result = validate_quality_issue(issue())

    require_valid(result)
