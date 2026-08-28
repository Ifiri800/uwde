from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.market.change import (
    MarketChangeAnalysis,
    MarketChangeAnalyzer,
    MarketChangeDirection,
    MarketChangeType,
    analyze_market_change,
    analyze_market_changes,
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
    signal_type: SignalType,
    *,
    entity_id: str = "entity-1",
    days: int = 0,
    confidence: float = 0.8,
    strength: float = 0.7,
    previous_value=None,
    current_value=None,
    evidence_ids=None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        detected_at=BASE_TIME + timedelta(days=days),
        confidence=confidence,
        strength=strength,
        previous_value=previous_value,
        current_value=current_value,
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


def test_company_expansion_creates_expansion_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.COMPANY_EXPANSION,
        )
    ])

    result = analyze_market_change(history)

    assert isinstance(result, MarketChangeAnalysis)
    assert result.change_type == MarketChangeType.EXPANSION
    assert result.direction == MarketChangeDirection.INCREASE


def test_new_company_creates_expansion_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.NEW_COMPANY,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.EXPANSION
    assert result.direction == MarketChangeDirection.INCREASE


def test_product_launch_creates_product_launch_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.PRODUCT_LAUNCH
    assert result.direction == MarketChangeDirection.INCREASE


def test_new_product_creates_product_launch_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.NEW_PRODUCT,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.PRODUCT_LAUNCH


def test_hiring_creates_hiring_growth_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.HIRING_SIGNAL,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.HIRING_GROWTH
    assert result.direction == MarketChangeDirection.INCREASE


def test_funding_creates_funding_growth_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.FUNDING_SIGNAL,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.FUNDING_GROWTH


def test_technology_adoption_creates_technology_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.TECHNOLOGY_ADOPTION,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.TECHNOLOGY_ADOPTION


def test_tender_creates_demand_growth_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.TENDER_OPPORTUNITY,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.DEMAND_GROWTH
    assert result.direction == MarketChangeDirection.INCREASE


def test_buyer_intent_creates_demand_growth_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.BUYER_INTENT,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.DEMAND_GROWTH


def test_market_growth_creates_expansion_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.EXPANSION


def test_procurement_creates_expansion_change():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PROCUREMENT_SIGNAL,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.EXPANSION


def test_competitor_change_is_classified():
    history = make_history([
        make_signal(
            "s1",
            SignalType.COMPETITOR_CHANGE,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.COMPETITIVE_CHANGE
    assert result.direction == MarketChangeDirection.INCREASE


def test_price_increase_is_detected():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            previous_value=100,
            current_value=120,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.PRICE_INCREASE
    assert result.direction == MarketChangeDirection.INCREASE


def test_price_decrease_is_detected():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            previous_value=120,
            current_value=100,
        )
    ])

    result = analyze_market_change(history)

    assert result.change_type == MarketChangeType.PRICE_DECREASE
    assert result.direction == MarketChangeDirection.DECREASE


def test_price_change_with_equal_values_is_stable():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            previous_value=100,
            current_value=100,
        )
    ])

    result = analyze_market_change(history)

    assert result.direction == MarketChangeDirection.STABLE


def test_non_numeric_price_change_is_stable():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            previous_value={"price": "unknown"},
            current_value={"price": "lower"},
        )
    ])

    result = analyze_market_change(history)

    assert result.direction == MarketChangeDirection.STABLE


def test_repeated_activity_increases_magnitude():
    history = make_history([
        make_signal(
            f"s{i}",
            SignalType.HIRING_SIGNAL,
            days=i * 10,
            strength=0.8,
        )
        for i in range(5)
    ])

    result = analyze_market_change(history)

    assert result.magnitude >= 0.8


def test_stronger_signal_produces_nonzero_magnitude():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
            strength=0.9,
        )
    ])

    result = analyze_market_change(history)

    assert result.magnitude > 0.0
    assert result.magnitude <= 1.0


def test_relative_numeric_change_contributes_to_magnitude():
    history = make_history([
        make_signal(
            "s1",
            SignalType.PRICE_CHANGE,
            strength=0.5,
            previous_value=100,
            current_value=200,
        )
    ])

    result = analyze_market_change(history)

    assert result.magnitude > 0.5


