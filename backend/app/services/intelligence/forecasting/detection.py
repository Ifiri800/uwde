from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from backend.app.services.intelligence.domain.signals import SignalType
from backend.app.services.intelligence.market.change import (
    MarketChangeAnalysis,
    MarketChangeDirection,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
)


class ForecastDirection(StrEnum):
    GROWTH = "growth"
    DECLINE = "decline"
    STABLE = "stable"


class ForecastHorizon(StrEnum):
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    LONG_TERM = "long_term"


@dataclass(frozen=True)
class ForecastAnalysis:
    """
    Explainable deterministic forecast derived from historical
    market intelligence.

    This layer estimates the likely future direction of an observed
    market pattern. It does not claim certainty and does not make
    strategic decisions.
    """

    entity_id: str
    signal_type: SignalType
    direction: ForecastDirection
    horizon: ForecastHorizon
    forecast_strength: float
    confidence: float
    observation_count: int
    first_observed_at: object
    latest_observed_at: object
    evidence_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.observation_count < 1:
            raise ValueError("observation_count must be at least 1")

        if not 0.0 <= self.forecast_strength <= 1.0:
            raise ValueError(
                "forecast_strength must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "signal_type": self.signal_type.value,
            "direction": self.direction.value,
            "horizon": self.horizon.value,
            "forecast_strength": self.forecast_strength,
            "confidence": self.confidence,
            "observation_count": self.observation_count,
            "first_observed_at": self.first_observed_at.isoformat(),
            "latest_observed_at": self.latest_observed_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "explanation": self.explanation,
        }


class ForecastingAnalyzer:
    """
    Deterministically forecasts future market direction from temporal
    signal histories and market change analyses.

    The forecast uses:
    - historical recurrence,
    - signal strength,
    - signal confidence,
    - observed change direction,
    - observation count.

    It intentionally avoids opaque predictions.
    """

    def analyze(
        self,
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> ForecastAnalysis:
        if not isinstance(history, TemporalSignalHistory):
            raise TypeError(
                "history must be a TemporalSignalHistory"
            )

        if not isinstance(change, MarketChangeAnalysis):
            raise TypeError(
                "change must be a MarketChangeAnalysis"
            )

        if history.entity_id != change.entity_id:
            raise ValueError(
                "history and change must reference the same entity"
            )

        try:
            signal_type = SignalType(history.signal_type)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "history signal_type must be a valid SignalType"
            ) from exc

        direction = self._forecast_direction(change)

        horizon = self._horizon(history)

        forecast_strength = self._forecast_strength(
            history,
            change,
        )

        confidence = self._confidence(
            history,
            change,
        )

        evidence_ids = self._evidence_ids(
            history,
            change,
        )

        explanation = self._explanation(
            history=history,
            direction=direction,
            horizon=horizon,
            forecast_strength=forecast_strength,
        )

        return ForecastAnalysis(
            entity_id=history.entity_id,
            signal_type=signal_type,
            direction=direction,
            horizon=horizon,
            forecast_strength=forecast_strength,
            confidence=confidence,
            observation_count=history.observation_count,
            first_observed_at=history.first_observed_at,
            latest_observed_at=history.latest_observed_at,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def analyze_many(
        self,
        inputs: list[
            tuple[TemporalSignalHistory, MarketChangeAnalysis]
        ],
    ) -> list[ForecastAnalysis]:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list")

        results = [
            self.analyze(history, change)
            for history, change in inputs
        ]

        return sorted(
            results,
            key=lambda result: (
                result.latest_observed_at,
                result.entity_id,
                result.signal_type.value,
            ),
        )

    @staticmethod
    def _forecast_direction(
        change: MarketChangeAnalysis,
    ) -> ForecastDirection:
        if change.direction == MarketChangeDirection.INCREASE:
            return ForecastDirection.GROWTH

        if change.direction == MarketChangeDirection.DECREASE:
            return ForecastDirection.DECLINE

        return ForecastDirection.STABLE

    @staticmethod
    def _horizon(
        history: TemporalSignalHistory,
    ) -> ForecastHorizon:
        if history.observation_count <= 1:
            return ForecastHorizon.SHORT_TERM

        if history.observation_count <= 4:
            return ForecastHorizon.MEDIUM_TERM

        return ForecastHorizon.LONG_TERM

    @staticmethod
    def _forecast_strength(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> float:
        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        average_strength = (
            sum(history.strength_history)
            / len(history.strength_history)
        )

        strength = (
            change.magnitude * 0.45
            + average_strength * 0.30
            + recurrence * 0.25
        )

        return round(
            min(1.0, max(0.0, strength)),
            6,
        )

    @staticmethod
    def _confidence(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> float:
        average_confidence = (
            sum(history.confidence_history)
            / len(history.confidence_history)
        )

        confidence = (
            average_confidence * 0.60
            + change.confidence * 0.40
        )

        return round(
            min(1.0, max(0.0, confidence)),
            6,
        )

    @staticmethod
    def _evidence_ids(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> tuple[str, ...]:
        evidence_ids: list[str] = []

        for evidence_id in change.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)

        for signal in history.signals:
            for evidence_id in signal.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        return tuple(evidence_ids)

    @staticmethod
    def _explanation(
        *,
        history: TemporalSignalHistory,
        direction: ForecastDirection,
        horizon: ForecastHorizon,
        forecast_strength: float,
    ) -> str:
        return (
            f"Forecast for entity {history.entity_id}: "
            f"future direction is {direction.value}, "
            f"with a {horizon.value.replace('_', '-')} horizon "
            f"and forecast strength of {forecast_strength:.3f}, "
            f"based on {history.observation_count} "
            f"historical signal(s)."
        )


def forecast_market_change(
    history: TemporalSignalHistory,
    change: MarketChangeAnalysis,
) -> ForecastAnalysis:
    """
    Convenience function using the default forecasting analyzer.
    """
    return ForecastingAnalyzer().analyze(
        history,
        change,
    )


def forecast_market_changes(
    inputs: list[
        tuple[TemporalSignalHistory, MarketChangeAnalysis]
    ],
) -> list[ForecastAnalysis]:
    """
    Convenience function for forecasting multiple market changes.
    """
    return ForecastingAnalyzer().analyze_many(inputs)
