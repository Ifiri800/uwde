from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.services.intelligence.market.change import (
    MarketChangeAnalysis,
)
from backend.app.services.intelligence.market.temporal import (
    TemporalSignalHistory,
)


@dataclass(frozen=True)
class ForecastConfidenceAnalysis:
    """
    Explainable confidence assessment for a market forecast.

    Confidence is derived from:
    - signal quality,
    - historical consistency,
    - data coverage,
    - uncertainty.

    This layer measures confidence in the forecast inputs. It does
    not alter the forecast direction or make strategic decisions.
    """

    entity_id: str
    confidence_score: float
    signal_quality: float
    historical_consistency: float
    data_coverage: float
    uncertainty: float
    evidence_ids: tuple[str, ...]
    explanation: str
    observation_count: int = 1

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.observation_count < 1:
            raise ValueError(
                "observation_count must be at least 1"
            )

        for name, value in (
            ("confidence_score", self.confidence_score),
            ("signal_quality", self.signal_quality),
            ("historical_consistency", self.historical_consistency),
            ("data_coverage", self.data_coverage),
            ("uncertainty", self.uncertainty),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0.0 and 1.0"
                )

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "confidence_score": self.confidence_score,
            "signal_quality": self.signal_quality,
            "historical_consistency": self.historical_consistency,
            "data_coverage": self.data_coverage,
            "uncertainty": self.uncertainty,
            "observation_count": self.observation_count,
            "evidence_ids": list(self.evidence_ids),
            "explanation": self.explanation,
        }


class ForecastConfidenceAnalyzer:
    """
    Deterministically evaluates confidence in a forecast.

    The calculation is deliberately transparent:

        confidence =
            signal_quality * 0.35
            + historical_consistency * 0.30
            + data_coverage * 0.20
            + (1 - uncertainty) * 0.15

    The result is bounded to [0, 1].
    """

    def analyze(
        self,
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> ForecastConfidenceAnalysis:
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

        signal_quality = self._signal_quality(history)

        historical_consistency = (
            self._historical_consistency(history)
        )

        data_coverage = self._data_coverage(
            history,
            change,
        )

        uncertainty = self._uncertainty(
            history,
            change,
        )

        confidence_score = (
            signal_quality * 0.35
            + historical_consistency * 0.30
            + data_coverage * 0.20
            + (1.0 - uncertainty) * 0.15
        )

        confidence_score = round(
            min(1.0, max(0.0, confidence_score)),
            6,
        )

        evidence_ids = self._evidence_ids(
            history,
            change,
        )

        explanation = (
            f"Forecast confidence for entity "
            f"{history.entity_id}: "
            f"confidence score is {confidence_score:.3f}, "
            f"based on signal quality "
            f"{signal_quality:.3f}, historical consistency "
            f"{historical_consistency:.3f}, data coverage "
            f"{data_coverage:.3f}, and uncertainty "
            f"{uncertainty:.3f}."
        )

        return ForecastConfidenceAnalysis(
            entity_id=history.entity_id,
            confidence_score=confidence_score,
            signal_quality=round(signal_quality, 6),
            historical_consistency=round(
                historical_consistency,
                6,
            ),
            data_coverage=round(data_coverage, 6),
            uncertainty=round(uncertainty, 6),
            observation_count=history.observation_count,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def analyze_many(
        self,
        inputs: list[
            tuple[
                TemporalSignalHistory,
                MarketChangeAnalysis,
            ]
        ],
    ) -> list[ForecastConfidenceAnalysis]:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list")

        results = [
            self.analyze(history, change)
            for history, change in inputs
        ]

        return sorted(
            results,
            key=lambda result: (
                result.entity_id,
                result.observation_count,
            ),
        )

    @staticmethod
    def _signal_quality(
        history: TemporalSignalHistory,
    ) -> float:
        if not history.confidence_history:
            return 0.0

        average_confidence = (
            sum(history.confidence_history)
            / len(history.confidence_history)
        )

        if not history.strength_history:
            average_strength = 0.0
        else:
            average_strength = (
                sum(history.strength_history)
                / len(history.strength_history)
            )

        quality = (
            average_confidence * 0.60
            + average_strength * 0.40
        )

        return min(1.0, max(0.0, quality))

    @staticmethod
    def _historical_consistency(
        history: TemporalSignalHistory,
    ) -> float:
        if history.observation_count <= 1:
            return 0.50

        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        if history.confidence_history:
            confidence_values = history.confidence_history
            average_confidence = (
                sum(confidence_values)
                / len(confidence_values)
            )

            deviation = (
                sum(
                    abs(
                        value
                        - average_confidence
                    )
                    for value in confidence_values
                )
                / len(confidence_values)
            )
        else:
            deviation = 1.0

        consistency = (
            recurrence * 0.60
            + (1.0 - min(1.0, deviation)) * 0.40
        )

        return min(1.0, max(0.0, consistency))

    @staticmethod
    def _data_coverage(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> float:
        evidence_count = len(
            set(
                evidence_id
                for signal in history.signals
                for evidence_id in signal.evidence_ids
            )
        )

        change_evidence_count = len(
            set(change.evidence_ids)
        )

        total_evidence = max(
            evidence_count,
            change_evidence_count,
        )

        evidence_score = min(
            1.0,
            total_evidence / 3.0,
        )

        observation_score = min(
            1.0,
            history.observation_count / 3.0,
        )

        coverage = (
            evidence_score * 0.60
            + observation_score * 0.40
        )

        return min(1.0, max(0.0, coverage))

    @staticmethod
    def _uncertainty(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
    ) -> float:
        signal_quality = (
            ForecastConfidenceAnalyzer._signal_quality(
                history
            )
        )

        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        magnitude_support = min(
            1.0,
            max(0.0, change.magnitude),
        )

        uncertainty = (
            (1.0 - signal_quality) * 0.40
            + (1.0 - recurrence) * 0.35
            + (1.0 - magnitude_support) * 0.25
        )

        return min(1.0, max(0.0, uncertainty))

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


def calculate_forecast_confidence(
    history: TemporalSignalHistory,
    change: MarketChangeAnalysis,
) -> ForecastConfidenceAnalysis:
    """
    Convenience function using the default confidence analyzer.
    """
    return ForecastConfidenceAnalyzer().analyze(
        history,
        change,
    )


def calculate_forecast_confidences(
    inputs: list[
        tuple[
            TemporalSignalHistory,
            MarketChangeAnalysis,
        ]
    ],
) -> list[ForecastConfidenceAnalysis]:
    """
    Convenience function for multiple confidence assessments.
    """
    return ForecastConfidenceAnalyzer().analyze_many(inputs)
