from datetime import datetime, timezone, timedelta

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.market.movement import (
    CompetitiveMovementDetector,
    MovementDirection,
    MovementType,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
)


def make_signal(
    signal_id: str,
    signal_type: SignalType,
    entity_id: str,
    detected_at: datetime,
    confidence: float = 0.8,
    strength: float = 0.7,
    previous_value=None,
    current_value=None,
    evidence_ids=None,
):
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        detected_at=detected_at,
        confidence=confidence,
        strength=strength,
        previous_value=previous_value,
        current_value=current_value,
        evidence_ids=evidence_ids or [],
    )


def make_history(signals):
    ordered = sorted(
        signals,
        key=lambda signal: signal.detected_at,
    )

    return TemporalSignalHistory(
        signal_type=ordered[0].signal_type,
        entity_id=ordered[0].entity_id,
        signals=tuple(ordered),
        first_observed_at=ordered[0].detected_at,
        latest_observed_at=ordered[-1].detected_at,
        observation_count=len(ordered),
        repeated_observation_count=max(
            0,
            len(ordered) - 1,
        ),
        time_span_seconds=(
            ordered[-1].detected_at
            - ordered[0].detected_at
        ).total_seconds(),
    )


def test_company_expansion_is_detected():
    now = datetime.now(timezone.utc)

    history = make_history([
        make_signal(
            "s1",
            SignalType.COMPANY_EXPANSION,
            "competitor-a",
            now,
            evidence_ids=["e1"],
        ),
        make_signal(
            "s2",
            SignalType.COMPANY_EXPANSION,
            "competitor-a",
            now + timedelta(days=30),
            evidence_ids=["e2"],
        ),
    ])

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.entity_id == "competitor-a"
    assert movement.movement_type == MovementType.EXPANSION
    assert movement.direction == MovementDirection.INCREASE
    assert movement.signal_count == 2
    assert movement.confidence == 0.8
    assert movement.evidence_ids == ("e1", "e2")
    assert movement.intensity > 0.0


def test_competitor_change_is_contraction():
    now = datetime.now(timezone.utc)

    history = make_history([
        make_signal(
            "s1",
            SignalType.COMPETITOR_CHANGE,
            "competitor-b",
            now,
        ),
    ])

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.movement_type == MovementType.CONTRACTION
    assert movement.direction == MovementDirection.DECREASE


def test_price_increase_is_detected():
    now = datetime.now(timezone.utc)

    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            "competitor-c",
            now,
            previous_value=100,
            current_value=120,
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
            "competitor-c",
            now + timedelta(days=30),
            previous_value=120,
            current_value=140,
        ),
    ])

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.movement_type == MovementType.PRICING
    assert movement.direction == MovementDirection.INCREASE


def test_price_decrease_is_detected():
    now = datetime.now(timezone.utc)

    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            "competitor-d",
            now,
            previous_value=100,
            current_value=90,
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
            "competitor-d",
            now + timedelta(days=30),
            previous_value=90,
            current_value=80,
        ),
    ])

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.movement_type == MovementType.PRICING
    assert movement.direction == MovementDirection.DECREASE


def test_non_numeric_price_change_is_stable():
    now = datetime.now(timezone.utc)

    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            "competitor-e",
            now,
            current_value={"price": "unknown"},
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
            "competitor-e",
            now + timedelta(days=10),
            current_value={"price": "lower"},
        ),
    ])

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.direction == MovementDirection.STABLE


def test_repeated_activity_increases_intensity():
    now = datetime.now(timezone.utc)

    signals = [
        make_signal(
            f"s{i}",
            SignalType.HIRING_SIGNAL,
            "competitor-f",
            now + timedelta(days=i * 10),
            strength=0.8,
        )
        for i in range(5)
    ]

    history = make_history(signals)

    movement = CompetitiveMovementDetector().detect(history)

    assert movement.movement_type == MovementType.HIRING
    assert movement.direction == MovementDirection.INCREASE
    assert movement.intensity >= 0.8


def test_detector_rejects_invalid_history():
    detector = CompetitiveMovementDetector()

    try:
        detector.detect("invalid")
    except TypeError as exc:
        assert "TemporalSignalHistory" in str(exc)
    else:
        raise AssertionError("Expected TypeError")


def test_multiple_histories_are_detected():
    now = datetime.now(timezone.utc)

    histories = [
        make_history([
            make_signal(
                "s1",
                SignalType.COMPANY_EXPANSION,
                "a",
                now,
            )
        ]),
        make_history([
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
                "b",
                now,
            )
        ]),
    ]

    movements = CompetitiveMovementDetector().detect_many(
        histories
    )

    assert len(movements) == 2
    assert movements[0].movement_type == MovementType.EXPANSION
    assert movements[1].movement_type == MovementType.PRODUCT
