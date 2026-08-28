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
from backend.app.services.intelligence.forecasting.detection import (
    ForecastDirection,
    ForecastHorizon,
)


class TrendDirection(StrEnum):
    UPWARD = "upward"
    DOWNWARD = "downward"
    FLAT = "flat"


@dataclass(frozen=True)
class ForecastModelResult:
    """
    Deterministic time-based projection derived from historical
    market intelligence.

    This layer projects the observed baseline and trend across
    defined forecast horizons. It does not calculate uncertainty
    or generate strategic recommendations.
    """

    entity_id: str
    signal_type: SignalType
    trend_direction: TrendDirection
    forecast_direction: ForecastDirection
    horizon: ForecastHorizon
    baseline: float
    growth_rate: float
    projected_value: float
    projection_change: float
    observation_count: int
    first_observed_at: object
    latest_observed_at: object
    evidence_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.observation_count < 1:
            raise ValueError(
                "observation_count must be at least 1"
            )

        if not 0.0 <= self.baseline <= 1.0:
            raise ValueError(
                "baseline must be between 0.0 and 1.0"
            )

        if not -1.0 <= self.growth_rate <= 1.0:
            raise ValueError(
                "growth_rate must be between -1.0 and 1.0"
            )

        if self.projected_value < 0.0:
            raise ValueError(
                "projected_value must be non-negative"
            )

        if not -1.0 <= self.projection_change <= 1.0:
            raise ValueError(
                "projection_change must be between -1.0 and 1.0"
            )

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "signal_type": self.signal_type.value,
            "trend_direction": self.trend_direction.value,
            "forecast_direction": self.forecast_direction.value,
            "horizon": self.horizon.value,
            "baseline": self.baseline,
            "growth_rate": self.growth_rate,
            "projected_value": self.projected_value,
            "projection_change": self.projection_change,
            "observation_count": self.observation_count,
            "first_observed_at": self.first_observed_at.isoformat(),
            "latest_observed_at": self.latest_observed_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "explanation": self.explanation,
        }


