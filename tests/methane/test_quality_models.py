from datetime import datetime, timezone

from backend.app.services.intelligence.methane.quality.errors import (
    QualityAssessmentError,
    QualityAuditError,
    QualityCalibrationError,
    QualityEvidenceError,
    QualityError,
    QualityValidationError,
)
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


def test_quality_dimension_values():
    assert QualityDimension.COMPLETENESS.value == "completeness"
    assert QualityDimension.ACCURACY.value == "accuracy"
    assert QualityDimension.CONSISTENCY.value == "consistency"


def test_quality_status_values():
    assert QualityStatus.PASS.value == "pass"
    assert QualityStatus.WARNING.value == "warning"
    assert QualityStatus.FAIL.value == "fail"


def test_quality_issue():
    issue = QualityIssue(
        dimension=QualityDimension.COMPLETENESS,
        code="MISSING_RECORD",
        message="Expected record is missing.",
        record_id="REC-001",
    )

    assert issue.record_id == "REC-001"
    assert issue.dimension == QualityDimension.COMPLETENESS


def test_quality_assessment():
    assessment = QualityAssessment(
        dimension=QualityDimension.ACCURACY,
        status=QualityStatus.PASS,
        score=98.5,
    )

    assert assessment.passed
    assert assessment.issue_count == 0


def test_quality_assessment_with_issue():
    issue = QualityIssue(
        dimension=QualityDimension.OUTLIERS,
        code="OUTLIER",
        message="Value outside expected range.",
    )

    assessment = QualityAssessment(
        dimension=QualityDimension.OUTLIERS,
        status=QualityStatus.WARNING,
        issues=(issue,),
    )

    assert not assessment.passed
    assert assessment.issue_count == 1


def test_quality_score():
    score = QualityScore(
        overall=92.0,
        dimensions={
            QualityDimension.COMPLETENESS: 95.0,
            QualityDimension.ACCURACY: 89.0,
        },
    )

    assert score.overall == 92.0
    assert score.dimension_count == 2


def test_audit_event():
    timestamp = datetime.now(timezone.utc)

    event = AuditEvent(
        event_id="AUD-001",
        event_type="quality_assessment",
        timestamp=timestamp,
        actor="system",
        action="assess",
    )

    assert event.event_id == "AUD-001"
    assert event.actor == "system"


def test_evidence_record():
    timestamp = datetime.now(timezone.utc)

    evidence = EvidenceRecord(
        evidence_id="EVD-001",
        evidence_type="measurement",
        source="sensor",
        captured_at=timestamp,
    )

    assert evidence.evidence_id == "EVD-001"
    assert evidence.source == "sensor"


def test_calibration_record():
    timestamp = datetime.now(timezone.utc)

    calibration = CalibrationRecord(
        calibration_id="CAL-001",
        instrument_id="INST-001",
        calibrated_at=timestamp,
        performed_by="technician",
    )

    assert calibration.passed
    assert calibration.instrument_id == "INST-001"


def test_custody_event():
    timestamp = datetime.now(timezone.utc)

    event = CustodyEvent(
        event_id="CUS-001",
        item_id="DATA-001",
        timestamp=timestamp,
        actor="operator",
        action="transfer",
    )

    assert event.item_id == "DATA-001"
    assert event.action == "transfer"


def test_quality_errors_inherit_from_base():
    assert issubclass(QualityValidationError, QualityError)
    assert issubclass(QualityAssessmentError, QualityError)
    assert issubclass(QualityEvidenceError, QualityError)
    assert issubclass(QualityAuditError, QualityError)
    assert issubclass(QualityCalibrationError, QualityError)
