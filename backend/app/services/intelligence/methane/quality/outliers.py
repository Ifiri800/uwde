from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def _numeric_values(
    records: tuple[Mapping[str, Any], ...],
    field_name: str,
) -> tuple[list[tuple[int, float]], list[QualityIssue]]:
    values: list[tuple[int, float]] = []
    issues: list[QualityIssue] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        if field_name not in record:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="missing_value",
                    message=f"field is missing: {field_name}",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        value = record[field_name]

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="missing_value",
                    message=f"field contains a missing value: {field_name}",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        if isinstance(value, bool):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="non_numeric_value",
                    message=f"field contains a non-numeric value: {field_name}",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="non_numeric_value",
                    message=f"field contains a non-numeric value: {field_name}",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        if not isfinite(numeric_value):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.OUTLIERS,
                    code="non_finite_value",
                    message=f"field contains a non-finite value: {field_name}",
                    record_id=str(index),
                    field=field_name,
                )
            )
            continue

        values.append((index, numeric_value))

    return values, issues


def _percentile(
    values: list[float],
    percentile: float,
) -> float:
    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower

    return (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction
    )


def assess_outliers(
    records: tuple[Mapping[str, Any], ...],
    *,
    fields: tuple[str, ...] = (),
    iqr_multiplier: float = 1.5,
) -> QualityAssessment:
    """
    Detect statistical outliers using the IQR method.

    Values outside:

        Q1 - multiplier * IQR
        Q3 + multiplier * IQR

    are classified as outliers.

    Invalid, missing, and non-finite values are reported separately.
    Source records are never modified.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    if not isinstance(fields, tuple):
        raise TypeError("fields must be a tuple")

    if not isinstance(iqr_multiplier, (int, float)):
        raise TypeError("iqr_multiplier must be numeric")

    if iqr_multiplier <= 0:
        raise ValueError("iqr_multiplier must be greater than zero")

    if not records or not fields:
        return QualityAssessment(
            dimension=QualityDimension.OUTLIERS,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    all_issues: list[QualityIssue] = []
    outlier_count = 0
    assessed_field_count = 0

    for field_name in fields:
        if not isinstance(field_name, str):
            raise TypeError("field names must be strings")

        values, issues = _numeric_values(
            records,
            field_name,
        )

        all_issues.extend(issues)

        if len(values) < 3:
            continue

        assessed_field_count += 1

        numeric_values = [value for _, value in values]

        q1 = _percentile(numeric_values, 0.25)
        q3 = _percentile(numeric_values, 0.75)
        iqr = q3 - q1

        lower_bound = q1 - (iqr_multiplier * iqr)
        upper_bound = q3 + (iqr_multiplier * iqr)

        for record_index, value in values:
            if value < lower_bound or value > upper_bound:
                outlier_count += 1

                all_issues.append(
                    QualityIssue(
                        dimension=QualityDimension.OUTLIERS,
                        code="outlier_value",
                        message=f"outlier detected in field: {field_name}",
                        record_id=str(record_index),
                        field=field_name,
                        details={
                            "value": value,
                            "q1": q1,
                            "q3": q3,
                            "iqr": iqr,
                            "lower_bound": lower_bound,
                            "upper_bound": upper_bound,
                        },
                    )
                )

    if assessed_field_count == 0:
        if all_issues:
            return QualityAssessment(
                dimension=QualityDimension.OUTLIERS,
                status=QualityStatus.WARNING,
                score=100.0,
                issues=tuple(all_issues),
            )

        return QualityAssessment(
            dimension=QualityDimension.OUTLIERS,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    total_values = sum(
        1
        for field_name in fields
        for record in records
        if isinstance(record, Mapping)
        and field_name in record
        and record[field_name] is not None
        and not (
            isinstance(record[field_name], str)
            and not record[field_name].strip()
        )
    )

    score = round(
        max(
            0.0,
            ((total_values - outlier_count) / total_values)
            * 100.0,
        ),
        2,
    ) if total_values else 0.0

    if not all_issues:
        status = QualityStatus.PASS
    elif score >= 50.0:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.FAIL

    return QualityAssessment(
        dimension=QualityDimension.OUTLIERS,
        status=status,
        score=score,
        issues=tuple(all_issues),
    )
