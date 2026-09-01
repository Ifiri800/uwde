from datetime import datetime, timedelta, timezone

from backend.app.services.intelligence.methane.quality.audit import (
    assess_audit_trail,
)
from backend.app.services.intelligence.methane.quality.models import (
    AuditEvent,
    QualityDimension,
    QualityStatus,
)


T0 = datetime(
    2026, 8, 1, 10, 0, tzinfo=timezone.utc
)


def event(
    event_id="A1",
    event_type="quality_check",
    timestamp=T0,
    actor="system",
    action="validate",
    description="Validation performed",
    record_id="R1",
    batch_id="B1",
):
    return AuditEvent(
        event_id=event_id,
        event_type=event_type,
        timestamp=timestamp,
        actor=actor,
        action=action,
        description=description,
        record_id=record_id,
        batch_id=batch_id,
    )


def test_valid_audit_trail_passes():
    result = assess_audit_trail(
        events=(
            event(),
            event(
                event_id="A2",
                timestamp=T0 + timedelta(minutes=5),
                action="approve",
            ),
        )
    )

    assert result.dimension == QualityDimension.AUDIT
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_empty_events_are_not_assessed():
    result = assess_audit_trail(events=())

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_invalid_event_type_is_detected():
    result = assess_audit_trail(
        events=("invalid",)
    )

    assert result.status == QualityStatus.FAIL


def test_missing_event_id_is_detected():
    result = assess_audit_trail(
        events=(event(event_id=""),)
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_event_id"
        for issue in result.issues
    )


def test_missing_actor_is_detected():
    result = assess_audit_trail(
        events=(event(actor=""),)
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_actor"
        for issue in result.issues
    )


def test_missing_action_is_detected():
    result = assess_audit_trail(
        events=(event(action=""),)
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_action"
        for issue in result.issues
    )


def test_missing_event_type_is_detected():
    result = assess_audit_trail(
        events=(event(event_type=""),)
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_event_type"
        for issue in result.issues
    )


def test_naive_timestamp_is_detected():
    result = assess_audit_trail(
        events=(
            event(
                timestamp=datetime(
                    2026, 8, 1, 10, 0
                )
            ),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_timestamp"
        for issue in result.issues
    )


def test_non_chronological_events_are_detected():
    result = assess_audit_trail(
        events=(
            event(),
            event(
                event_id="A2",
                timestamp=T0 - timedelta(minutes=5),
            ),
        )
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "chronology_error"
        for issue in result.issues
    )


def test_duplicate_event_ids_are_detected():
    result = assess_audit_trail(
        events=(
            event(),
            event(),
        )
    )

    assert result.status == QualityStatus.WARNING
    assert any(
        issue.code == "duplicate_event_id"
        for issue in result.issues
    )


def test_blank_description_is_allowed():
    result = assess_audit_trail(
        events=(event(description=""),)
    )

    assert result.status == QualityStatus.PASS


def test_audit_event_context_is_preserved():
    result = assess_audit_trail(
        events=(
            event(
                record_id="RECORD-77",
                batch_id="BATCH-22",
            ),
        )
    )

    assert result.status == QualityStatus.PASS
    assert result.issue_count == 0
