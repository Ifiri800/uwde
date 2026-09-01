from __future__ import annotations

from numbers import Real
from typing import Any, Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_accuracy(
    records: tuple[Mapping[str, Any], ...],
    *,
    numeric_fields: tuple[str, ...] = (),
    minimums: Mapping[str, float] | None = None,
    maximums: Mapping[str, float] | None = None,
    reference_values: Mapping[str, float] | None = None,
    tolerances: Mapping[str, float] | None = None,
) -> QualityAssessment:
    """
    Assess numerical accuracy and configured value constraints.

    Checks include:
    - numeric type validity
    - minimum bounds
    - maximum bounds
    - reference-value tolerance

    The assessment reports issues without mutating source records.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    minimums = minimums or {}
    maximums = maximums or {}
    reference_values = reference_values or {}
    tolerances = tolerances or {}

    configured_fields = (
        set(numeric_fields)
        | set(minimums)
        | set(maximums)
        | set(reference_values)
        | set(tolerances)
    )

    if not records or not configured_fields:
        return QualityAssessment(
            dimension=QualityDimension.ACCURACY,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []
    checks = 0
    passed = 0

    for record_index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.ACCURACY,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(record_index),
                )
            )
            continue

        for field in configured_fields:
            if field not in record:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.ACCURACY,
                        code="missing_value",
                        message=f"field is missing: {field}",
                        record_id=str(record_index),
                        field=field,
                    )
                )
                continue

            value = record[field]
            checks += 1

            if field in numeric_fields and (
                not isinstance(value, Real)
                or isinstance(value, bool)
            ):
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.ACCURACY,
                        code="invalid_numeric",
                        message="value must be numeric",
                        record_id=str(record_index),
                        field=field,
                        details={"value": value},
                    )
                )
                continue

            if field in minimums:
                if not isinstance(value, Real) or isinstance(value, bool):
                    continue

                if value < minimums[field]:
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.ACCURACY,
                            code="below_minimum",
                            message="value is below configured minimum",
                            record_id=str(record_index),
                            field=field,
                            details={
                                "value": value,
                                "minimum": minimums[field],
                            },
                        )
                    )
                    continue

            if field in maximums:
                if not isinstance(value, Real) or isinstance(value, bool):
                    continue

                if value > maximums[field]:
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.ACCURACY,
                            code="above_maximum",
                            message="value exceeds configured maximum",
                            record_id=str(record_index),
                            field=field,
                            details={
                                "value": value,
                                "maximum": maximums[field],
                            },
                        )
                    )
                    continue

            if field in reference_values:
                if not isinstance(value, Real) or isinstance(value, bool):
                    continue

                tolerance = tolerances.get(field, 0.0)
                reference = reference_values[field]

                if abs(value - reference) > tolerance:
                    issues.append(
                        QualityIssue(
                            dimension=QualityDimension.ACCURACY,
                            code="outside_tolerance",
                            message="value is outside configured tolerance",
                            record_id=str(record_index),
                            field=field,
                            details={
                                "value": value,
                                "reference": reference,
                                "tolerance": tolerance,
                            },
                        )
                    )
                    continue

            passed += 1

    if checks == 0:
        score = 0.0
    else:
        score = round((passed / checks) * 100.0, 2)

    if not issues:
        status = QualityStatus.PASS
    elif score >= 50.0:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.FAIL

    return QualityAssessment(
        dimension=QualityDimension.ACCURACY,
        status=status,
        score=score,
        issues=tuple(issues),
    )
