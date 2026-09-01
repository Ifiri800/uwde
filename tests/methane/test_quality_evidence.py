from datetime import datetime, timezone

from backend.app.services.intelligence.methane.quality.evidence import (
    assess_evidence,
)
from backend.app.services.intelligence.methane.quality.models import (
    EvidenceRecord,
    QualityDimension,
    QualityStatus,
)


T0 = datetime(
    2026, 8, 1, 10, 0, tzinfo=timezone.utc
)


def evidence(
    evidence_id="EV-001",
    evidence_type="measurement",
    source="sensor-01",
    captured_at=T0,
    description="Measurement evidence",
    record_id="REC-001",
    uri="https://example.com/evidence/1",
    checksum="abc123",
):
    return EvidenceRecord(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        source=source,
        captured_at=captured_at,
        description=description,
        record_id=record_id,
        uri=uri,
        checksum=checksum,
    )


def test_valid_evidence_passes():
    result = assess_evidence(
        evidence_records=(evidence(),)
    )

    assert result.dimension == QualityDimension.EVIDENCE
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_empty_evidence_is_not_assessed():
    result = assess_evidence(
        evidence_records=()
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_invalid_evidence_type_is_detected():
    result = assess_evidence(
        evidence_records=("invalid",)
    )

    assert result.status == QualityStatus.FAIL


def test_missing_evidence_id_is_detected():
    result = assess_evidence(
        evidence_records=(
            evidence(evidence_id=""),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_evidence_id"
        for issue in result.issues
    )


def test_missing_evidence_type_is_detected():
    result = assess_evidence(
        evidence_records=(
            evidence(evidence_type=""),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_evidence_type"
        for issue in result.issues
    )


def test_missing_source_is_detected():
    result = assess_evidence(
        evidence_records=(
            evidence(source=""),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_source"
        for issue in result.issues
    )


def test_naive_capture_timestamp_is_detected():
    result = assess_evidence(
        evidence_records=(
            evidence(
                captured_at=datetime(
                    2026, 8, 1, 10, 0
                )
            ),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_timestamp"
        for issue in result.issues
    )


def test_duplicate_evidence_ids_are_detected():
    result = assess_evidence(
        evidence_records=(
            evidence(),
            evidence(),
        )
    )

    assert result.status == QualityStatus.WARNING
    assert any(
        issue.code == "duplicate_evidence_id"
        for issue in result.issues
    )


def test_missing_checksum_is_warning():
    result = assess_evidence(
        evidence_records=(
            evidence(checksum=None),
        )
    )

    assert result.status == QualityStatus.WARNING
    assert any(
        issue.code == "missing_checksum"
        for issue in result.issues
    )


def test_missing_uri_is_warning():
    result = assess_evidence(
        evidence_records=(
            evidence(uri=None),
        )
    )

    assert result.status == QualityStatus.WARNING
    assert any(
        issue.code == "missing_uri"
        for issue in result.issues
    )


def test_record_traceability_is_preserved():
    result = assess_evidence(
        evidence_records=(
            evidence(record_id="REC-777"),
        )
    )

    assert result.status == QualityStatus.PASS
    assert result.issue_count == 0
