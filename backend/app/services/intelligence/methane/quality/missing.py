from __future__ import annotations

from typing import Any, Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def _is_missing(value: Any) -> bool:
    """
    Determine whether a value should be treated as missing.

    Missing values are:
    - None
    - empty strings
    - whitespace-only strings
    """

    if value is None:
        return True

    if isinstance(value, str) and not value.strip():
        return True

    return False


def assess_missing(
    records: tuple[Mapping[str, Any], ...],
    *,
    fields: tuple[str, ...] = (),
) -> QualityAssessment:
    """
    Assess missing values in configured fields.

    Missing fields, None values, empty strings, and whitespace-only
    strings are reported as missing.

    Source records are never modified.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    if not fields or not records:
        return QualityAssessment(
            dimension=QualityDimension.MISSING,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []
    total_checks = 0
    missing_count = 0

    for record_index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.MISSING,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(record_index),
                )
            )
            continue

        for field_name in fields:
            total_checks += 1

            if field_name not in record:
                missing_count += 1

                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.MISSING,
                        code="missing_field",
                        message=f"field is missing: {field_name}",
                        record_id=str(record_index),
                        field=field_name,
                    )
                )
                continue

            if _is_missing(record[field_name]):
                missing_count += 1

                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.MISSING,
                        code="missing_value",
                        message=f"field contains a missing value: {field_name}",
                        record_id=str(record_index),
                        field=field_name,
                    )
                )

    if total_checks == 0:
        score = 0.0
    else:
        score = round(
            ((total_checks - missing_count) / total_checks)
            * 100.0,
            2,
        )

    if not issues:
        status = QualityStatus.PASS
    elif score >= 50.0:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.FAIL

    return QualityAssessment(
        dimension=QualityDimension.MISSING,
        status=status,
        score=score,
        issues=tuple(issues),
    )
