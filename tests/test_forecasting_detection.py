from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.forecasting.detection import (
    ForecastAnalysis,
    ForecastDirection,
    ForecastHorizon,
    ForecastingAnalyzer,
    forecast_market_change,
    forecast_market_changes,
)
from backend.app.services.intelligence.market.change import (
    MarketChangeAnalysis,
    MarketChangeDirection,
    MarketChangeType,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
)


BASE_TIME = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)


def make_signal(
    signal_id: str,
    signal_type: SignalType = SignalType.MARKET_GROWTH,
    entity_id: str = "market-1",
    days: int = 0,
    confidence: float = 0.8,
    strength: float = 0.7,
    evidence_ids=None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        detected_at=BASE_TIME + timedelta(days=days),
        confidence=confidence,
        strength=strength,
        evidence_ids=(
            [f"e-{signal_id}"]
            if evidence_ids is None
            else evidence_ids
        ),
    )


def make_history(
    signals: list[Signal],
) -> TemporalSignalHistory:
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


def make_change(
    *,
    entity_id: str = "market-1",
    signal_type: SignalType = SignalType.MARKET_GROWTH,
    direction: MarketChangeDirection = MarketChangeDirection.INCREASE,
    change_type: MarketChangeType = MarketChangeType.EXPANSION,
    magnitude: float = 0.7,
    confidence: float = 0.8,
    observation_count: int = 1,
    evidence_ids=("e-1",),
) -> MarketChangeAnalysis:
    return MarketChangeAnalysis(
        entity_id=entity_id,
        change_type=change_type,
        direction=direction,
        signal_type=signal_type,
        observation_count=observation_count,
        magnitude=magnitude,
        confidence=confidence,
        first_observed_at=BASE_TIME,
        latest_observed_at=BASE_TIME + timedelta(days=10),
        evidence_ids=evidence_ids,
        explanation="Market change detected.",
    )


def test_growth_change_produces_growth_forecast():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.GROWTH