class ForecastingModel:
    """
    Deterministic forecasting model.

    The model combines:
    - historical signal strength,
    - latest observed strength,
    - observed change direction,
    - recurrence,
    - time horizon.

    The model intentionally remains transparent and bounded.
    """

    HORIZON_MULTIPLIERS: dict[ForecastHorizon, float] = {
        ForecastHorizon.SHORT_TERM: 1.0,
        ForecastHorizon.MEDIUM_TERM: 2.0,
        ForecastHorizon.LONG_TERM: 3.0,
    }

    def project(
        self,
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
        forecast_direction: ForecastDirection,
        horizon: ForecastHorizon,
    ) -> ForecastModelResult:
        if not isinstance(history, TemporalSignalHistory):
            raise TypeError(
                "history must be a TemporalSignalHistory"
            )

        if not isinstance(change, MarketChangeAnalysis):
            raise TypeError(
                "change must be a MarketChangeAnalysis"
            )

        if not isinstance(forecast_direction, ForecastDirection):
            raise TypeError(
                "forecast_direction must be a ForecastDirection"
            )

        if not isinstance(horizon, ForecastHorizon):
            raise TypeError(
                "horizon must be a ForecastHorizon"
            )

        if history.entity_id != change.entity_id:
            raise ValueError(
                "history and change must reference the same entity"
            )

        signal_type = SignalType(history.signal_type)

        baseline = self._baseline(history)
        trend_direction = self._trend_direction(
            change.direction
        )
        growth_rate = self._growth_rate(
            history,
            change,
            baseline,
        )

        projected_value = self._project_value(
            baseline,
            growth_rate,
            horizon,
        )

        projection_change = self._projection_change(
            baseline,
            projected_value,
        )

        evidence_ids = self._evidence_ids(
            history,
            change,
        )

        explanation = self._explanation(
            entity_id=history.entity_id,
            trend_direction=trend_direction,
            horizon=horizon,
            baseline=baseline,
            growth_rate=growth_rate,
            projected_value=projected_value,
        )

        return ForecastModelResult(
            entity_id=history.entity_id,
            signal_type=signal_type,
            trend_direction=trend_direction,
            forecast_direction=forecast_direction,
            horizon=horizon,
            baseline=baseline,
            growth_rate=growth_rate,
            projected_value=projected_value,
            projection_change=projection_change,
            observation_count=history.observation_count,
            first_observed_at=history.first_observed_at,
            latest_observed_at=history.latest_observed_at,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def project_from_detection(
        self,
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
        detection: Any,
    ) -> ForecastModelResult:
        """
        Project directly from ForecastAnalysis produced by
        forecasting detection.
        """
        if not hasattr(detection, "direction"):
            raise TypeError(
                "detection must contain a forecast direction"
            )

        if not hasattr(detection, "horizon"):
            raise TypeError(
                "detection must contain a forecast horizon"
            )

        return self.project(
            history=history,
            change=change,
            forecast_direction=detection.direction,
            horizon=detection.horizon,
        )

    def project_many(
        self,
        inputs: list[
            tuple[
                TemporalSignalHistory,
                MarketChangeAnalysis,
                ForecastDirection,
                ForecastHorizon,
            ]
        ],
    ) -> list[ForecastModelResult]:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list")

        results = [
            self.project(
                history,
                change,
                direction,
                horizon,
            )
            for history, change, direction, horizon in inputs
        ]

        return sorted(
            results,
            key=lambda result: (
                result.latest_observed_at,
                result.entity_id,
                result.signal_type.value,
                result.horizon.value,
            ),
        )

    @staticmethod
    def _baseline(
        history: TemporalSignalHistory,
    ) -> float:
        if not history.strength_history:
            return 0.0

        return round(
            min(
                1.0,
                max(
                    0.0,
                    sum(history.strength_history)
                    / len(history.strength_history),
                ),
            ),
            6,
        )

    @staticmethod
    def _trend_direction(
        direction: MarketChangeDirection,
    ) -> TrendDirection:
        if direction == MarketChangeDirection.INCREASE:
            return TrendDirection.UPWARD

        if direction == MarketChangeDirection.DECREASE:
            return TrendDirection.DOWNWARD

        return TrendDirection.FLAT

    @staticmethod
    def _growth_rate(
        history: TemporalSignalHistory,
        change: MarketChangeAnalysis,
        baseline: float,
    ) -> float:
        if baseline <= 0.0:
            return 0.0

        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        directional_sign = 0.0

        if change.direction == MarketChangeDirection.INCREASE:
            directional_sign = 1.0
        elif change.direction == MarketChangeDirection.DECREASE:
            directional_sign = -1.0

        rate = (
            change.magnitude * 0.50
            + recurrence * 0.20
            + baseline * 0.30
        )

        return round(
            max(
                -1.0,
                min(
                    1.0,
                    rate * directional_sign,
                ),
            ),
            6,
        )

    @classmethod
    def _project_value(
        cls,
        baseline: float,
        growth_rate: float,
        horizon: ForecastHorizon,
    ) -> float:
        multiplier = cls.HORIZON_MULTIPLIERS[horizon]

        projected = baseline * (
            1.0 + growth_rate * multiplier
        )

        return round(
            max(0.0, min(1.0, projected)),
            6,
        )

    @staticmethod
    def _projection_change(
        baseline: float,
        projected_value: float,
    ) -> float:
        if baseline <= 0.0:
            return 0.0

        return round(
            max(
                -1.0,
                min(
                    1.0,
                    (projected_value - baseline)
                    / baseline,
                ),
            ),
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
        entity_id: str,
        trend_direction: TrendDirection,
        horizon: ForecastHorizon,
        baseline: float,
        growth_rate: float,
        projected_value: float,
    ) -> str:
        return (
            f"Forecast model for entity {entity_id}: "
            f"trend is {trend_direction.value}, "
            f"baseline is {baseline:.3f}, "
            f"estimated growth rate is {growth_rate:.3f}, "
            f"and projected {horizon.value.replace('_', '-')} "
            f"value is {projected_value:.3f}."
        )


def project_forecast(
    history: TemporalSignalHistory,
    change: MarketChangeAnalysis,
    forecast_direction: ForecastDirection,
    horizon: ForecastHorizon,
) -> ForecastModelResult:
    """
    Convenience function using the default forecasting model.
    """
    return ForecastingModel().project(
        history,
        change,
        forecast_direction,
        horizon,
    )


def project_forecast_many(
    inputs: list[
        tuple[
            TemporalSignalHistory,
            MarketChangeAnalysis,
            ForecastDirection,
            ForecastHorizon,
        ]
    ],
) -> list[ForecastModelResult]:
    """
    Convenience function for multiple forecast projections.
    """
    return ForecastingModel().project_many(inputs)
