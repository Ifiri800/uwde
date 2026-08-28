from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.forecasting.model import (
    ForecastModelResult,
    TrendDirection,
)
from backend.app.services.intelligence.forecasting.detection import (
    ForecastDirection,
    ForecastHorizon,
)
from backend.app.services.intelligence.forecasting.confidence import (
    ForecastConfidenceAnalysis,
)
from backend.app.services.intelligence.forecasting.scenario import (
    ForecastScenario,
    ScenarioForecast,
    ScenarioForecastingAnalyzer,
    forecast_scenarios,
    forecast_scenarios_many,
)


def make_model(
    entity_id="company-1",
    baseline=0.40,
    projected_value=0.60,
    projection_change=0.50,
):
    return ForecastModelResult(
        entity_id=entity_id,
        signal_type="company_expansion",
        trend_direction=TrendDirection.UPWARD,
        forecast_direction=ForecastDirection.GROWTH,
        horizon=ForecastHorizon.MEDIUM_TERM,
        baseline=baseline,
        growth_rate=0.25,
        projected_value=projected_value,
        projection_change=projection_change,
        observation_count=3,
        first_observed_at=datetime(
            2026, 1, 1, tzinfo=timezone.utc
        ),
        latest_observed_at=datetime(
            2026, 3, 1, tzinfo=timezone.utc
        ),
        evidence_ids=("e1", "e2"),
        explanation="Forecast model result.",
    )


def make_confidence(
    entity_id="company-1",
    confidence_score=0.80,
):
    return ForecastConfidenceAnalysis(
        entity_id=entity_id,
        signal_quality=0.80,
        historical_consistency=0.80,
        data_coverage=0.80,
        uncertainty=0.20,
        confidence_score=confidence_score,
        evidence_ids=("e1", "e2"),
        explanation="Forecast confidence assessment.",
    )


def test_returns_three_scenarios():
    result = forecast_scenarios(
        make_model(),
        make_confidence(),
    )

    assert len(result) == 3
    assert {
        item.scenario
        for item in result
    } == {
        ForecastScenario.BASELINE,
        ForecastScenario.OPTIMISTIC,
        ForecastScenario.CONSERVATIVE,
    }


def test_baseline_uses_model_projection():
    result = forecast_scenarios(
        make_model(
            baseline=0.40,
            projected_value=0.60,
            projection_change=0.50,
        ),
        make_confidence(),
    )

    baseline = next(
        item for item in result
        if item.scenario == ForecastScenario.BASELINE
    )

    assert baseline.projected_value == 0.80
    assert baseline.projection_change == 0.50


def test_optimistic_exceeds_baseline_for_growth():
    result = forecast_scenarios(
        make_model(
            baseline=0.30,
            projected_value=0.50,
            projection_change=0.666667,
        ),
        make_confidence(),
    )

    baseline = next(
        item for item in result
        if item.scenario == ForecastScenario.BASELINE
    )

    optimistic = next(
        item for item in result
        if item.scenario == ForecastScenario.OPTIMISTIC
    )

    assert optimistic.projected_value > baseline.projected_value
    assert optimistic.projection_change > baseline.projection_change


def test_conservative_is_below_baseline_for_growth():
    result = forecast_scenarios(
        make_model(
            baseline=0.30,
            projected_value=0.50,
            projection_change=0.666667,
        ),
        make_confidence(),
    )

    baseline = next(
        item for item in result
        if item.scenario == ForecastScenario.BASELINE
    )

    conservative = next(
        item for item in result
        if item.scenario == ForecastScenario.CONSERVATIVE
    )

    assert conservative.projected_value < baseline.projected_value
    assert conservative.projection_change < baseline.projection_change


def test_declining_forecast_produces_bounded_scenarios():
    model = make_model(
        baseline=0.60,
        projected_value=0.40,
        projection_change=-0.333333,
    )

    result = forecast_scenarios(
        model,
        make_confidence(),
    )

    for scenario in result:
        assert 0.0 <= scenario.projected_value <= 1.0
        assert -1.0 <= scenario.projection_change <= 1.0


def test_stable_projection_keeps_all_scenarios_stable():
    model = make_model(
        baseline=0.50,
        projected_value=0.50,
        projection_change=0.0,
    )

    result = forecast_scenarios(
        model,
        make_confidence(),
    )

    assert all(
        item.projected_value == 0.50
        for item in result
    )

    assert all(
        item.projection_change == 0.0
        for item in result
    )


