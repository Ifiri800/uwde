from __future__ import annotations

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
from backend.app.services.intelligence.forecasting.detection import (
    ForecastDirection,
    ForecastHorizon,
    ForecastAnalysis,
)
from backend.app.services.intelligence.forecasting.model import (
    ForecastModelResult,
    ForecastingModel,
    TrendDirection,
    project_forecast,
    project_forecast_many,
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
    evidence_ids: list[str] | None = None,
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
    direction: MarketChangeDirection = (
        MarketChangeDirection.INCREASE
    ),
    magnitude: float = 0.6,
    confidence: float = 0.8,
    evidence_ids: tuple[str, ...] = ("e1",),
) -> MarketChangeAnalysis:
    change_type = (
        MarketChangeType.EXPANSION
        if direction == MarketChangeDirection.INCREASE
        else (
            MarketChangeType.CONTRACTION
            if direction == MarketChangeDirection.DECREASE
            else MarketChangeType.EXPANSION
        )
    )

    return MarketChangeAnalysis(
        entity_id=entity_id,
        change_type=change_type,
        direction=direction,
        signal_type=signal_type,
        observation_count=1,
        magnitude=magnitude,
        confidence=confidence,
        first_observed_at=BASE_TIME,
        latest_observed_at=BASE_TIME,
        evidence_ids=evidence_ids,
        explanation="test market change",
    )


def make_detection(
    *,
    entity_id: str = "market-1",
    direction: ForecastDirection = ForecastDirection.GROWTH,
    horizon: ForecastHorizon = ForecastHorizon.SHORT_TERM,
) -> ForecastAnalysis:
    return ForecastAnalysis(
        entity_id=entity_id,
        signal_type=SignalType.MARKET_GROWTH,
        direction=direction,
        horizon=horizon,
        forecast_strength=0.7,
        confidence=0.8,
        observation_count=1,
        first_observed_at=BASE_TIME,
        latest_observed_at=BASE_TIME,
        evidence_ids=("e1",),
        explanation="test forecast detection",
    )


