from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.domain.signals import SignalType
from backend.app.services.intelligence.market.detection import (
    MarketDetectionEngine,
    detect_market_signal,
    detect_market_signals,
)
from backend.app.services.intelligence.market.entities import (
    MarketObservation,
)
from backend.app.services.intelligence.market.observations import (
    MarketObservationType,
)


def make_observation(
    observation_id: str,
    observation_type: MarketObservationType,
    *,
    market_id: str = "market-1",
    value: object = True,
    confidence: float = 0.85,
    evidence_ids: tuple[str, ...] = (),
) -> MarketObservation:
    return MarketObservation(
        observation_id=observation_id,
        market_id=market_id,
        observation_type=observation_type,
        value=value,
        source_url="https://example.com/source",
        observed_at=datetime.now(timezone.utc),
        confidence=confidence,
        evidence_ids=evidence_ids,
    )


class TestMarketDetectionEngine:
    def test_detect_single_observation(self):
        observation = make_observation(
            "obs-001",
            MarketObservationType.COMPANY_ENTRY,
        )

        signals = MarketDetectionEngine().detect(observation)

        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.NEW_COMPANY
        assert signals[0].entity_id == "market-1"

    def test_signal_id_is_derived_from_observation(self):
        observation = make_observation(
            "obs-002",
            MarketObservationType.PRODUCT_LAUNCH,
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.signal_id == "market-signal:obs-002"

    def test_confidence_is_preserved(self):
        observation = make_observation(
            "obs-003",
            MarketObservationType.PRICE_CHANGE,
            confidence=0.63,
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.confidence == 0.63
        assert signal.strength == 0.63

    def test_evidence_is_preserved(self):
        observation = make_observation(
            "obs-004",
            MarketObservationType.FUNDING_EVENT,
            evidence_ids=("e1", "e2"),
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.evidence_ids == ["e1", "e2"]

    def test_value_is_preserved(self):
        observation = make_observation(
            "obs-005",
            MarketObservationType.PRICE_CHANGE,
            value={"old": 100, "new": 125},
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.current_value == {
            "old": 100,
            "new": 125,
        }

    def test_observed_at_is_preserved(self):
        observed_at = datetime(
            2026,
            8,
            28,
            10,
            30,
            tzinfo=timezone.utc,
        )

        observation = MarketObservation(
            observation_id="obs-006",
            market_id="market-1",
            observation_type=MarketObservationType.MARKET_EXPANSION,
            value={"region": "West Africa"},
            source_url="https://example.com/source",
            observed_at=observed_at,
            confidence=0.9,
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.detected_at == observed_at

    def test_metadata_contains_market_observation_context(self):
        observation = make_observation(
            "obs-007",
            MarketObservationType.GEOGRAPHIC_EXPANSION,
        )

        signal = MarketDetectionEngine().detect(
            observation
        )[0]

        assert signal.metadata["source"] == "market"
        assert signal.metadata["observation_id"] == "obs-007"
        assert (
            signal.metadata["observation_type"]
            == "geographic_expansion"
        )
        assert (
            signal.metadata["source_url"]
            == "https://example.com/source"
        )

    def test_invalid_observation_type_is_rejected_by_observation(self):
        with pytest.raises(ValueError):
            MarketObservation(
                observation_id="obs-008",
                market_id="market-1",
                observation_type="invalid",
                value=True,
                source_url="https://example.com/source",
            )

    def test_invalid_observation_object_is_rejected(self):
        with pytest.raises(
            TypeError,
            match="observation must be a MarketObservation",
        ):
            MarketDetectionEngine().detect(
                "invalid"  # type: ignore[arg-type]
            )

    def test_detect_many(self):
        observations = [
            make_observation(
                "obs-009",
                MarketObservationType.COMPANY_ENTRY,
            ),
            make_observation(
                "obs-010",
                MarketObservationType.PRODUCT_LAUNCH,
            ),
            make_observation(
                "obs-011",
                MarketObservationType.HIRING_GROWTH,
            ),
        ]

        signals = MarketDetectionEngine().detect_many(
            observations
        )

        assert len(signals) == 3
        assert [
            signal.signal_type
            for signal in signals
        ] == [
            SignalType.NEW_COMPANY,
            SignalType.PRODUCT_LAUNCH,
            SignalType.HIRING_SIGNAL,
        ]

    def test_detect_many_preserves_order(self):
        observations = [
            make_observation(
                "obs-a",
                MarketObservationType.PRICE_CHANGE,
            ),
            make_observation(
                "obs-b",
                MarketObservationType.FUNDING_EVENT,
            ),
        ]

        signals = MarketDetectionEngine().detect_many(
            observations
        )

        assert [
            signal.signal_id
            for signal in signals
        ] == [
            "market-signal:obs-a",
            "market-signal:obs-b",
        ]

    def test_duplicate_observation_ids_are_suppressed(self):
        observation = make_observation(
            "obs-012",
            MarketObservationType.PARTNERSHIP,
        )

        signals = MarketDetectionEngine().detect_many(
            [observation, observation]
        )

        assert len(signals) == 1
        assert signals[0].signal_id == "market-signal:obs-012"

    def test_invalid_observation_list_is_rejected(self):
        with pytest.raises(
            TypeError,
            match="observations must be a list",
        ):
            MarketDetectionEngine().detect_many(
                None  # type: ignore[arg-type]
            )

    def test_invalid_item_in_observation_list_is_rejected(self):
        observation = make_observation(
            "obs-013",
            MarketObservationType.COMPANY_ENTRY,
        )

        with pytest.raises(
            TypeError,
            match="observations must contain only",
        ):
            MarketDetectionEngine().detect_many(
                [observation, "invalid"]  # type: ignore[list-item]
            )


class TestMarketDetectionConvenienceFunctions:
    def test_detect_market_signal(self):
        observation = make_observation(
            "obs-014",
            MarketObservationType.DEMAND_SIGNAL,
        )

        signals = detect_market_signal(observation)

        assert len(signals) == 1
        assert signals[0].signal_type == SignalType.BUYER_INTENT

    def test_detect_market_signals(self):
        observations = [
            make_observation(
                "obs-015",
                MarketObservationType.TECHNOLOGY_ADOPTION,
            ),
            make_observation(
                "obs-016",
                MarketObservationType.CAPACITY_CHANGE,
            ),
        ]

        signals = detect_market_signals(observations)

        assert len(signals) == 2
        assert signals[0].signal_type == SignalType.TECHNOLOGY_ADOPTION
        assert signals[1].signal_type == SignalType.COMPANY_EXPANSION


def test_all_market_observation_types_have_signal_mappings():
    observations = [
        MarketObservationType.COMPANY_ENTRY,
        MarketObservationType.COMPANY_EXIT,
        MarketObservationType.PRODUCT_LAUNCH,
        MarketObservationType.PRODUCT_DISCONTINUATION,
        MarketObservationType.PRICE_CHANGE,
        MarketObservationType.HIRING_GROWTH,
        MarketObservationType.FUNDING_EVENT,
        MarketObservationType.PARTNERSHIP,
        MarketObservationType.MARKET_EXPANSION,
        MarketObservationType.GEOGRAPHIC_EXPANSION,
        MarketObservationType.TECHNOLOGY_ADOPTION,
        MarketObservationType.CAPACITY_CHANGE,
        MarketObservationType.DEMAND_SIGNAL,
    ]

    for index, observation_type in enumerate(observations):
        observation = make_observation(
            f"mapping-{index}",
            observation_type,
        )

        signals = detect_market_signal(observation)

        assert len(signals) == 1
        assert signals[0].signal_type is not None
