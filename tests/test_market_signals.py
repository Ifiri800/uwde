from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.domain.signals import SignalType
from backend.app.services.intelligence.market.entities import (
    MarketObservation,
)
from backend.app.services.intelligence.market.observations import (
    MarketObservationType,
)
from backend.app.services.intelligence.market.signals import (
    generate_market_signal,
    generate_market_signals,
    market_signal_type,
)


def make_observation(
    observation_type: MarketObservationType,
    *,
    value: object = "test",
    confidence: float = 0.8,
    evidence_ids: tuple[str, ...] = ("evidence-1",),
) -> MarketObservation:
    return MarketObservation(
        observation_id="obs-001",
        market_id="market-001",
        observation_type=observation_type,
        value=value,
        source_url="https://example.com/source",
        observed_at=datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
        confidence=confidence,
        evidence_ids=evidence_ids,
    )


@pytest.mark.parametrize(
    ("observation_type", "signal_type"),
    [
        (
            MarketObservationType.COMPANY_ENTRY,
            SignalType.NEW_COMPANY,
        ),
        (
            MarketObservationType.COMPANY_EXIT,
            SignalType.COMPETITOR_CHANGE,
        ),
        (
            MarketObservationType.PRODUCT_LAUNCH,
            SignalType.PRODUCT_LAUNCH,
        ),
        (
            MarketObservationType.PRODUCT_DISCONTINUATION,
            SignalType.COMPETITOR_CHANGE,
        ),
        (
            MarketObservationType.PRICE_CHANGE,
            SignalType.PRICE_CHANGE,
        ),
        (
            MarketObservationType.HIRING_GROWTH,
            SignalType.HIRING_SIGNAL,
        ),
        (
            MarketObservationType.FUNDING_EVENT,
            SignalType.FUNDING_SIGNAL,
        ),
        (
            MarketObservationType.PARTNERSHIP,
            SignalType.COMPANY_EXPANSION,
        ),
        (
            MarketObservationType.MARKET_EXPANSION,
            SignalType.MARKET_GROWTH,
        ),
        (
            MarketObservationType.GEOGRAPHIC_EXPANSION,
            SignalType.COMPANY_EXPANSION,
        ),
        (
            MarketObservationType.TECHNOLOGY_ADOPTION,
            SignalType.TECHNOLOGY_ADOPTION,
        ),
        (
            MarketObservationType.CAPACITY_CHANGE,
            SignalType.COMPANY_EXPANSION,
        ),
        (
            MarketObservationType.DEMAND_SIGNAL,
            SignalType.BUYER_INTENT,
        ),
    ],
)
def test_market_signal_mapping(
    observation_type: MarketObservationType,
    signal_type: SignalType,
):
    assert market_signal_type(observation_type) == signal_type


def test_market_signal_preserves_observation_context():
    observation = make_observation(
        MarketObservationType.PRICE_CHANGE,
        value={"old": 100, "new": 120},
        confidence=0.9,
        evidence_ids=("e1", "e2"),
    )

    signal = generate_market_signal(observation)

    assert signal.signal_id == "market-signal:obs-001"
    assert signal.signal_type == SignalType.PRICE_CHANGE
    assert signal.entity_id == "market-001"
    assert signal.confidence == 0.9
    assert signal.strength == 0.9
    assert signal.evidence_ids == ["e1", "e2"]
    assert signal.current_value == {"old": 100, "new": 120}
    assert signal.metadata["source"] == "market"
    assert signal.metadata["observation_id"] == "obs-001"
    assert signal.metadata["source_url"] == (
        "https://example.com/source"
    )


def test_market_signal_uses_observation_timestamp():
    observation = make_observation(
        MarketObservationType.MARKET_EXPANSION,
    )

    signal = generate_market_signal(observation)

    assert signal.detected_at == observation.observed_at


def test_generate_market_signals():
    observations = [
        make_observation(
            MarketObservationType.COMPANY_ENTRY,
        ),
        make_observation(
            MarketObservationType.DEMAND_SIGNAL,
        ),
    ]

    signals = generate_market_signals(observations)

    assert len(signals) == 2
    assert signals[0].signal_type == SignalType.NEW_COMPANY
    assert signals[1].signal_type == SignalType.BUYER_INTENT


def test_invalid_observation_type_is_rejected():
    with pytest.raises(ValueError):
        market_signal_type("invalid_type")


def test_invalid_observation_object_is_rejected():
    with pytest.raises(TypeError):
        generate_market_signal("not-an-observation")


def test_invalid_observation_collection_is_rejected():
    with pytest.raises(TypeError):
        generate_market_signals("not-a-list")
