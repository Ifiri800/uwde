from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
    TemporalSignalTracker,
    track_temporal_signals,
)


BASE_TIME = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)


def make_signal(
    signal_id: str,
    *,
    signal_type: SignalType = SignalType.MARKET_GROWTH,
    entity_id: str = "market-1",
    days: int = 0,
    confidence: float = 0.8,
    strength: float = 0.7,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        detected_at=BASE_TIME + timedelta(days=days),
        confidence=confidence,
        strength=strength,
        evidence_ids=[f"e-{signal_id}"],
    )


def test_single_signal_creates_temporal_history():
    histories = track_temporal_signals(
        [make_signal("s1")]
    )

    assert len(histories) == 1

    history = histories[0]

    assert isinstance(history, TemporalSignalHistory)
    assert history.observation_count == 1
    assert history.repeated_observation_count == 0
    assert history.is_recurring is False
    assert history.time_span_seconds == 0.0


def test_repeated_signals_are_grouped():
    histories = track_temporal_signals(
        [
            make_signal("s1", days=0),
            make_signal("s2", days=7),
            make_signal("s3", days=14),
        ]
    )

    assert len(histories) == 1

    history = histories[0]

    assert history.observation_count == 3
    assert history.repeated_observation_count == 2
    assert history.is_recurring is True


def test_signals_are_chronologically_ordered():
    histories = track_temporal_signals(
        [
            make_signal("s3", days=14),
            make_signal("s1", days=0),
            make_signal("s2", days=7),
        ]
    )

    assert [
        signal.signal_id
        for signal in histories[0].signals
    ] == ["s1", "s2", "s3"]


def test_first_and_latest_observation_are_tracked():
    histories = track_temporal_signals(
        [
            make_signal("s1", days=2),
            make_signal("s2", days=10),
        ]
    )

    history = histories[0]

    assert history.first_observed_at == (
        BASE_TIME + timedelta(days=2)
    )

    assert history.latest_observed_at == (
        BASE_TIME + timedelta(days=10)
    )


def test_time_span_is_calculated():
    histories = track_temporal_signals(
        [
            make_signal("s1", days=0),
            make_signal("s2", days=10),
        ]
    )

    assert history_time_span(histories[0]) == (
        10 * 24 * 60 * 60
    )


def test_latest_signal_is_available():
    histories = track_temporal_signals(
        [
            make_signal("s1", days=0),
            make_signal("s2", days=5),
        ]
    )

    assert histories[0].latest_signal.signal_id == "s2"


def test_confidence_history_is_preserved():
    histories = track_temporal_signals(
        [
            make_signal(
                "s1",
                days=0,
                confidence=0.5,
            ),
            make_signal(
                "s2",
                days=5,
                confidence=0.7,
            ),
            make_signal(
                "s3",
                days=10,
                confidence=0.9,
            ),
        ]
    )

    assert histories[0].confidence_history == (
        0.5,
        0.7,
        0.9,
    )


def test_strength_history_is_preserved():
    histories = track_temporal_signals(
        [
            make_signal(
                "s1",
                days=0,
                strength=0.4,
            ),
            make_signal(
                "s2",
                days=5,
                strength=0.6,
            ),
            make_signal(
                "s3",
                days=10,
                strength=0.8,
            ),
        ]
    )

    assert histories[0].strength_history == (
        0.4,
        0.6,
        0.8,
    )


def test_different_entities_create_separate_histories():
    histories = track_temporal_signals(
        [
            make_signal(
                "s1",
                entity_id="market-1",
            ),
            make_signal(
                "s2",
                entity_id="market-2",
            ),
        ]
    )

    assert len(histories) == 2


def test_different_signal_types_create_separate_histories():
    histories = track_temporal_signals(
        [
            make_signal(
                "s1",
                signal_type=SignalType.MARKET_GROWTH,
            ),
            make_signal(
                "s2",
                signal_type=SignalType.PRICE_CHANGE,
            ),
        ]
    )

    assert len(histories) == 2


def test_empty_input_returns_empty_history():
    assert track_temporal_signals([]) == []


def test_invalid_input_type():
    with pytest.raises(
        TypeError,
        match="signals must be a list",
    ):
        TemporalSignalTracker().track(
            "invalid"  # type: ignore[arg-type]
        )


def test_invalid_signal_items():
    with pytest.raises(
        TypeError,
        match="signals must contain only Signal objects",
    ):
        TemporalSignalTracker().track(
            ["invalid"]  # type: ignore[list-item]
        )


def test_to_dict_contains_temporal_metadata():
    histories = track_temporal_signals(
        [
            make_signal("s1", days=0),
            make_signal("s2", days=5),
        ]
    )

    data = histories[0].to_dict()

    assert data["entity_id"] == "market-1"
    assert data["observation_count"] == 2
    assert data["repeated_observation_count"] == 1
    assert data["is_recurring"] is True
    assert len(data["signals"]) == 2


def test_histories_are_sorted_by_latest_observation():
    histories = track_temporal_signals(
        [
            make_signal(
                "old",
                entity_id="market-old",
                days=1,
            ),
            make_signal(
                "new",
                entity_id="market-new",
                days=20,
            ),
        ]
    )

    assert histories[0].entity_id == "market-old"
    assert histories[1].entity_id == "market-new"


def history_time_span(history: TemporalSignalHistory) -> float:
    return history.time_span_seconds
