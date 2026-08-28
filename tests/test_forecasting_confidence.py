from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.market.change import (
    MarketChangeAnalysis,
    MarketChangeDirection,
    MarketChangeType,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
)
from backend.app.services.intelligence.forecasting.confidence import (
    ForecastConfidenceAnalysis,
    ForecastConfidenceAnalyzer,
    calculate_forecast_confidence,
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
    days: int = 0,
    confidence: float = 0.8,
    strength: float = 0.7,
    evidence_ids=None,
):
    return Signal(
        signal_id=signal_id,
        signal_type=SignalType.MARKET_GROWTH,
        entity_id="market-1",
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
    signals=None,
):
    signals = signals or [make_signal("s1")]

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
    direction=MarketChangeDirection.INCREASE,
    magnitude=0.7,
    confidence=0.8,
    evidence_ids=("e-s1",),
):
    return MarketChangeAnalysis(
        entity_id="market-1",
        change_type=MarketChangeType.EXPANSION,
        direction=direction,
        signal_type=SignalType.MARKET_GROWTH,
        observation_count=1,
        magnitude=magnitude,
        confidence=confidence,
        first_observed_at=BASE_TIME,
        latest_observed_at=BASE_TIME,
        evidence_ids=evidence_ids,
        explanation="Test market change.",
    )


def test_high_quality_signals_produce_high_confidence():
    history = make_history([
        make_signal(
            "s1",
            confidence=0.95,
            strength=0.9,
        ),
        make_signal(
            "s2",
            days=10,
            confidence=0.95,
            strength=0.9,
        ),
    ])

    change = make_change(
        magnitude=0.9,
        confidence=0.95,
    )

    result = calculate_forecast_confidence(
        history,
        change,
    )

    assert isinstance(result, ForecastConfidenceAnalysis)
    assert result.confidence_score > 0.7


def test_low_signal_quality_reduces_confidence():
    high_history = make_history([
        make_signal(
            "s1",
            confidence=0.95,
            strength=0.9,
        )
    ])

    low_history = make_history([
        make_signal(
            "s1",
            confidence=0.4,
            strength=0.3,
        )
    ])

    change = make_change(
        confidence=0.9,
        magnitude=0.8,
    )

    high = calculate_forecast_confidence(
        high_history,
        change,
    )

    low = calculate_forecast_confidence(
        low_history,
        change,
    )

    assert high.confidence_score > low.confidence_score


def test_repeated_consistent_history_increases_confidence():
    single = make_history([
        make_signal(
            "s1",
            confidence=0.8,
            strength=0.7,
        )
    ])

    repeated = make_history([
        make_signal(
            "s1",
            confidence=0.8,
            strength=0.7,
        ),
        make_signal(
            "s2",
            days=10,
            confidence=0.8,
            strength=0.7,
        ),
        make_signal(
            "s3",
            days=20,
            confidence=0.8,
            strength=0.7,
        ),
        make_signal(
            "s4",
            days=30,
            confidence=0.8,
            strength=0.7,
        ),
    ])

    change = make_change()

    single_result = calculate_forecast_confidence(
        single,
        change,
    )

    repeated_result = calculate_forecast_confidence(
        repeated,
        change,
    )

    assert (
        repeated_result.historical_consistency
        >= single_result.historical_consistency
    )


def test_data_coverage_increases_with_evidence():
    low_coverage = make_history([
        make_signal(
            "s1",
            evidence_ids=["e1"],
        )
    ])

    high_coverage = make_history([
        make_signal(
            "s1",
            evidence_ids=["e1", "e2", "e3"],
        ),
        make_signal(
            "s2",
            days=10,
            evidence_ids=["e4", "e5"],
        ),
    ])

    change = make_change()

    low = calculate_forecast_confidence(
        low_coverage,
        change,
    )

    high = calculate_forecast_confidence(
        high_coverage,
        change,
    )

    assert high.data_coverage >= low.data_coverage


def test_uncertainty_is_bounded():
    history = make_history()
    change = make_change()

    result = calculate_forecast_confidence(
        history,
        change,
    )

    assert 0.0 <= result.uncertainty <= 1.0


def test_confidence_score_is_bounded():
    history = make_history([
        make_signal(
            "s1",
            confidence=1.0,
            strength=1.0,
        ),
        make_signal(
            "s2",
            days=10,
            confidence=1.0,
            strength=1.0,
        ),
    ])

    change = make_change(
        magnitude=1.0,
        confidence=1.0,
    )

    result = calculate_forecast_confidence(
        history,
        change,
    )

    assert 0.0 <= result.confidence_score <= 1.0


def test_confidence_components_are_exposed():
    result = calculate_forecast_confidence(
        make_history(),
        make_change(),
    )

    assert 0.0 <= result.signal_quality <= 1.0
    assert 0.0 <= result.historical_consistency <= 1.0
    assert 0.0 <= result.data_coverage <= 1.0
    assert 0.0 <= result.uncertainty <= 1.0


def test_evidence_ids_are_preserved():
    history = make_history([
        make_signal(
            "s1",
            evidence_ids=["e1", "e2"],
        )
    ])

    change = make_change(
        evidence_ids=("e2", "e3"),
    )

    result = calculate_forecast_confidence(
        history,
        change,
    )

    assert result.evidence_ids == (
        "e2",
        "e3",
        "e1",
    )


def test_result_to_dict_is_explainable():
    result = calculate_forecast_confidence(
        make_history(),
        make_change(),
    )

    data = result.to_dict()

    assert data["entity_id"] == "market-1"
    assert "confidence_score" in data
    assert "signal_quality" in data
    assert "historical_consistency" in data
    assert "data_coverage" in data
    assert "uncertainty" in data
    assert "explanation" in data


def test_analyzer_rejects_invalid_history():
    with pytest.raises(
        TypeError,
        match="history must be a TemporalSignalHistory",
    ):
        ForecastConfidenceAnalyzer().analyze(
            "invalid",
            make_change(),
        )


def test_analyzer_rejects_invalid_change():
    with pytest.raises(
        TypeError,
        match="change must be a MarketChangeAnalysis",
    ):
        ForecastConfidenceAnalyzer().analyze(
            make_history(),
            "invalid",
        )


def test_analyzer_rejects_entity_mismatch():
    change = MarketChangeAnalysis(
        entity_id="different-market",
        change_type=MarketChangeType.EXPANSION,
        direction=MarketChangeDirection.INCREASE,
        signal_type=SignalType.MARKET_GROWTH,
        observation_count=1,
        magnitude=0.7,
        confidence=0.8,
        first_observed_at=BASE_TIME,
        latest_observed_at=BASE_TIME,
        evidence_ids=("e1",),
        explanation="Test market change.",
    )

    with pytest.raises(
        ValueError,
        match="same entity",
    ):
        ForecastConfidenceAnalyzer().analyze(
            make_history(),
            change,
        )


def test_convenience_function_matches_analyzer():
    history = make_history()
    change = make_change()

    expected = ForecastConfidenceAnalyzer().analyze(
        history,
        change,
    )

    actual = calculate_forecast_confidence(
        history,
        change,
    )

    assert actual == expected


def test_confidence_is_deterministic():
    history = make_history([
        make_signal("s1", confidence=0.8, strength=0.7),
        make_signal(
            "s2",
            days=10,
            confidence=0.9,
            strength=0.8,
        ),
    ])

    change = make_change(
        magnitude=0.75,
        confidence=0.85,
    )

    first = calculate_forecast_confidence(
        history,
        change,
    )

    second = calculate_forecast_confidence(
        history,
        change,
    )

    assert first == second
