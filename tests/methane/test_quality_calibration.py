from datetime import datetime, timezone, timedelta

from backend.app.services.intelligence.methane.quality.calibration import (
    assess_calibration,
)
from backend.app.services.intelligence.methane.quality.models import (
    CalibrationRecord,
    QualityDimension,
    QualityStatus,
)


NOW = datetime(
    2026,
    8,
    31,
    12,
    0,
    tzinfo=timezone.utc,
)


def calibration(
    instrument_id="INST-001",
    passed=True,
    calibrated_at=NOW - timedelta(days=10),
    valid_until=NOW + timedelta(days=20),
):
    return CalibrationRecord(
        calibration_id="CAL-001",
        instrument_id=instrument_id,
        calibrated_at=calibrated_at,
        performed_by="Technician",
        valid_until=valid_until,
        method="Reference standard",
        certificate_reference="CERT-001",
        passed=passed,
    )


def test_valid_calibration_passes():
    result = assess_calibration(
        records=(calibration(),),
        now=NOW,
    )

    assert result.dimension == QualityDimension.CALIBRATION
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_failed_calibration_is_detected():
    result = assess_calibration(
        records=(calibration(passed=False),),
        now=NOW,
    )

    assert result.status == QualityStatus.FAIL
    assert result.issue_count == 1
    assert result.issues[0].code == "calibration_failed"


def test_expired_calibration_is_detected():
    result = assess_calibration(
        records=(
            calibration(
                valid_until=NOW - timedelta(days=1)
            ),
        ),
        now=NOW,
    )

    assert result.status == QualityStatus.FAIL
    assert result.issue_count == 1
    assert result.issues[0].code == "calibration_expired"


def test_missing_expiry_is_allowed():
    result = assess_calibration(
        records=(
            calibration(valid_until=None),
        ),
        now=NOW,
    )

    assert result.status == QualityStatus.PASS
    assert result.score == 100.0


def test_missing_instrument_id_is_detected():
    record = CalibrationRecord(
        calibration_id="CAL-001",
        instrument_id="",
        calibrated_at=NOW,
        performed_by="Technician",
        passed=True,
    )

    result = assess_calibration(
        records=(record,),
        now=NOW,
    )

    assert result.status == QualityStatus.FAIL
    assert result.issue_count == 1
    assert result.issues[0].code == "invalid_instrument"


def test_empty_records_are_not_assessed():
    result = assess_calibration(
        records=(),
        now=NOW,
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_invalid_record_type_is_rejected():
    result = assess_calibration(
        records=("invalid",),
        now=NOW,
    )

    assert result.status == QualityStatus.FAIL
    assert result.issue_count == 1


def test_naive_now_is_rejected():
    try:
        assess_calibration(
            records=(calibration(),),
            now=datetime(2026, 8, 31, 12, 0),
        )
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_naive_calibration_timestamp_is_detected():
    record = CalibrationRecord(
        calibration_id="CAL-001",
        instrument_id="INST-001",
        calibrated_at=datetime(2026, 8, 1, 12, 0),
        performed_by="Technician",
        passed=True,
    )

    result = assess_calibration(
        records=(record,),
        now=NOW,
    )

    assert result.status == QualityStatus.FAIL
    assert result.issue_count == 1