def test_confidence_is_average_of_signal_confidences():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
            confidence=0.6,
        ),
        make_signal(
            "s2",
            SignalType.MARKET_GROWTH,
            days=5,
            confidence=0.8,
        ),
        make_signal(
            "s3",
            SignalType.MARKET_GROWTH,
            days=10,
            confidence=1.0,
        ),
    ])

    result = analyze_market_change(history)

    assert result.confidence == 0.8


def test_evidence_ids_are_deduplicated_and_preserved():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
            evidence_ids=["e1", "e2"],
        ),
        make_signal(
            "s2",
            SignalType.MARKET_GROWTH,
            days=5,
            evidence_ids=["e2", "e3"],
        ),
    ])

    result = analyze_market_change(history)

    assert result.evidence_ids == (
        "e1",
        "e2",
        "e3",
    )


def test_observation_metadata_is_preserved():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
            entity_id="market-7",
        ),
        make_signal(
            "s2",
            SignalType.MARKET_GROWTH,
            entity_id="market-7",
            days=10,
        ),
    ])

    result = analyze_market_change(history)

    assert result.entity_id == "market-7"
    assert result.observation_count == 2
    assert result.first_observed_at == BASE_TIME
    assert result.latest_observed_at == (
        BASE_TIME + timedelta(days=10)
    )


def test_multiple_changes_are_sorted_deterministically():
    histories = [
        make_history([
            make_signal(
                "s1",
                SignalType.MARKET_GROWTH,
                entity_id="b",
                days=10,
            )
        ]),
        make_history([
            make_signal(
                "s2",
                SignalType.PRICE_CHANGE,
                entity_id="a",
                days=5,
                previous_value=100,
                current_value=120,
            )
        ]),
    ]

    results = analyze_market_changes(histories)

    assert len(results) == 2
    assert results[0].entity_id == "a"
    assert results[1].entity_id == "b"


def test_empty_history_list_returns_empty_list():
    assert analyze_market_changes([]) == []


def test_analyzer_rejects_invalid_history():
    with pytest.raises(
        TypeError,
        match="TemporalSignalHistory",
    ):
        MarketChangeAnalyzer().analyze("invalid")


def test_analyzer_rejects_invalid_history_signal_type():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
        )
    ])

    invalid = TemporalSignalHistory(
        signal_type="not-a-valid-signal",
        entity_id=history.entity_id,
        signals=history.signals,
        first_observed_at=history.first_observed_at,
        latest_observed_at=history.latest_observed_at,
        observation_count=history.observation_count,
        repeated_observation_count=history.repeated_observation_count,
        time_span_seconds=history.time_span_seconds,
    )

    with pytest.raises(
        ValueError,
        match="valid SignalType",
    ):
        MarketChangeAnalyzer().analyze(invalid)


def test_analyzer_rejects_invalid_histories_argument():
    with pytest.raises(
        TypeError,
        match="histories must be a list",
    ):
        MarketChangeAnalyzer().analyze_many(
            "invalid"  # type: ignore[arg-type]
        )


def test_to_dict_is_explainable():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
            evidence_ids=["e1"],
        )
    ])

    result = analyze_market_change(history)
    data = result.to_dict()

    assert data["entity_id"] == "entity-1"
    assert data["change_type"] == "expansion"
    assert data["direction"] == "increase"
    assert data["signal_type"] == "market_growth"
    assert data["observation_count"] == 1
    assert data["magnitude"] == result.magnitude
    assert data["confidence"] == result.confidence
    assert data["evidence_ids"] == ["e1"]
    assert "Market change detected" in data["explanation"]


def test_convenience_functions_match_analyzer():
    history = make_history([
        make_signal(
            "s1",
            SignalType.MARKET_GROWTH,
        )
    ])

    direct = MarketChangeAnalyzer().analyze(history)
    convenience = analyze_market_change(history)

    assert convenience == direct


def test_convenience_many_function_matches_analyzer():
    histories = [
        make_history([
            make_signal(
                "s1",
                SignalType.MARKET_GROWTH,
            )
        ])
    ]

    direct = MarketChangeAnalyzer().analyze_many(histories)
    convenience = analyze_market_changes(histories)

    assert convenience == direct