def test_increasing_change_creates_upward_trend():
    history = make_history([
        make_signal("s1", strength=0.5),
        make_signal("s2", days=10, strength=0.7),
    ])

    change = make_change(
        direction=MarketChangeDirection.INCREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.trend_direction == TrendDirection.UPWARD


def test_decreasing_change_creates_downward_trend():
    history = make_history([
        make_signal("s1", strength=0.7),
        make_signal("s2", days=10, strength=0.5),
    ])

    change = make_change(
        direction=MarketChangeDirection.DECREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.DECLINE,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.trend_direction == TrendDirection.DOWNWARD


def test_stable_change_creates_flat_trend():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change(
        direction=MarketChangeDirection.STABLE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.STABLE,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.trend_direction == TrendDirection.FLAT


def test_baseline_is_average_signal_strength():
    history = make_history([
        make_signal("s1", strength=0.4),
        make_signal("s2", days=5, strength=0.6),
        make_signal("s3", days=10, strength=0.8),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.baseline == 0.6


def test_baseline_is_bounded():
    history = make_history([
        make_signal("s1", strength=1.0),
        make_signal("s2", days=5, strength=1.0),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert 0.0 <= result.baseline <= 1.0


def test_growth_rate_is_positive_for_growth():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.INCREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.growth_rate > 0.0


def test_growth_rate_is_negative_for_decline():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.DECREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.DECLINE,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.growth_rate < 0.0


def test_stable_change_has_zero_growth_rate():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change(
        direction=MarketChangeDirection.STABLE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.STABLE,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.growth_rate == 0.0


def test_medium_term_projection_exceeds_short_term_for_growth():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.INCREASE,
    )

    model = ForecastingModel()

    short_term = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    medium_term = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert medium_term.projected_value >= short_term.projected_value


def test_long_term_projection_exceeds_medium_term_for_growth():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.INCREASE,
    )

    model = ForecastingModel()

    medium_term = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    long_term = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.LONG_TERM,
    )

    assert long_term.projected_value >= medium_term.projected_value


def test_declining_projection_decreases_value():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.DECREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.DECLINE,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.projected_value < result.baseline


def test_stable_projection_preserves_baseline():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change(
        direction=MarketChangeDirection.STABLE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.STABLE,
        ForecastHorizon.LONG_TERM,
    )

    assert result.projected_value == result.baseline
    assert result.projection_change == 0.0


def test_projection_is_bounded():
    history = make_history([
        make_signal("s1", strength=1.0),
        make_signal("s2", days=5, strength=1.0),
        make_signal("s3", days=10, strength=1.0),
        make_signal("s4", days=15, strength=1.0),
        make_signal("s5", days=20, strength=1.0),
    ])

    change = make_change(
        magnitude=1.0,
        direction=MarketChangeDirection.INCREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.LONG_TERM,
    )

    assert 0.0 <= result.projected_value <= 1.0


def test_projection_change_is_positive_for_growth():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.INCREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.projection_change > 0.0


def test_projection_change_is_negative_for_decline():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change(
        direction=MarketChangeDirection.DECREASE,
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.DECLINE,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.projection_change < 0.0


def test_evidence_ids_are_deduplicated():
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
        evidence_ids=("e2", "e4"),
    )

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert result.evidence_ids == (
        "e2",
        "e4",
        "e1",
        "e3",
    )


def test_observation_metadata_is_preserved():
    history = make_history([
        make_signal("s1"),
        make_signal("s2", days=10),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert result.entity_id == history.entity_id
    assert result.signal_type == history.signal_type
    assert result.observation_count == 2
    assert result.first_observed_at == history.first_observed_at
    assert result.latest_observed_at == history.latest_observed_at


def test_result_is_forecast_model_result():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert isinstance(result, ForecastModelResult)


def test_result_to_dict_is_explainable():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    data = result.to_dict()

    assert data["entity_id"] == "market-1"
    assert data["trend_direction"] == "upward"
    assert data["forecast_direction"] == "growth"
    assert data["horizon"] == "short_term"
    assert isinstance(data["evidence_ids"], list)
    assert data["explanation"]


def test_explanation_contains_projection_details():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    result = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert "baseline" in result.explanation
    assert "growth rate" in result.explanation
    assert "projected" in result.explanation


def test_model_rejects_invalid_history():
    with pytest.raises(
        TypeError,
        match="history must be a TemporalSignalHistory",
    ):
        ForecastingModel().project(
            "invalid",  # type: ignore[arg-type]
            make_change(),
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        )


def test_model_rejects_invalid_change():
    history = make_history([
        make_signal("s1"),
    ])

    with pytest.raises(
        TypeError,
        match="change must be a MarketChangeAnalysis",
    ):
        ForecastingModel().project(
            history,
            "invalid",  # type: ignore[arg-type]
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        )


def test_model_rejects_invalid_forecast_direction():
    history = make_history([
        make_signal("s1"),
    ])

    with pytest.raises(
        TypeError,
        match="forecast_direction must be a ForecastDirection",
    ):
        ForecastingModel().project(
            history,
            make_change(),
            "growth",  # type: ignore[arg-type]
            ForecastHorizon.SHORT_TERM,
        )


def test_model_rejects_invalid_horizon():
    history = make_history([
        make_signal("s1"),
    ])

    with pytest.raises(
        TypeError,
        match="horizon must be a ForecastHorizon",
    ):
        ForecastingModel().project(
            history,
            make_change(),
            ForecastDirection.GROWTH,
            "short_term",  # type: ignore[arg-type]
        )


def test_model_rejects_entity_mismatch():
    history = make_history([
        make_signal("s1", entity_id="market-a"),
    ])

    change = make_change(
        entity_id="market-b",
    )

    with pytest.raises(
        ValueError,
        match="same entity",
    ):
        ForecastingModel().project(
            history,
            change,
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        )


def test_project_from_detection_uses_detection_direction_and_horizon():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    detection = make_detection(
        direction=ForecastDirection.GROWTH,
        horizon=ForecastHorizon.LONG_TERM,
    )

    result = ForecastingModel().project_from_detection(
        history,
        change,
        detection,
    )

    assert result.forecast_direction == ForecastDirection.GROWTH
    assert result.horizon == ForecastHorizon.LONG_TERM


def test_project_from_detection_rejects_missing_direction():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    with pytest.raises(
        TypeError,
        match="forecast direction",
    ):
        ForecastingModel().project_from_detection(
            history,
            change,
            object(),
        )


def test_project_many_requires_list():
    with pytest.raises(
        TypeError,
        match="inputs must be a list",
    ):
        ForecastingModel().project_many(
            "invalid"  # type: ignore[arg-type]
        )


def test_project_many_returns_all_results():
    history_a = make_history([
        make_signal(
            "s1",
            entity_id="a",
        ),
    ])

    history_b = make_history([
        make_signal(
            "s2",
            entity_id="b",
        ),
    ])

    change_a = make_change(entity_id="a")
    change_b = make_change(entity_id="b")

    results = ForecastingModel().project_many([
        (
            history_a,
            change_a,
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        ),
        (
            history_b,
            change_b,
            ForecastDirection.GROWTH,
            ForecastHorizon.MEDIUM_TERM,
        ),
    ])

    assert len(results) == 2
    assert {result.entity_id for result in results} == {
        "a",
        "b",
    }


def test_project_many_is_sorted_deterministically():
    history_old = make_history([
        make_signal(
            "old",
            entity_id="old",
        ),
    ])

    history_new = make_history([
        make_signal(
            "new",
            entity_id="new",
            days=20,
        ),
    ])

    results = ForecastingModel().project_many([
        (
            history_new,
            make_change(entity_id="new"),
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        ),
        (
            history_old,
            make_change(entity_id="old"),
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        ),
    ])

    assert results[0].entity_id == "old"
    assert results[1].entity_id == "new"


def test_empty_project_many_returns_empty_list():
    assert ForecastingModel().project_many([]) == []


def test_convenience_function_matches_model():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    expected = ForecastingModel().project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    actual = project_forecast(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.SHORT_TERM,
    )

    assert actual == expected


def test_convenience_many_function_matches_model():
    history = make_history([
        make_signal("s1"),
    ])

    change = make_change()

    inputs = [
        (
            history,
            change,
            ForecastDirection.GROWTH,
            ForecastHorizon.SHORT_TERM,
        )
    ]

    expected = ForecastingModel().project_many(inputs)
    actual = project_forecast_many(inputs)

    assert actual == expected


def test_forecast_strength_inputs_are_deterministic():
    history = make_history([
        make_signal("s1", strength=0.5),
        make_signal("s2", days=10, strength=0.7),
    ])

    change = make_change(
        magnitude=0.6,
    )

    model = ForecastingModel()

    first = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    second = model.project(
        history,
        change,
        ForecastDirection.GROWTH,
        ForecastHorizon.MEDIUM_TERM,
    )

    assert first == second
