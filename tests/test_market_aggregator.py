from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalStatus,
    SignalType,
)
from backend.app.services.intelligence.market.aggregator import (
    MarketAggregator,
    MarketDirection,
    MarketIntelligence,
    aggregate_market_intelligence,
)


def make_signal(
    signal_id: str,
    signal_type: SignalType,
    *,
    market_id: str = "market-1",
    confidence: float = 0.8,
    strength: float = 0.7,
    evidence_ids: list[str] | None = None,
    status: SignalStatus = SignalStatus.DETECTED,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=market_id,
        detected_at=datetime.now(timezone.utc),
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or [],
        status=status,
    )


def make_evidence(
    evidence_id: str,
    *,
    confidence: float = 0.9,
    entity_id: str = "market-1",
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_url="https://example.com/source",
        entity_id=entity_id,
        observed_value={"value": True},
        confidence=confidence,
    )


class TestMarketIntelligence:
    def test_valid_market_intelligence(self):
        result = MarketIntelligence(
            market_id="market-1",
            signal_count=2,
            average_score=0.7,
            average_confidence=0.8,
            signal_type_diversity=1.0,
            evidence_coverage=0.5,
            corroborated_signal_count=1,
            growth_signal_count=2,
            decline_signal_count=0,
            overall_score=0.75,
            direction=MarketDirection.GROWTH,
            explanation="Market assessment is growth.",
        )

        assert result.market_id == "market-1"
        assert result.direction == MarketDirection.GROWTH

    def test_empty_market_id_rejected(self):
        with pytest.raises(ValueError, match="market_id is required"):
            MarketIntelligence(
                market_id="",
                signal_count=0,
                average_score=0.0,
                average_confidence=0.0,
                signal_type_diversity=0.0,
                evidence_coverage=0.0,
                corroborated_signal_count=0,
                growth_signal_count=0,
                decline_signal_count=0,
                overall_score=0.0,
                direction=MarketDirection.STABLE,
                explanation="No signals.",
            )

    def test_invalid_score_rejected(self):
        with pytest.raises(ValueError):
            MarketIntelligence(
                market_id="market-1",
                signal_count=1,
                average_score=1.1,
                average_confidence=0.5,
                signal_type_diversity=0.5,
                evidence_coverage=0.5,
                corroborated_signal_count=0,
                growth_signal_count=1,
                decline_signal_count=0,
                overall_score=0.5,
                direction=MarketDirection.GROWTH,
                explanation="Assessment.",
            )

    def test_negative_signal_count_rejected(self):
        with pytest.raises(ValueError, match="signal_count cannot be negative"):
            MarketIntelligence(
                market_id="market-1",
                signal_count=-1,
                average_score=0.0,
                average_confidence=0.0,
                signal_type_diversity=0.0,
                evidence_coverage=0.0,
                corroborated_signal_count=0,
                growth_signal_count=0,
                decline_signal_count=0,
                overall_score=0.0,
                direction=MarketDirection.STABLE,
                explanation="Assessment.",
            )

    def test_to_dict(self):
        result = MarketIntelligence(
            market_id="market-1",
            signal_count=1,
            average_score=0.5,
            average_confidence=0.6,
            signal_type_diversity=1.0,
            evidence_coverage=1.0,
            corroborated_signal_count=1,
            growth_signal_count=1,
            decline_signal_count=0,
            overall_score=0.7,
            direction=MarketDirection.GROWTH,
            explanation="Assessment.",
        )

        data = result.to_dict()

        assert data["market_id"] == "market-1"
        assert data["direction"] == "growth"
        assert data["signal_count"] == 1


