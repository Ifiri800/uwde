from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_completeness(
    records: Sequence[Mapping[str, Any]],
    required_fields: Sequence[str],
) -> QualityAssessment:
    """
    Assess presence of required fields across source records.

    Completeness measures field availability. Structural validity is
    reported separately as a quality issue and does not artificially
    reduce the completeness denominator.
    """

    issues: list[QualityIssue] = []

    if not isinstance(records, (list, tuple)):
        issues.append(
            QualityIssue(
                dimension=QualityDimension.COMPLETENESS,
                code="invalid_records",
                message="records must be a list or tuple",
            )
        )
        return QualityAssessment(
            dimension=QualityDimension.COMPLETENESS,
            status=QualityStatus.FAIL,
            score=0.0,
            issues=tuple(issues),
        )

    if not isinstance(required_fields, (list, tuple)):
        issues.append(
            QualityIssue(
                dimension=QualityDimension.COMPLETENESS,
                code="invalid_required_fields",
                message="required_fields must be a list or tuple",
            )
        )
        return QualityAssessment(
            dimension=QualityDimension.COMPLETENESS,
            status=QualityStatus.FAIL,
            score=0.0,
            issues=tuple(issues),
        )

    fields = tuple(
        field
        for field in required_fields
        if isinstance(field, str) and field.strip()
    )

    total_cells = len(records) * len(fields)

    if total_cells == 0:
        return QualityAssessment(
            dimension=QualityDimension.COMPLETENESS,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
            issues=(),
        )

    present_cells = 0

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.COMPLETENESS,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(index),
                )
            )

            # Invalid structure is reported separately. It does not
            # count as a missing field for completeness scoring.
            continue

        for field_name in fields:
            if field_name in record:
                present_cells += 1
            else:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.COMPLETENESS,
                        code="missing_required_field",
                        message=(
                            f"required field is missing: {field_name}"
                        ),
                        record_id=str(index),
                        field=field_name,
                    )
                )

    invalid_record_count = sum(
        1
        for record in records
        if not isinstance(record, Mapping)
    )

    valid_records = len(records) - invalid_record_count

    if valid_records == 0:
        score = 0.0
    else:
        score = (present_cells / total_cells) * 100.0

    if score == 100.0 and not invalid_record_count:
        status = QualityStatus.PASS
    elif score >= 50.0:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.FAIL

    return QualityAssessment(
        dimension=QualityDimension.COMPLETENESS,
        status=status,
        score=score,
        issues=tuple(issues),
    )
