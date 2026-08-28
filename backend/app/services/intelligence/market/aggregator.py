from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal
from backend.app.services.intelligence.scoring.scorer import (
    SignalScore,
    SignalScorer,
)


class MarketDirection(StrEnum):
    GROWTH = "growth"
    DECLINE = "decline"
    STABLE = "stable"


@dataclass(frozen=True)
class MarketIntelligence:
    """
    Explainable aggregate intelligence assessment for a market.
    """

    market_id: str
    signal_count: int
    average_score: float
    average_confidence: float
    signal_type_diversity: float
    evidence_coverage: float
    corroborated_signal_count: int
    growth_signal_count: int
    decline_signal_count: int
    overall_score: float
    direction: MarketDirection
    explanation: str

    def __post_init__(self) -> None:
        if not self.market_id.strip():
            raise ValueError("market_id is required")

        if self.signal_count < 0:
            raise ValueError("signal_count cannot be negative")

        for value in (
            self.average_score,
            self.average_confidence,
            self.signal_type_diversity,
            self.evidence_coverage,
            self.overall_score,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "intelligence score values must be between 0.0 and 1.0"
                )

        for value in (
            self.corroborated_signal_count,
            self.growth_signal_count,
            self.decline_signal_count,
        ):
            if value < 0:
                raise ValueError("signal counts cannot be negative")

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "signal_count": self.signal_count,
            "average_score": self.average_score,
            "average_confidence": self.average_confidence,
            "signal_type_diversity": self.signal_type_diversity,
            "evidence_coverage": self.evidence_coverage,
            "corroborated_signal_count": self.corroborated_signal_count,
            "growth_signal_count": self.growth_signal_count,
            "decline_signal_count": self.decline_signal_count,
            "overall_score": self.overall_score,
            "direction": self.direction.value,
            "explanation": self.explanation,
        }


