from datetime import datetime, timedelta, timezone

from backend.app.services.intelligence.methane.quality.custody import (
    assess_custody,
)
from backend.app.services.intelligence.methane.quality.models import (
    CustodyEvent,
    QualityDimension,
    QualityStatus,
)


T0 = datetime(
    2026, 8, 1, 10, 0, tzinfo=timezone.utc
)


def event(
    event_id="E1",
    item_id="ITEM-001",
    timestamp=T0,
    actor="Operator",
    action="received",
    location="Facility A",
    checksum="abc",
):
    return CustodyEvent(
        event_id=event_id,
        item_id=item_id,
        timestamp=timestamp,
        actor=actor,
        action=action,
        location=location,
        checksum=checksum,
    )


def test_valid_custody_passes():
    result = assess_custody(
        events=(
            event(),
            event(
                event_id="E2",
                timestamp=T0 + timedelta(hours=1),
                action="transferred",
                checksum="def",
            ),
        ),
        item_id="ITEM-001",
    )

    assert result.dimension == QualityDimension.CUSTODY
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_wrong_item_id_is_detected():
    result = assess_custody(
        events=(event(item_id="OTHER"),),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL
    assert result.issues[0].code == "item_mismatch"


def test_empty_actor_is_detected():
    result = assess_custody(
        events=(event(actor=""),),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL
    assert result.issues[0].code == "invalid_actor"


def test_empty_action_is_detected():
    result = assess_custody(
        events=(event(action=""),),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL
    assert result.issues[0].code == "invalid_action"


def test_non_chronological_events_are_detected():
    result = assess_custody(
        events=(
            event(),
            event(
                event_id="E2",
                timestamp=T0 - timedelta(hours=1),
            ),
        ),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "chronology_error"
        for issue in result.issues
    )


def test_duplicate_event_is_detected():
    result = assess_custody(
        events=(
            event(),
            event(),
        ),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.WARNING
    assert any(
        issue.code == "duplicate_event"
        for issue in result.issues
    )


def test_empty_events_are_not_assessed():
    result = assess_custody(
        events=(),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_invalid_event_type_is_detected():
    result = assess_custody(
        events=("invalid",),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL


def test_empty_item_id_is_rejected():
    result = assess_custody(
        events=(event(),),
        item_id="",
    )

    assert result.status == QualityStatus.FAIL


def test_naive_timestamp_is_detected():
    result = assess_custody(
        events=(
            event(
                timestamp=datetime(
                    2026, 8, 1, 10, 0
                )
            ),
        ),
        item_id="ITEM-001",
    )

    assert result.status == QualityStatus.FAIL
    assert any(
        issue.code == "invalid_timestamp"
        for issue in result.issues
    )
