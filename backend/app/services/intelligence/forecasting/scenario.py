from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from backend.app.services.intelligence.forecasting.model import (
    ForecastModelResult,
)
from backend.app.services.intelligence.forecasting.confidence import (
    ForecastConfidenceAnalysis,
)


class ForecastScenario(StrEnum):
    BASELINE = "baseline"
    OPTIMISTIC = "optimistic"
    CONSERVATIVE = "conservative"


@dataclass(frozen=True)
class ScenarioForecast:
    """
    Explainable scenario projection derived from a forecasting model
    and its confidence assessment.
    """

    entity_id: str
    scenario: ForecastScenario
    projected_value: float
    projection_change: float
    confidence: float
    forecast_strength: float
    explanation: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if not 0.0 <= self.projected_value <= 1.0:
            raise ValueError(
                "projected_value must be between 0.0 and 1.0"
            )

        if not -1.0 <= self.projection_change <= 1.0:
            raise ValueError(
                "projection_change must be between -1.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.forecast_strength <= 1.0:
            raise ValueError(
                "forecast_strength must be between 0.0 and 1.0"
            )

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "scenario": self.scenario.value,
            "projected_value": self.projected_value,
            "projection_change": self.projection_change,
            "confidence": self.confidence,
            "forecast_strength": self.forecast_strength,
            "explanation": self.explanation,
        }


class ScenarioForecastingAnalyzer:
    """
    Deterministically generates three market scenarios:

    - baseline: the model's direct projection,
    - optimistic: stronger positive movement,
    - conservative: weaker positive movement or stronger decline.

    Scenario adjustments are bounded to the model's [0, 1] domain.
    """

    SCENARIO_FACTORS = {
        ForecastScenario.BASELINE: 1.00,
        ForecastScenario.OPTIMISTIC: 1.20,
        ForecastScenario.CONSERVATIVE: 0.80,
    }

    def analyze(
        self,
        model: ForecastModelResult,
        confidence: ForecastConfidenceAnalysis,
    ) -> list[ScenarioForecast]:
        if not isinstance(model, ForecastModelResult):
            raise TypeError(
                "model must be a ForecastModelResult"
            )

        if not isinstance(
            confidence,
            ForecastConfidenceAnalysis,
        ):
            raise TypeError(
                "confidence must be a ForecastConfidenceAnalysis"
            )

        if model.entity_id != confidence.entity_id:
            raise ValueError(
                "model and confidence must reference the same entity"
            )

        results = [
            self._build_scenario(
                model,
                confidence,
                scenario,
            )
            for scenario in ForecastScenario
        ]

        return results

    def analyze_many(
        self,
        inputs: list[
            tuple[
                ForecastModelResult,
                ForecastConfidenceAnalysis,
            ]
        ],
    ) -> list[ScenarioForecast]:
        if not isinstance(inputs, list):
            raise TypeError("inputs must be a list")

        results: list[ScenarioForecast] = []

        for model, confidence in inputs:
            results.extend(
                self.analyze(
                    model,
                    confidence,
                )
            )

        return sorted(
            results,
            key=lambda result: (
                result.entity_id,
                result.scenario.value,
            ),
        )

    @classmethod
    def _build_scenario(
        cls,
        model: ForecastModelResult,
        confidence: ForecastConfidenceAnalysis,
        scenario: ForecastScenario,
    ) -> ScenarioForecast:
        factor = cls.SCENARIO_FACTORS[scenario]

        baseline = model.projected_value
        baseline_change = model.projection_change

        # Scale the model's relative projection change according
        # to the selected scenario.
        adjusted_change = baseline_change * factor

        # The model baseline determines the magnitude of the
        # scenario adjustment, while projected_value remains
        # the starting forecast projection.
        projected_value = baseline + (
            model.baseline * adjusted_change
        )

        projected_value = min(
            1.0,
            max(
                0.0,
                projected_value,
            ),
        )

        explanation = (
            f"{scenario.value} scenario for "
            f"entity {model.entity_id}: projected value is "
            f"{projected_value:.3f}, representing a change of "
            f"{adjusted_change:+.3f} from the model baseline."
        )

        scenario_confidence = cls._scenario_confidence(
            confidence.confidence_score,
            scenario,
        )

        return ScenarioForecast(
            entity_id=model.entity_id,
            scenario=scenario,
            projected_value=round(
                projected_value,
                6,
            ),
            projection_change=round(
                adjusted_change,
                6,
            ),
            confidence=round(
                scenario_confidence,
                6,
            ),
            forecast_strength=0.0,
            explanation=explanation,
        )
    @staticmethod
    def _scenario_confidence(
        base_confidence: float,
        scenario: ForecastScenario,
    ) -> float:
        if scenario == ForecastScenario.BASELINE:
            adjustment = 1.00
        elif scenario == ForecastScenario.OPTIMISTIC:
            adjustment = 0.90
        else:
            adjustment = 0.90

        return min(
            1.0,
            max(
                0.0,
                base_confidence * adjustment,
            ),
        )


def forecast_scenarios(
    model: ForecastModelResult,
    confidence: ForecastConfidenceAnalysis,
) -> list[ScenarioForecast]:
    """
    Convenience function for generating baseline, optimistic,
    and conservative scenarios.
    """
    return ScenarioForecastingAnalyzer().analyze(
        model,
        confidence,
    )


def forecast_scenarios_many(
    inputs: list[
        tuple[
            ForecastModelResult,
            ForecastConfidenceAnalysis,
        ]
    ],
) -> list[ScenarioForecast]:
    """
    Convenience function for generating scenarios for many forecasts.
    """
    return ScenarioForecastingAnalyzer().analyze_many(inputs)