class MarketAggregator:
    """
    Deterministically aggregates scored signals into market-level
    intelligence.

    The aggregator does not replace SignalScorer. It consumes the
    existing explainable signal scores and combines them with
    confidence, evidence coverage, corroboration, and directional
    signal balance.
    """

    OVERALL_SCORE_WEIGHT = 0.60
    CONFIDENCE_WEIGHT = 0.15
    DIVERSITY_WEIGHT = 0.10
    EVIDENCE_WEIGHT = 0.15

    GROWTH_SIGNAL_TYPES = {
        "new_company",
        "new_product",
        "product_launch",
        "company_expansion",
        "hiring_signal",
        "funding_signal",
        "market_growth",
        "technology_adoption",
        "buyer_intent",
    }

    DECLINE_SIGNAL_TYPES = {
        "competitor_change",
        "price_change",
    }

    def __init__(
        self,
        scorer: SignalScorer | None = None,
    ) -> None:
        self._scorer = scorer or SignalScorer()

    def aggregate(
        self,
        market_id: str,
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> MarketIntelligence:
        if not isinstance(market_id, str) or not market_id.strip():
            raise ValueError("market_id is required")

        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if not signals:
            return self._empty_result(market_id)

        if any(not isinstance(signal, Signal) for signal in signals):
            raise TypeError("signals must contain only Signal objects")

        evidence_records = evidence or []

        if not isinstance(evidence_records, list):
            raise TypeError("evidence must be a list")

        if any(
            not isinstance(item, Evidence)
            for item in evidence_records
        ):
            raise TypeError(
                "evidence must contain only Evidence objects"
            )

        market_signals = [
            signal
            for signal in signals
            if signal.entity_id == market_id
        ]

        if not market_signals:
            return self._empty_result(market_id)

        scored = [
            self._scorer.score(
                signal,
                evidence_records,
            )
            for signal in market_signals
        ]

        signal_count = len(market_signals)

        average_score = self._average(
            item.score for item in scored
        )

        average_confidence = self._average(
            signal.confidence
            for signal in market_signals
        )

        signal_type_diversity = (
            len({
                signal.signal_type.value
                for signal in market_signals
            })
            / signal_count
        )

        evidence_coverage = self._evidence_coverage(
            market_signals
        )

        corroborated_signal_count = sum(
            1
            for item in scored
            if item.corroboration_component >= 1.0
        )

        growth_signal_count = sum(
            1
            for signal in market_signals
            if signal.signal_type.value in self.GROWTH_SIGNAL_TYPES
        )

        decline_signal_count = sum(
            1
            for signal in market_signals
            if signal.signal_type.value in self.DECLINE_SIGNAL_TYPES
        )

        overall_score = (
            average_score * self.OVERALL_SCORE_WEIGHT
            + average_confidence * self.CONFIDENCE_WEIGHT
            + signal_type_diversity * self.DIVERSITY_WEIGHT
            + evidence_coverage * self.EVIDENCE_WEIGHT
        )

        overall_score = round(
            min(1.0, max(0.0, overall_score)),
            6,
        )

        direction = self._direction(
            growth_signal_count,
            decline_signal_count,
        )

        explanation = self._explanation(
            signal_count=signal_count,
            average_score=average_score,
            average_confidence=average_confidence,
            signal_type_diversity=signal_type_diversity,
            evidence_coverage=evidence_coverage,
            corroborated_signal_count=corroborated_signal_count,
            growth_signal_count=growth_signal_count,
            decline_signal_count=decline_signal_count,
            direction=direction,
        )

        return MarketIntelligence(
            market_id=market_id,
            signal_count=signal_count,
            average_score=round(average_score, 6),
            average_confidence=round(average_confidence, 6),
            signal_type_diversity=round(
                signal_type_diversity,
                6,
            ),
            evidence_coverage=round(
                evidence_coverage,
                6,
            ),
            corroborated_signal_count=corroborated_signal_count,
            growth_signal_count=growth_signal_count,
            decline_signal_count=decline_signal_count,
            overall_score=overall_score,
            direction=direction,
            explanation=explanation,
        )

    @staticmethod
    def _average(values) -> float:
        values = list(values)

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _evidence_coverage(
        signals: list[Signal],
    ) -> float:
        if not signals:
            return 0.0

        supported = sum(
            1
            for signal in signals
            if signal.evidence_ids
        )

        return supported / len(signals)

    @staticmethod
    def _direction(
        growth_signal_count: int,
        decline_signal_count: int,
    ) -> MarketDirection:
        if growth_signal_count > decline_signal_count:
            return MarketDirection.GROWTH

        if decline_signal_count > growth_signal_count:
            return MarketDirection.DECLINE

        return MarketDirection.STABLE

    @staticmethod
    def _explanation(
        *,
        signal_count: int,
        average_score: float,
        average_confidence: float,
        signal_type_diversity: float,
        evidence_coverage: float,
        corroborated_signal_count: int,
        growth_signal_count: int,
        decline_signal_count: int,
        direction: MarketDirection,
    ) -> str:
        return (
            f"Market assessment is {direction.value} based on "
            f"{signal_count} signals. Average signal score is "
            f"{average_score:.3f}, confidence is "
            f"{average_confidence:.3f}, signal-type diversity is "
            f"{signal_type_diversity:.3f}, and evidence coverage is "
            f"{evidence_coverage:.3f}. "
            f"{corroborated_signal_count} signal(s) have corroborating "
            f"evidence, with {growth_signal_count} growth-oriented and "
            f"{decline_signal_count} decline-oriented signal(s)."
        )

    @staticmethod
    def _empty_result(
        market_id: str,
    ) -> MarketIntelligence:
        return MarketIntelligence(
            market_id=market_id,
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
            explanation=(
                "No market signals were available for aggregation."
            ),
        )


def aggregate_market_intelligence(
    market_id: str,
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> MarketIntelligence:
    """
    Convenience function using the default market aggregator.
    """
    return MarketAggregator().aggregate(
        market_id,
        signals,
        evidence,
    )
