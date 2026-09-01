from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    CalibrationRecord,
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_calibration(
    records: tuple[CalibrationRecord, ...],
    *,
    now: datetime,
) -> QualityAssessment:
    """
    Assess instrument calibration records for QA/QC compliance.

    Checks:
    - record type
    - instrument identification
    - calibration timestamp
    - timezone awareness
    - calibration pass/fail
    - calibration expiry
    - future calibration timestamps

    Calibration records are never modified.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    if not isinstance(now, datetime):
        raise TypeError("now must be a datetime")

    if now.tzinfo is None:
        raise ValueError(
            "now must be timezone-aware"
        )

    if not records:
        return QualityAssessment(
            dimension=QualityDimension.CALIBRATION,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []

    for index, record in enumerate(records):

        if not isinstance(record, CalibrationRecord):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="invalid_record",
                    message="record must be a CalibrationRecord",
                    record_id=str(index),
                    severity="error",
                )
            )
            continue

        record_id = record.calibration_id or str(index)

        if not isinstance(record.instrument_id, str):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="invalid_instrument",
                    message="instrument_id must be a string",
                    record_id=record_id,
                    field="instrument_id",
                    severity="error",
                )
            )

        elif not record.instrument_id.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="invalid_instrument",
                    message="instrument_id is required",
                    record_id=record_id,
                    field="instrument_id",
                    severity="error",
                )
            )

        calibrated_at = record.calibrated_at

        if not isinstance(calibrated_at, datetime):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="invalid_calibration_timestamp",
                    message="calibrated_at must be a datetime",
                    record_id=record_id,
                    field="calibrated_at",
                    severity="error",
                )
            )
            continue

        if calibrated_at.tzinfo is None:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="invalid_calibration_timestamp",
                    message="calibrated_at must be timezone-aware",
                    record_id=record_id,
                    field="calibrated_at",
                    severity="error",
                )
            )
            continue

        calibrated_at_utc = calibrated_at.astimezone(
            timezone.utc
        )

        now_utc = now.astimezone(timezone.utc)

        if calibrated_at_utc > now_utc:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="future_calibration",
                    message="calibration timestamp is in the future",
                    record_id=record_id,
                    field="calibrated_at",
                    severity="error",
                )
            )

        if not record.passed:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CALIBRATION,
                    code="calibration_failed",
                    message="instrument calibration did not pass",
                    record_id=record_id,
                    severity="error",
                )
            )

        if record.valid_until is not None:

            if not isinstance(record.valid_until, datetime):
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CALIBRATION,
                        code="invalid_valid_until",
                        message="valid_until must be a datetime or None",
                        record_id=record_id,
                        field="valid_until",
                        severity="error",
                    )
                )

            elif record.valid_until.tzinfo is None:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CALIBRATION,
                        code="invalid_valid_until",
                        message="valid_until must be timezone-aware",
                        record_id=record_id,
                        field="valid_until",
                        severity="error",
                    )
                )

            else:
                valid_until_utc = record.valid_until.astimezone(
                    timezone.utc
                )

                if valid_until_utc < now_utc:
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.CALIBRATION,
                            code="calibration_expired",
                            message="instrument calibration has expired",
                            record_id=record_id,
                            field="valid_until",
                            severity="error",
                        )
                    )

    total = len(records)

    failed = len(issues)

    score = round(
        max(
            0.0,
            ((total - failed) / total) * 100.0,
        ),
        2,
    )

    if not issues:
        status = QualityStatus.PASS
    else:
        status = QualityStatus.FAIL

    return QualityAssessment(
        dimension=QualityDimension.CALIBRATION,
        status=status,
        score=score,
        issues=tuple(issues),
    )
