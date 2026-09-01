from __future__ import annotations

from typing import Any, Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_consistency(
    records: tuple[Mapping[str, Any], ...],
    *,
    field_types: Mapping[str, type] | None = None,
    allowed_values: Mapping[str, tuple[Any, ...]] | None = None,
) -> QualityAssessment:
    """
    Assess consistency of configured fields across records.

    Checks:
    - expected field types
    - configured allowed values
    - missing configured fields
    - invalid record structure

    Source records are never modified.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    field_types = field_types or {}
    allowed_values = allowed_values or {}

    configured_fields = (
        set(field_types)
        | set(allowed_values)
    )

    if not records or not configured_fields:
        return QualityAssessment(
            dimension=QualityDimension.CONSISTENCY,
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
                    dimension=QualityDimension.CONSISTENCY,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(record_index),
                )
            )
            continue

        for field_name in configured_fields:
            if field_name not in record:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CONSISTENCY,
                        code="missing_field",
                        message=f"configured field is missing: {field_name}",
                        record_id=str(record_index),
                        field=field_name,
                    )
                )
                continue

            value = record[field_name]
            checks += 1

            expected_type = field_types.get(field_name)

            if expected_type is not None and not isinstance(
                value,
                expected_type,
            ):
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CONSISTENCY,
                        code="inconsistent_type",
                        message=(
                            f"value must be {expected_type.__name__}"
                        ),
                        record_id=str(record_index),
                        field=field_name,
                        details={
                            "expected_type": expected_type.__name__,
                            "actual_type": type(value).__name__,
                        },
                    )
                )
                continue

            allowed = allowed_values.get(field_name)

            if allowed is not None and value not in allowed:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CONSISTENCY,
                        code="invalid_allowed_value",
                        message="value is not in the configured allowed values",
                        record_id=str(record_index),
                        field=field_name,
                        details={
                            "value": value,
                            "allowed_values": allowed,
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
        dimension=QualityDimension.CONSISTENCY,
        status=status,
        score=score,
        issues=tuple(issues),
    )