def test_confidence_is_bounded():
    result = forecast_scenarios(
        make_model(),
        make_confidence(confidence_score=1.0),
    )

    for item in result:
        assert 0.0 <= item.confidence <= 1.0


def test_baseline_has_highest_confidence():
    result = forecast_scenarios(
        make_model(),
        make_confidence(confidence_score=0.90),
    )

    baseline = next(
        item for item in result
        if item.scenario == ForecastScenario.BASELINE
    )

    optimistic = next(
        item for item in result
        if item.scenario == ForecastScenario.OPTIMISTIC
    )

    conservative = next(
        item for item in result
        if item.scenario == ForecastScenario.CONSERVATIVE
    )

    assert baseline.confidence >= optimistic.confidence
    assert baseline.confidence >= conservative.confidence


def test_forecast_strength_field_is_not_required_by_scenario_layer():
    result = forecast_scenarios(
        make_model(),
        make_confidence(),
    )

    assert all(
        item.forecast_strength >= 0.0
        for item in result
    )


def test_entity_id_is_preserved():
    result = forecast_scenarios(
        make_model(entity_id="company-x"),
        make_confidence(entity_id="company-x"),
    )

    assert all(
        item.entity_id == "company-x"
        for item in result
    )


def test_explanations_are_scenario_specific():
    result = forecast_scenarios(
        make_model(),
        make_confidence(),
    )

    explanations = [
        item.explanation
        for item in result
    ]

    assert len(set(explanations)) == 3

    for item in result:
        assert item.scenario.value in item.explanation
        assert "projected value" in item.explanation


def test_result_is_scenario_forecast():
    result = forecast_scenarios(
        make_model(),
        make_confidence(),
    )

    assert all(
        isinstance(item, ScenarioForecast)
        for item in result
    )


def test_to_dict_is_explainable():
    result = forecast_scenarios(
        make_model(),
        make_confidence(),
    )

    data = result[0].to_dict()

    assert data["entity_id"] == "company-1"
    assert "scenario" in data
    assert "projected_value" in data
    assert "projection_change" in data
    assert "confidence" in data
    assert "forecast_strength" in data
    assert "explanation" in data


def test_analyzer_rejects_invalid_model():
    with pytest.raises(TypeError):
        ScenarioForecastingAnalyzer().analyze(
            object(),
            make_confidence(),
        )


def test_analyzer_rejects_invalid_confidence():
    with pytest.raises(TypeError):
        ScenarioForecastingAnalyzer().analyze(
            make_model(),
            object(),
        )


def test_analyzer_rejects_entity_mismatch():
    with pytest.raises(ValueError):
        ScenarioForecastingAnalyzer().analyze(
            make_model(entity_id="company-a"),
            make_confidence(entity_id="company-b"),
        )


def test_analyze_many_requires_list():
    with pytest.raises(TypeError):
        ScenarioForecastingAnalyzer().analyze_many(tuple())


def test_analyze_many_returns_all_scenarios():
    inputs = [
        (
            make_model(entity_id="company-a"),
            make_confidence(entity_id="company-a"),
        ),
        (
            make_model(entity_id="company-b"),
            make_confidence(entity_id="company-b"),
        ),
    ]

    result = forecast_scenarios_many(inputs)

    assert len(result) == 6


def test_analyze_many_is_sorted_deterministically():
    inputs = [
        (
            make_model(entity_id="company-b"),
            make_confidence(entity_id="company-b"),
        ),
        (
            make_model(entity_id="company-a"),
            make_confidence(entity_id="company-a"),
        ),
    ]

    result = forecast_scenarios_many(inputs)

    keys = [
        (item.entity_id, item.scenario.value)
        for item in result
    ]

    assert keys == sorted(keys)


def test_empty_input_returns_empty_list():
    assert forecast_scenarios_many([]) == []


def test_convenience_function_matches_analyzer():
    model = make_model()
    confidence = make_confidence()

    expected = ScenarioForecastingAnalyzer().analyze(
        model,
        confidence,
    )

    actual = forecast_scenarios(
        model,
        confidence,
    )

    assert actual == expected


def test_convenience_many_function_matches_analyzer():
    inputs = [
        (
            make_model(),
            make_confidence(),
        )
    ]

    expected = ScenarioForecastingAnalyzer().analyze_many(
        inputs
    )

    actual = forecast_scenarios_many(inputs)

    assert actual == expected


def test_scenario_results_are_deterministic():
    model = make_model()
    confidence = make_confidence()

    first = forecast_scenarios(
        model,
        confidence,
    )

    second = forecast_scenarios(
        model,
        confidence,
    )

    assert first == second
