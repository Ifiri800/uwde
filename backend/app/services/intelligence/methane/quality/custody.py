from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    CustodyEvent,
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_custody(
    events: tuple[CustodyEvent, ...],
    item_id: str,
) -> QualityAssessment:
    """
    Assess chain-of-custody integrity for a data or evidence item.

    Checks:
    - item identity
    - event validity
    - actor
    - action
    - timestamp validity
    - chronological ordering
    - duplicate events

    Source events are never modified.
    """

    if not isinstance(events, tuple):
        raise TypeError("events must be a tuple")

    if not isinstance(item_id, str):
        raise TypeError("item_id must be a string")

    if not item_id.strip():
        return QualityAssessment(
            dimension=QualityDimension.CUSTODY,
            status=QualityStatus.FAIL,
            score=0.0,
            issues=(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="invalid_item_id",
                    message="item_id is required",
                    field="item_id",
                    severity="error",
                ),
            ),
        )

    if not events:
        return QualityAssessment(
            dimension=QualityDimension.CUSTODY,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []
    seen_event_ids: set[str] = set()
    previous_timestamp: datetime | None = None

    for index, event in enumerate(events):

        if not isinstance(event, CustodyEvent):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="invalid_event",
                    message="event must be a CustodyEvent",
                    record_id=str(index),
                    severity="error",
                )
            )
            continue

        event_id = event.event_id or str(index)

        if event.item_id != item_id:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="item_mismatch",
                    message="custody event item_id does not match target item",
                    record_id=event_id,
                    field="item_id",
                    severity="error",
                )
            )

        if not event.actor.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="invalid_actor",
                    message="custody event actor is required",
                    record_id=event_id,
                    field="actor",
                    severity="error",
                )
            )

        if not event.action.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="invalid_action",
                    message="custody event action is required",
                    record_id=event_id,
                    field="action",
                    severity="error",
                )
            )

        timestamp = event.timestamp

        if timestamp.tzinfo is None:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="invalid_timestamp",
                    message="custody timestamp must be timezone-aware",
                    record_id=event_id,
                    field="timestamp",
                    severity="error",
                )
            )
        else:
            timestamp_utc = timestamp.astimezone(timezone.utc)

            if (
                previous_timestamp is not None
                and timestamp_utc < previous_timestamp
            ):
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.CUSTODY,
                        code="chronology_error",
                        message="custody events are not chronological",
                        record_id=event_id,
                        field="timestamp",
                        severity="error",
                    )
                )

            previous_timestamp = timestamp_utc

        if event.event_id in seen_event_ids:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.CUSTODY,
                    code="duplicate_event",
                    message="duplicate custody event detected",
                    record_id=event_id,
                    severity="warning",
                )
            )

        seen_event_ids.add(event.event_id)

    issue_count = len(issues)

    error_count = sum(
        1
        for issue in issues
        if issue.severity == "error"
    )

    score = round(
        max(
            0.0,
            ((len(events) - error_count) / len(events))
            * 100.0,
        ),
        2,
    )

    if error_count:
        status = QualityStatus.FAIL
    elif issue_count:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.PASS

    return QualityAssessment(
        dimension=QualityDimension.CUSTODY,
        status=status,
        score=score,
        issues=tuple(issues),
    )
