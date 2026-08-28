from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from backend.app.services.intelligence.domain.signals import SignalType
from .temporal import TemporalSignalHistory


class MarketChangeType(StrEnum):
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    PRICE_INCREASE = "price_increase"
    PRICE_DECREASE = "price_decrease"
    PRODUCT_LAUNCH = "product_launch"
    PRODUCT_DISCONTINUATION = "product_discontinuation"
    HIRING_GROWTH = "hiring_growth"
    FUNDING_GROWTH = "funding_growth"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    DEMAND_GROWTH = "demand_growth"
    DEMAND_DECLINE = "demand_decline"
    COMPETITIVE_CHANGE = "competitive_change"


class MarketChangeDirection(StrEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


@dataclass(frozen=True)
class MarketChangeAnalysis:
    """
    Explainable analysis of a market change derived from temporal
    intelligence signal history.

    This layer identifies and measures change. It does not determine
    whether the change represents a threat, opportunity, or risk.
    """

    entity_id: str
    change_type: MarketChangeType
    direction: MarketChangeDirection
    signal_type: SignalType
    observation_count: int
    magnitude: float
    confidence: float
    first_observed_at: object
    latest_observed_at: object
    evidence_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.observation_count < 1:
            raise ValueError("observation_count must be at least 1")

        if not 0.0 <= self.magnitude <= 1.0:
            raise ValueError("magnitude must be between 0.0 and 1.0")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "change_type": self.change_type.value,
            "direction": self.direction.value,
            "signal_type": self.signal_type.value,
            "observation_count": self.observation_count,
            "magnitude": self.magnitude,
            "confidence": self.confidence,
            "first_observed_at": self.first_observed_at.isoformat(),
            "latest_observed_at": self.latest_observed_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "explanation": self.explanation,
        }


