from __future__ import annotations

from typing import Any, Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def _freeze(value: Any) -> Any:
    """
    Convert common mutable values into deterministic hashable values.
    """

    if isinstance(value, Mapping):
        return tuple(
            sorted(
                (key, _freeze(item))
                for key, item in value.items()
            )
        )

    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, set):
        return tuple(sorted(_freeze(item) for item in value))

    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


def assess_duplicates(
    records: tuple[Mapping[str, Any], ...],
    *,
    identity_fields: tuple[str, ...] = (),
    enabled: bool = True,
) -> QualityAssessment:
    """
    Detect duplicate records.

    When identity_fields are supplied, only those fields determine
    record identity. Otherwise the complete record is used.

    Source records are never modified.
    """

    if not isinstance(records, tuple):
        raise TypeError("records must be a tuple")

    if not isinstance(enabled, bool):
        raise TypeError("enabled must be a boolean")

    if not enabled or not records:
        return QualityAssessment(
            dimension=QualityDimension.DUPLICATES,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    seen: dict[Any, int] = {}
    duplicate_indices: list[int] = []
    issues: list[QualityIssue] = []

    valid_count = 0

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.DUPLICATES,
                    code="invalid_record",
                    message="record must be a mapping",
                    record_id=str(index),
                )
            )
            continue

        valid_count += 1

        if identity_fields:
            key = tuple(
                _freeze(record.get(field))
                for field in identity_fields
            )
        else:
            key = _freeze(record)

        if key in seen:
            duplicate_indices.append(index)

            issues.append(
                QualityIssue(
                    dimension=QualityDimension.DUPLICATES,
                    code="duplicate_record",
                    message="duplicate record detected",
                    record_id=str(index),
                    details={
                        "original_record_index": seen[key],
                    },
                )
            )
        else:
            seen[key] = index

    if not valid_count:
        return QualityAssessment(
            dimension=QualityDimension.DUPLICATES,
            status=QualityStatus.WARNING,
            score=0.0,
            issues=tuple(issues),
        )

    score = round(
        ((valid_count - len(duplicate_indices)) / valid_count)
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
        dimension=QualityDimension.DUPLICATES,
        status=status,
        score=score,
        issues=tuple(issues),
    )
