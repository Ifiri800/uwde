from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import sqrt

from .models import DriftAssessment, ModelMetric


@dataclass(frozen=True)
class PredictionMonitoring:
    """Monitoring summary for a batch of model predictions."""

    prediction_count: int
    mean_prediction: float
    mean_confidence: float
    minimum_confidence: float
    maximum_confidence: float

    def __post_init__(self) -> None:
        if self.prediction_count < 0:
            raise ValueError("prediction_count cannot be negative")

        for name, value in {
            "mean_prediction": self.mean_prediction,
            "mean_confidence": self.mean_confidence,
            "minimum_confidence": self.minimum_confidence,
            "maximum_confidence": self.maximum_confidence,
        }.items():
            if not float("-inf") < value < float("inf"):
                raise ValueError(f"{name} must be finite")

        for name, value in {
            "mean_confidence": self.mean_confidence,
            "minimum_confidence": self.minimum_confidence,
            "maximum_confidence": self.maximum_confidence,
        }.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1"
                )


@dataclass(frozen=True)
class PerformanceAssessment:
    """Assessment of model performance against a baseline."""

    metric_name: str
    current_value: float
    baseline_value: float
    degradation: float
    threshold: float
    degraded: bool

    def __post_init__(self) -> None:
        if not self.metric_name.strip():
            raise ValueError("metric_name is required")

        for name, value in {
            "current_value": self.current_value,
            "baseline_value": self.baseline_value,
            "degradation": self.degradation,
            "threshold": self.threshold,
        }.items():
            if not float("-inf") < value < float("inf"):
                raise ValueError(f"{name} must be finite")

        if self.threshold < 0.0:
            raise ValueError("threshold cannot be negative")


class MLMonitoringEngine:
    """
    Deterministic monitoring engine for production ML systems.

    Provides prediction health, feature drift, and performance
    degradation assessments without coupling monitoring to a
    particular ML framework.
    """

    def monitor_predictions(
        self,
        predictions: Sequence[float],
        confidences: Sequence[float],
    ) -> PredictionMonitoring:

        if len(predictions) != len(confidences):
            raise ValueError(
                "predictions and confidences must have equal length"
            )

        if not predictions:
            return PredictionMonitoring(
                prediction_count=0,
                mean_prediction=0.0,
                mean_confidence=0.0,
                minimum_confidence=0.0,
                maximum_confidence=0.0,
            )

        values = tuple(float(value) for value in predictions)
        confidence_values = tuple(
            float(value)
            for value in confidences
        )

        if any(
            not float("-inf") < value < float("inf")
            for value in values
        ):
            raise ValueError(
                "predictions must be finite"
            )

        if any(
            not 0.0 <= value <= 1.0
            for value in confidence_values
        ):
            raise ValueError(
                "confidences must be between 0 and 1"
            )

        return PredictionMonitoring(
            prediction_count=len(values),
            mean_prediction=sum(values) / len(values),
            mean_confidence=(
                sum(confidence_values)
                / len(confidence_values)
            ),
            minimum_confidence=min(confidence_values),
            maximum_confidence=max(confidence_values),
        )

    def assess_feature_drift(
        self,
        feature_name: str,
        reference: Sequence[float],
        current: Sequence[float],
        *,
        threshold: float = 0.1,
        reference_version: str | None = None,
        current_version: str | None = None,
        assessment_id: str = "drift-assessment",
    ) -> DriftAssessment:

        if not feature_name.strip():
            raise ValueError("feature_name is required")

        if threshold < 0.0:
            raise ValueError(
                "threshold cannot be negative"
            )

        if not reference:
            raise ValueError(
                "reference distribution is required"
            )

        if not current:
            raise ValueError(
                "current distribution is required"
            )

        reference_values = tuple(float(v) for v in reference)
        current_values = tuple(float(v) for v in current)

        if any(
            not float("-inf") < value < float("inf")
            for value in reference_values + current_values
        ):
            raise ValueError(
                "drift values must be finite"
            )

        reference_mean = (
            sum(reference_values)
            / len(reference_values)
        )

        current_mean = (
            sum(current_values)
            / len(current_values)
        )

        reference_std = self._std(reference_values)
        current_std = self._std(current_values)

        score = abs(
            current_mean - reference_mean
        ) / max(
            reference_std,
            1e-12,
        )

        score += abs(
            current_std - reference_std
        ) / max(
            reference_std,
            1e-12,
        )

        return DriftAssessment(
            assessment_id=assessment_id,
            drift_type="feature_distribution",
            score=score,
            threshold=threshold,
            detected=score >= threshold,
            feature_name=feature_name,
            reference_version=reference_version,
            current_version=current_version,
            metadata={
                "reference_count": len(reference_values),
                "current_count": len(current_values),
                "reference_mean": reference_mean,
                "current_mean": current_mean,
                "reference_std": reference_std,
                "current_std": current_std,
            },
        )

    def assess_performance(
        self,
        metric: ModelMetric,
        baseline_value: float,
        *,
        threshold: float = 0.1,
    ) -> PerformanceAssessment:

        if baseline_value < 0.0:
            raise ValueError(
                "baseline_value cannot be negative"
            )

        if threshold < 0.0:
            raise ValueError(
                "threshold cannot be negative"
            )

        if baseline_value == 0.0:
            degradation = (
                0.0
                if metric.value == 0.0
                else float("inf")
            )
        else:
            degradation = (
                metric.value - baseline_value
            ) / baseline_value

        return PerformanceAssessment(
            metric_name=metric.name,
            current_value=metric.value,
            baseline_value=baseline_value,
            degradation=degradation,
            threshold=threshold,
            degraded=degradation >= threshold,
        )

    @staticmethod
    def _std(values: Sequence[float]) -> float:
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / len(values)

        return sqrt(variance)


__all__ = [
    "MLMonitoringEngine",
    "PerformanceAssessment",
    "PredictionMonitoring",
]