class MarketChangeAnalyzer:
    """
    Deterministically analyzes market change from temporal signal
    histories.

    The analyzer:
    - classifies the type of change,
    - determines direction,
    - estimates magnitude,
    - calculates confidence,
    - preserves evidence,
    - produces an explainable result.

    It does not infer competitive threat, opportunity, or risk.
    """

    CHANGE_MAP: dict[SignalType, MarketChangeType] = {
        SignalType.NEW_COMPANY: MarketChangeType.EXPANSION,
        SignalType.NEW_PRODUCT: MarketChangeType.PRODUCT_LAUNCH,
        SignalType.PRODUCT_LAUNCH: MarketChangeType.PRODUCT_LAUNCH,
        SignalType.PRICE_CHANGE: MarketChangeType.PRICE_INCREASE,
        SignalType.COMPANY_EXPANSION: MarketChangeType.EXPANSION,
        SignalType.HIRING_SIGNAL: MarketChangeType.HIRING_GROWTH,
        SignalType.PROCUREMENT_SIGNAL: MarketChangeType.EXPANSION,
        SignalType.FUNDING_SIGNAL: MarketChangeType.FUNDING_GROWTH,
        SignalType.MARKET_GROWTH: MarketChangeType.EXPANSION,
        SignalType.COMPETITOR_CHANGE: MarketChangeType.COMPETITIVE_CHANGE,
        SignalType.TECHNOLOGY_ADOPTION: MarketChangeType.TECHNOLOGY_ADOPTION,
        SignalType.TENDER_OPPORTUNITY: MarketChangeType.DEMAND_GROWTH,
        SignalType.BUYER_INTENT: MarketChangeType.DEMAND_GROWTH,
    }

    def analyze(
        self,
        history: TemporalSignalHistory,
    ) -> MarketChangeAnalysis:
        if not isinstance(history, TemporalSignalHistory):
            raise TypeError(
                "history must be a TemporalSignalHistory"
            )

        try:
            signal_type = SignalType(history.signal_type)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "history signal_type must be a valid SignalType"
            ) from exc

        try:
            change_type = self.CHANGE_MAP[signal_type]
        except KeyError as exc:
            raise ValueError(
                f"No market change mapping defined for "
                f"{signal_type.value}"
            ) from exc

        direction = self._direction(
            signal_type,
            change_type,
            history,
        )

        if signal_type == SignalType.PRICE_CHANGE:
            if direction == MarketChangeDirection.INCREASE:
                change_type = MarketChangeType.PRICE_INCREASE
            elif direction == MarketChangeDirection.DECREASE:
                change_type = MarketChangeType.PRICE_DECREASE

        magnitude = self._magnitude(history)

        confidence = self._confidence(history)

        evidence_ids = self._evidence_ids(history)

        explanation = self._explanation(
            history=history,
            change_type=change_type,
            direction=direction,
            magnitude=magnitude,
        )

        return MarketChangeAnalysis(
            entity_id=history.entity_id,
            change_type=change_type,
            direction=direction,
            signal_type=signal_type,
            observation_count=history.observation_count,
            magnitude=magnitude,
            confidence=confidence,
            first_observed_at=history.first_observed_at,
            latest_observed_at=history.latest_observed_at,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def analyze_many(
        self,
        histories: list[TemporalSignalHistory],
    ) -> list[MarketChangeAnalysis]:
        if not isinstance(histories, list):
            raise TypeError("histories must be a list")

        results = [
            self.analyze(history)
            for history in histories
        ]

        return sorted(
            results,
            key=lambda result: (
                result.latest_observed_at,
                result.entity_id,
                result.change_type.value,
            ),
        )

    @classmethod
    def _direction(
        cls,
        signal_type: SignalType,
        change_type: MarketChangeType,
        history: TemporalSignalHistory,
    ) -> MarketChangeDirection:
        if signal_type == SignalType.PRICE_CHANGE:
            return cls._value_direction(history)

        if change_type == MarketChangeType.COMPETITIVE_CHANGE:
            return MarketChangeDirection.INCREASE

        if change_type in {
            MarketChangeType.DEMAND_GROWTH,
            MarketChangeType.EXPANSION,
            MarketChangeType.PRODUCT_LAUNCH,
            MarketChangeType.HIRING_GROWTH,
            MarketChangeType.FUNDING_GROWTH,
            MarketChangeType.TECHNOLOGY_ADOPTION,
        }:
            return MarketChangeDirection.INCREASE

        if change_type == MarketChangeType.PRODUCT_DISCONTINUATION:
            return MarketChangeDirection.DECREASE

        return MarketChangeDirection.STABLE

    @staticmethod
    def _value_direction(
        history: TemporalSignalHistory,
    ) -> MarketChangeDirection:
        if len(history.signals) < 1:
            return MarketChangeDirection.STABLE

        latest = history.signals[-1]

        previous = latest.previous_value
        current = latest.current_value

        if isinstance(previous, (int, float)) and isinstance(
            current,
            (int, float),
        ):
            if current > previous:
                return MarketChangeDirection.INCREASE

            if current < previous:
                return MarketChangeDirection.DECREASE

        if len(history.signals) >= 2:
            previous_signal = history.signals[-2]

            previous = previous_signal.current_value
            current = latest.current_value

            if isinstance(previous, (int, float)) and isinstance(
                current,
                (int, float),
            ):
                if current > previous:
                    return MarketChangeDirection.INCREASE

                if current < previous:
                    return MarketChangeDirection.DECREASE

        return MarketChangeDirection.STABLE

    @staticmethod
    def _magnitude(
        history: TemporalSignalHistory,
    ) -> float:
        average_strength = (
            sum(history.strength_history)
            / len(history.strength_history)
        )

        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        magnitude = (
            average_strength * 0.70
            + recurrence * 0.30
        )

        latest_signal = history.latest_signal

        if (
            isinstance(latest_signal.previous_value, (int, float))
            and isinstance(latest_signal.current_value, (int, float))
            and latest_signal.previous_value != 0
        ):
            relative_change = abs(
                latest_signal.current_value
                - latest_signal.previous_value
            ) / abs(latest_signal.previous_value)

            magnitude = (
                magnitude * 0.60
                + min(1.0, relative_change) * 0.40
            )

        return round(
            min(1.0, max(0.0, magnitude)),
            6,
        )

    @staticmethod
    def _confidence(
        history: TemporalSignalHistory,
    ) -> float:
        if not history.confidence_history:
            return 0.0

        return round(
            min(
                1.0,
                max(
                    0.0,
                    sum(history.confidence_history)
                    / len(history.confidence_history),
                ),
            ),
            6,
        )

    @staticmethod
    def _evidence_ids(
        history: TemporalSignalHistory,
    ) -> tuple[str, ...]:
        evidence_ids: list[str] = []

        for signal in history.signals:
            for evidence_id in signal.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        return tuple(evidence_ids)

    @staticmethod
    def _explanation(
        *,
        history: TemporalSignalHistory,
        change_type: MarketChangeType,
        direction: MarketChangeDirection,
        magnitude: float,
    ) -> str:
        recurrence = (
            "recurring"
            if history.is_recurring
            else "single-observation"
        )

        return (
            f"Market change detected for entity "
            f"{history.entity_id}: "
            f"{change_type.value.replace('_', ' ')} "
            f"with {history.observation_count} "
            f"{recurrence} signal(s), "
            f"direction is {direction.value}, "
            f"and change magnitude is {magnitude:.3f}."
        )


def analyze_market_change(
    history: TemporalSignalHistory,
) -> MarketChangeAnalysis:
    """
    Convenience function using the default market change analyzer.
    """
    return MarketChangeAnalyzer().analyze(history)


def analyze_market_changes(
    histories: list[TemporalSignalHistory],
) -> list[MarketChangeAnalysis]:
    """
    Convenience function using the default market change analyzer.
    """
    return MarketChangeAnalyzer().analyze_many(histories)

