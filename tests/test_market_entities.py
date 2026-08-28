from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.market import (
    Market,
    MarketObservation,
    MarketObservationType,
    MarketSegment,
)


def test_market_creates_valid_record():
    market = Market(
        market_id="market-1",
        name="Water Treatment",
        industry="Environmental Services",
        geography="Nigeria",
    )

    assert market.market_id == "market-1"
    assert market.name == "Water Treatment"


def test_market_requires_id():
    with pytest.raises(ValueError):
        Market(
            market_id="",
            name="Water Treatment",
            industry="Environmental Services",
        )


def test_market_requires_name():
    with pytest.raises(ValueError):
        Market(
            market_id="market-1",
            name="",
            industry="Environmental Services",
        )


def test_market_requires_industry():
    with pytest.raises(ValueError):
        Market(
            market_id="market-1",
            name="Water Treatment",
            industry="",
        )


def test_market_serializes():
    market = Market(
        market_id="market-1",
        name="Water Treatment",
        industry="Environmental Services",
        geography="Nigeria",
    )

    data = market.to_dict()

    assert data["market_id"] == "market-1"
    assert data["geography"] == "Nigeria"


def test_market_segment_creates_valid_record():
    segment = MarketSegment(
        segment_id="segment-1",
        market_id="market-1",
        name="Industrial Water Treatment",
    )

    assert segment.market_id == "market-1"


def test_market_segment_requires_market():
    with pytest.raises(ValueError):
        MarketSegment(
            segment_id="segment-1",
            market_id="",
            name="Industrial Water Treatment",
        )


def test_market_observation_creates_valid_record():
    observation = MarketObservation(
        observation_id="obs-1",
        market_id="market-1",
        observation_type=MarketObservationType.PRODUCT_LAUNCH.value,
        value={"product": "New Treatment System"},
        source_url="https://example.com/source",
        confidence=0.9,
    )

    assert observation.observation_id == "obs-1"
    assert observation.confidence == 0.9


def test_market_observation_requires_source():
    with pytest.raises(ValueError):
        MarketObservation(
            observation_id="obs-1",
            market_id="market-1",
            observation_type="product_launch",
            value="New product",
            source_url="",
        )


def test_market_observation_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        MarketObservation(
            observation_id="obs-1",
            market_id="market-1",
            observation_type="product_launch",
            value="New product",
            source_url="https://example.com",
            confidence=1.1,
        )


def test_market_observation_requires_timezone():
    with pytest.raises(ValueError):
        MarketObservation(
            observation_id="obs-1",
            market_id="market-1",
            observation_type="product_launch",
            value="New product",
            source_url="https://example.com",
            observed_at=datetime(2026, 1, 1),
        )


def test_market_observation_serializes_timestamp():
    observation = MarketObservation(
        observation_id="obs-1",
        market_id="market-1",
        observation_type="product_launch",
        value="New product",
        source_url="https://example.com",
        observed_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        confidence=0.95,
        evidence_ids=("evidence-1", "evidence-2"),
    )

    data = observation.to_dict()

    assert data["observed_at"].endswith("+00:00")
    assert data["evidence_ids"] == [
        "evidence-1",
        "evidence-2",
    ]


def test_market_observation_types_are_defined():
    assert (
        MarketObservationType.PRICE_CHANGE.value
        == "price_change"
    )

    assert (
        MarketObservationType.MARKET_EXPANSION.value
        == "market_expansion"
    )