class TestMarketAggregator:
    def test_empty_signals_return_stable_empty_result(self):
        result = MarketAggregator().aggregate(
            "market-1",
            [],
        )

        assert result.signal_count == 0
        assert result.overall_score == 0.0
        assert result.direction == MarketDirection.STABLE
        assert "No market signals" in result.explanation

    def test_signals_for_other_market_are_ignored(self):
        signal = make_signal(
            "signal-1",
            SignalType.NEW_COMPANY,
            market_id="other-market",
        )

        result = MarketAggregator().aggregate(
            "market-1",
            [signal],
        )

        assert result.signal_count == 0
        assert result.direction == MarketDirection.STABLE

    def test_growth_direction(self):
        signals = [
            make_signal("s1", SignalType.NEW_COMPANY),
            make_signal("s2", SignalType.PRODUCT_LAUNCH),
            make_signal("s3", SignalType.COMPANY_EXPANSION),
            make_signal("s4", SignalType.COMPETITOR_CHANGE),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.signal_count == 4
        assert result.growth_signal_count == 3
        assert result.decline_signal_count == 1
        assert result.direction == MarketDirection.GROWTH

    def test_decline_direction(self):
        signals = [
            make_signal("s1", SignalType.COMPETITOR_CHANGE),
            make_signal("s2", SignalType.PRICE_CHANGE),
            make_signal("s3", SignalType.NEW_COMPANY),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.growth_signal_count == 1
        assert result.decline_signal_count == 2
        assert result.direction == MarketDirection.DECLINE

    def test_stable_direction_when_counts_are_equal(self):
        signals = [
            make_signal("s1", SignalType.NEW_COMPANY),
            make_signal("s2", SignalType.COMPETITOR_CHANGE),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.growth_signal_count == 1
        assert result.decline_signal_count == 1
        assert result.direction == MarketDirection.STABLE

    def test_signal_type_diversity(self):
        signals = [
            make_signal("s1", SignalType.NEW_COMPANY),
            make_signal("s2", SignalType.NEW_COMPANY),
            make_signal("s3", SignalType.PRODUCT_LAUNCH),
            make_signal("s4", SignalType.PRICE_CHANGE),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.signal_type_diversity == 0.75

    def test_evidence_coverage(self):
        signals = [
            make_signal(
                "s1",
                SignalType.NEW_COMPANY,
                evidence_ids=["e1"],
            ),
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
            ),
            make_signal(
                "s3",
                SignalType.HIRING_SIGNAL,
                evidence_ids=["e2"],
            ),
            make_signal(
                "s4",
                SignalType.MARKET_GROWTH,
            ),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.evidence_coverage == 0.5

    def test_corroborated_signal_count(self):
        signals = [
            make_signal(
                "s1",
                SignalType.NEW_COMPANY,
                evidence_ids=["e1", "e2"],
            ),
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
                evidence_ids=["e3"],
            ),
        ]

        evidence = [
            make_evidence("e1"),
            make_evidence("e2"),
            make_evidence("e3"),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
            evidence,
        )

        assert result.corroborated_signal_count == 1

    def test_average_confidence(self):
        signals = [
            make_signal(
                "s1",
                SignalType.NEW_COMPANY,
                confidence=0.8,
            ),
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
                confidence=0.6,
            ),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
        )

        assert result.average_confidence == 0.7

    def test_overall_score_is_bounded(self):
        signals = [
            make_signal(
                "s1",
                SignalType.NEW_COMPANY,
                confidence=1.0,
                strength=1.0,
                evidence_ids=["e1", "e2"],
            ),
        ]

        evidence = [
            make_evidence("e1", confidence=1.0),
            make_evidence("e2", confidence=1.0),
        ]

        result = MarketAggregator().aggregate(
            "market-1",
            signals,
            evidence,
        )

        assert 0.0 <= result.overall_score <= 1.0

    def test_explanation_contains_core_metrics(self):
        signal = make_signal(
            "s1",
            SignalType.NEW_COMPANY,
            evidence_ids=["e1"],
        )

        result = MarketAggregator().aggregate(
            "market-1",
            [signal],
        )

        assert "1 signals" in result.explanation
        assert "confidence" in result.explanation
        assert "evidence coverage" in result.explanation
        assert "growth-oriented" in result.explanation

    def test_invalid_market_id_rejected(self):
        with pytest.raises(ValueError, match="market_id is required"):
            MarketAggregator().aggregate("", [])

    def test_non_list_signals_rejected(self):
        with pytest.raises(TypeError, match="signals must be a list"):
            MarketAggregator().aggregate(
                "market-1",
                None,  # type: ignore[arg-type]
            )

    def test_invalid_signal_type_rejected(self):
        with pytest.raises(
            TypeError,
            match="signals must contain only Signal objects",
        ):
            MarketAggregator().aggregate(
                "market-1",
                ["invalid"],  # type: ignore[list-item]
            )

    def test_invalid_evidence_type_rejected(self):
        signal = make_signal(
            "s1",
            SignalType.NEW_COMPANY,
        )

        with pytest.raises(
            TypeError,
            match="evidence must contain only Evidence objects",
        ):
            MarketAggregator().aggregate(
                "market-1",
                [signal],
                ["invalid"],  # type: ignore[list-item]
            )

    def test_convenience_function(self):
        signal = make_signal(
            "s1",
            SignalType.NEW_COMPANY,
        )

        result = aggregate_market_intelligence(
            "market-1",
            [signal],
        )

        assert isinstance(result, MarketIntelligence)
        assert result.signal_count == 1


def test_market_direction_values():
    assert MarketDirection.GROWTH.value == "growth"
    assert MarketDirection.DECLINE.value == "decline"
    assert MarketDirection.STABLE.value == "stable"