def test_decline_change_produces_decline_forecast():
    history = make_history([
        make_signal(
            "s1",
            signal_type=SignalType.COMPETITOR_CHANGE,
        ),
    ])

    change = make_change(
        signal_type=SignalType.COMPETITOR_CHANGE,
        direction=MarketChangeDirection.DECREASE,
        change_type=MarketChangeType.CONTRACTION,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.DECLINE


def test_stable_change_produces_stable_forecast():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change(
        direction=MarketChangeDirection.STABLE,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.STABLE


def test_single_observation_is_short_term():
    history = make_history([
        make_signal("s1"),
    ])

    result = forecast_market_change(
        history,
        make_change(),
    )

    assert result.horizon == ForecastHorizon.SHORT_TERM


def test_two_observations_are_medium_term():
    history = make_history([
        make_signal("s1", days=0),
        make_signal("s2", days=10),
    ])

    result = forecast_market_change(
        history,
        make_change(observation_count=2),
    )

    assert result.horizon == ForecastHorizon.MEDIUM_TERM


def test_four_observations_are_medium_term():
    history = make_history([
        make_signal("s1", days=0),
        make_signal("s2", days=10),
        make_signal("s3", days=20),
        make_signal("s4", days=30),
    ])

    result = forecast_market_change(
        history,
        make_change(observation_count=4),
    )

    assert result.horizon == ForecastHorizon.MEDIUM_TERM


def test_five_observations_are_long_term():
    history = make_history([
        make_signal("s1", days=0),
        make_signal("s2", days=10),
        make_signal("s3", days=20),
        make_signal("s4", days=30),
        make_signal("s5", days=40),
    ])

    result = forecast_market_change(
        history,
        make_change(observation_count=5),
    )

    assert result.horizon == ForecastHorizon.LONG_TERM


def test_repeated_activity_increases_forecast_strength():
    single_history = make_history([
        make_signal("s1", strength=0.7),
    ])

    repeated_history = make_history([
        make_signal("s1", days=0, strength=0.7),
        make_signal("s2", days=10, strength=0.7),
        make_signal("s3", days=20, strength=0.7),
        make_signal("s4", days=30, strength=0.7),
        make_signal("s5", days=40, strength=0.7),
    ])

    change_single = make_change(
        magnitude=0.7,
        observation_count=1,
    )

    change_repeated = make_change(
        magnitude=0.7,
        observation_count=5,
    )

    single = forecast_market_change(
        single_history,
        change_single,
    )

    repeated = forecast_market_change(
        repeated_history,
        change_repeated,
    )

    assert repeated.forecast_strength > single.forecast_strength


def test_stronger_signal_increases_forecast_strength():
    weak_history = make_history([
        make_signal(
            "weak",
            strength=0.2,
        ),
    ])

    strong_history = make_history([
        make_signal(
            "strong",
            strength=0.9,
        ),
    ])

    change = make_change(
        magnitude=0.6,
    )

    weak = forecast_market_change(
        weak_history,
        change,
    )

    strong = forecast_market_change(
        strong_history,
        change,
    )

    assert strong.forecast_strength > weak.forecast_strength


def test_higher_change_magnitude_increases_forecast_strength():
    history = make_history([
        make_signal("s1"),
    ])

    weak_change = make_change(
        magnitude=0.2,
    )

    strong_change = make_change(
        magnitude=0.9,
    )

    weak = forecast_market_change(
        history,
        weak_change,
    )

    strong = forecast_market_change(
        history,
        strong_change,
    )

    assert strong.forecast_strength > weak.forecast_strength


def test_confidence_is_combined_from_history_and_change():
    history = make_history([
        make_signal(
            "s1",
            confidence=0.8,
        ),
    ])

    change = make_change(
        confidence=0.6,
    )

    result = forecast_market_change(
        history,
        change,
    )

    expected = (
        0.8 * 0.60
        + 0.6 * 0.40
    )

    assert result.confidence == round(
        expected,
        6,
    )


def test_evidence_ids_are_preserved_and_deduplicated():
    history = make_history([
        make_signal(
            "s1",
            evidence_ids=["e1", "e2"],
        ),
        make_signal(
            "s2",
            days=5,
            evidence_ids=["e2", "e3"],
        ),
    ])

    change = make_change(
        evidence_ids=("e1", "e4"),
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.evidence_ids == (
        "e1",
        "e4",
        "e2",
        "e3",
    )


def test_observation_metadata_is_preserved():
    history = make_history([
        make_signal("s1", days=2),
        make_signal("s2", days=12),
    ])

    change = make_change(
        observation_count=2,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.entity_id == "market-1"
    assert result.observation_count == 2
    assert result.first_observed_at == (
        BASE_TIME + timedelta(days=2)
    )
    assert result.latest_observed_at == (
        BASE_TIME + timedelta(days=12)
    )


def test_result_is_forecast_analysis():
    history = make_history([
        make_signal("s1"),
    ])

    result = forecast_market_change(
        history,
        make_change(),
    )

    assert isinstance(
        result,
        ForecastAnalysis,
    )


def test_result_to_dict_is_explainable():
    history = make_history([
        make_signal("s1"),
    ])

    result = forecast_market_change(
        history,
        make_change(),
    )

    data = result.to_dict()

    assert data["entity_id"] == "market-1"
    assert data["signal_type"] == SignalType.MARKET_GROWTH.value
    assert data["direction"] == ForecastDirection.GROWTH.value
    assert data["horizon"] == ForecastHorizon.SHORT_TERM.value
    assert isinstance(data["forecast_strength"], float)
    assert isinstance(data["confidence"], float)
    assert isinstance(data["evidence_ids"], list)
    assert isinstance(data["explanation"], str)


def test_explanation_contains_forecast_details():
    history = make_history([
        make_signal("s1"),
    ])

    result = forecast_market_change(
        history,
        make_change(),
    )

    assert "market-1" in result.explanation
    assert "growth" in result.explanation
    assert "short-term" in result.explanation
    assert "forecast strength" in result.explanation


def test_analyzer_rejects_invalid_history():
    with pytest.raises(
        TypeError,
        match="history must be a TemporalSignalHistory",
    ):
        ForecastingAnalyzer().analyze(
            "invalid",  # type: ignore[arg-type]
            make_change(),
        )


def test_analyzer_rejects_invalid_change():
    history = make_history([
        make_signal("s1"),
    ])

    with pytest.raises(
        TypeError,
        match="change must be a MarketChangeAnalysis",
    ):
        ForecastingAnalyzer().analyze(
            history,
            "invalid",  # type: ignore[arg-type]
        )


def test_analyzer_rejects_entity_mismatch():
    history = make_history([
        make_signal(
            "s1",
            entity_id="entity-a",
        ),
    ])

    change = make_change(
        entity_id="entity-b",
    )

    with pytest.raises(
        ValueError,
        match="same entity",
    ):
        ForecastingAnalyzer().analyze(
            history,
            change,
        )


def test_analyze_many_requires_list():
    analyzer = ForecastingAnalyzer()

    with pytest.raises(
        TypeError,
        match="inputs must be a list",
    ):
        analyzer.analyze_many(
            "invalid"  # type: ignore[arg-type]
        )


def test_analyze_many_returns_all_results():
    history_a = make_history([
        make_signal(
            "a1",
            entity_id="a",
            days=1,
        ),
    ])

    history_b = make_history([
        make_signal(
            "b1",
            entity_id="b",
            days=2,
        ),
    ])

    change_a = make_change(
        entity_id="a",
        observation_count=1,
    )

    change_b = make_change(
        entity_id="b",
        observation_count=1,
    )

    results = forecast_market_changes([
        (history_a, change_a),
        (history_b, change_b),
    ])

    assert len(results) == 2
    assert {
        result.entity_id
        for result in results
    } == {"a", "b"}


def test_analyze_many_is_sorted_deterministically():
    history_late = make_history([
        make_signal(
            "late",
            entity_id="late",
            days=20,
        ),
    ])

    history_early = make_history([
        make_signal(
            "early",
            entity_id="early",
            days=5,
        ),
    ])

    results = forecast_market_changes([
        (
            history_late,
            make_change(
                entity_id="late",
            ),
        ),
        (
            history_early,
            make_change(
                entity_id="early",
            ),
        ),
    ])

    assert [
        result.entity_id
        for result in results
    ] == [
        "early",
        "late",
    ]


def test_empty_input_returns_empty_list():
    assert forecast_market_changes([]) == []


def test_convenience_function_matches_analyzer():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    direct = ForecastingAnalyzer().analyze(
        history,
        change,
    )

    convenience = forecast_market_change(
        history,
        change,
    )

    assert convenience == direct


def test_convenience_many_function_matches_analyzer():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    analyzer = ForecastingAnalyzer().analyze_many([
        (history, change),
    ])

    convenience = forecast_market_changes([
        (history, change),
    ])

    assert convenience == analyzer


def test_forecast_strength_is_bounded():
    history = make_history([
        make_signal(
            "s1",
            strength=1.0,
        ),
        make_signal(
            "s2",
            days=5,
            strength=1.0,
        ),
        make_signal(
            "s3",
            days=10,
            strength=1.0,
        ),
        make_signal(
            "s4",
            days=15,
            strength=1.0,
        ),
        make_signal(
            "s5",
            days=20,
            strength=1.0,
        ),
    ])

    change = make_change(
        magnitude=1.0,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert 0.0 <= result.forecast_strength <= 1.0


def test_confidence_is_bounded():
    history = make_history([
        make_signal(
            "s1",
            confidence=1.0,
        ),
    ])

    change = make_change(
        confidence=1.0,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert 0.0 <= result.confidence <= 1.0


def test_declining_market_change_produces_decline_forecast():
    history = make_history([
        make_signal(
            "s1",
            signal_type=SignalType.PRICE_CHANGE,
        ),
        make_signal(
            "s2",
            signal_type=SignalType.PRICE_CHANGE,
            days=10,
        ),
    ])

    change = make_change(
        signal_type=SignalType.PRICE_CHANGE,
        direction=MarketChangeDirection.DECREASE,
        change_type=MarketChangeType.PRICE_DECREASE,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.DECLINE


def test_increasing_market_change_produces_growth_forecast():
    history = make_history([
        make_signal(
            "s1",
            signal_type=SignalType.PRICE_CHANGE,
        ),
    ])

    change = make_change(
        signal_type=SignalType.PRICE_CHANGE,
        direction=MarketChangeDirection.INCREASE,
        change_type=MarketChangeType.PRICE_INCREASE,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.GROWTH


def test_stable_market_change_produces_stable_forecast():
    history = make_history([
        make_signal(
            "s1",
            signal_type=SignalType.PRICE_CHANGE,
        ),
    ])

    change = make_change(
        signal_type=SignalType.PRICE_CHANGE,
        direction=MarketChangeDirection.STABLE,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.STABLE


def test_different_entities_can_be_forecast_independently():
    history_a = make_history([
        make_signal(
            "a",
            entity_id="entity-a",
        ),
    ])

    history_b = make_history([
        make_signal(
            "b",
            entity_id="entity-b",
        ),
    ])

    result_a = forecast_market_change(
        history_a,
        make_change(entity_id="entity-a"),
    )

    result_b = forecast_market_change(
        history_b,
        make_change(entity_id="entity-b"),
    )

    assert result_a.entity_id == "entity-a"
    assert result_b.entity_id == "entity-b"


def test_forecast_uses_change_direction_not_signal_type_alone():
    history = make_history([
        make_signal(
            "s1",
            signal_type=SignalType.MARKET_GROWTH,
        ),
    ])

    change = make_change(
        signal_type=SignalType.MARKET_GROWTH,
        direction=MarketChangeDirection.DECREASE,
        change_type=MarketChangeType.CONTRACTION,
    )

    result = forecast_market_change(
        history,
        change,
    )

    assert result.direction == ForecastDirection.DECLINE


def test_forecast_strength_is_deterministic():
    history = make_history([
        make_signal(
            "s1",
            strength=0.65,
        ),
        make_signal(
            "s2",
            days=10,
            strength=0.75,
        ),
    ])

    change = make_change(
        magnitude=0.72,
        confidence=0.81,
    )

    first = forecast_market_change(
        history,
        change,
    )

    second = forecast_market_change(
        history,
        change,
    )

    assert first == second
