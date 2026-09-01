from __future__ import annotations

from datetime import timezone

from .models import (
    AuditEvent,
    QualityAssessment,
    QualityDimension,
    QualityIssue,
    QualityStatus,
)


def assess_audit_trail(
    events: tuple[AuditEvent, ...],
) -> QualityAssessment:
    """
    Assess the integrity of an immutable audit trail.

    Checks:
    - event type
    - event ID
    - actor
    - action
    - timestamp
    - chronological ordering
    - duplicate event IDs

    Audit events are never modified.
    """

    if not isinstance(events, tuple):
        raise TypeError("events must be a tuple")

    if not events:
        return QualityAssessment(
            dimension=QualityDimension.AUDIT,
            status=QualityStatus.NOT_ASSESSED,
            score=None,
        )

    issues: list[QualityIssue] = []
    seen_event_ids: set[str] = set()
    previous_timestamp = None
    error_count = 0

    for index, event in enumerate(events):
        if not isinstance(event, AuditEvent):
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_event",
                    message="event must be an AuditEvent",
                    record_id=str(index),
                    severity="error",
                )
            )
            error_count += 1
            continue

        event_id = event.event_id or str(index)

        if not event.event_id.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_event_id",
                    message="event_id is required",
                    record_id=event_id,
                    field="event_id",
                    severity="error",
                )
            )
            error_count += 1

        if not event.event_type.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_event_type",
                    message="event_type is required",
                    record_id=event_id,
                    field="event_type",
                    severity="error",
                )
            )
            error_count += 1

        if not event.actor.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_actor",
                    message="actor is required",
                    record_id=event_id,
                    field="actor",
                    severity="error",
                )
            )
            error_count += 1

        if not event.action.strip():
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_action",
                    message="action is required",
                    record_id=event_id,
                    field="action",
                    severity="error",
                )
            )
            error_count += 1

        timestamp = event.timestamp

        if timestamp.tzinfo is None:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="invalid_timestamp",
                    message="timestamp must be timezone-aware",
                    record_id=event_id,
                    field="timestamp",
                    severity="error",
                )
            )
            error_count += 1
        else:
            timestamp_utc = timestamp.astimezone(timezone.utc)

            if (
                previous_timestamp is not None
                and timestamp_utc < previous_timestamp
            ):
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.AUDIT,
                        code="chronology_error",
                        message="audit events are not chronological",
                        record_id=event_id,
                        field="timestamp",
                        severity="error",
                    )
                )
                error_count += 1

            previous_timestamp = timestamp_utc

        if event.event_id in seen_event_ids:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.AUDIT,
                    code="duplicate_event_id",
                    message="duplicate audit event ID detected",
                    record_id=event_id,
                    field="event_id",
                    severity="warning",
                )
            )

        seen_event_ids.add(event.event_id)

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
    elif issues:
        status = QualityStatus.WARNING
    else:
        status = QualityStatus.PASS

    return QualityAssessment(
        dimension=QualityDimension.AUDIT,
        status=status,
        score=score,
        issues=tuple(issues),
    )
