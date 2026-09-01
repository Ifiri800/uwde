from __future__ import annotations

from collections.abc import Iterable

from .features import normalize_features
from .models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligencePrediction,
    IntelligenceResult,
    IntelligenceType,
)


class LeakProbabilityEngine:
    """
    Deterministic methane leak-probability engine.

    Feature values are interpreted as normalized leak indicators
    in the range 0.0 to 1.0. Feature confidence is used as the
    weighting factor.

    This is a transparent baseline for Layer 10. A statistical or
    machine-learning classifier can later replace this implementation
    without changing the public intelligence result contract.
    """

    LOW_THRESHOLD = 0.33
    HIGH_THRESHOLD = 0.66

    def predict(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "leak-probability",
        model_id: str | None = "deterministic-leak-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        self._validate_values(normalized)

        probability = self._probability(normalized)
        confidence = self._confidence(normalized)
        classification = self._classification(probability)

        explanation = (
            "Leak probability derived from "
            f"{len(normalized)} normalized leak-indicator features "
            "using a confidence-weighted deterministic baseline."
        )

        prediction = IntelligencePrediction(
            prediction_id=prediction_id,
            entity_id=entity_id,
            intelligence_type=IntelligenceType.LEAK_PROBABILITY,
            method=IntelligenceMethod.DETERMINISTIC,
            value=probability,
            confidence=confidence,
            feature_names=tuple(
                feature.name
                for feature in normalized
            ),
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id=model_id,
            explanation=explanation,
            metadata={
                "classification": classification,
                "low_threshold": self.LOW_THRESHOLD,
                "high_threshold": self.HIGH_THRESHOLD,
            },
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.LEAK_PROBABILITY,
            predictions=(prediction,),
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                f"Leak probability classified as {classification}.",
            ),
            metadata={
                "probability": probability,
                "classification": classification,
            },
        )

    @staticmethod
    def _validate_values(
        features: tuple[IntelligenceFeature, ...],
    ) -> None:

        for feature in features:
            if not 0.0 <= feature.value <= 1.0:
                raise ValueError(
                    "leak probability features must be between 0 and 1"
                )

    @staticmethod
    def _probability(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:

        total_weight = sum(
            feature.confidence
            for feature in features
        )

        if total_weight <= 0.0:
            return 0.0

        probability = sum(
            feature.value * feature.confidence
            for feature in features
        ) / total_weight

        return min(1.0, max(0.0, probability))

    @staticmethod
    def _confidence(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:

        if not features:
            return 0.0

        return min(
            1.0,
            max(
                0.0,
                sum(
                    feature.confidence
                    for feature in features
                ) / len(features),
            ),
        )

    @classmethod
    def _classification(
        cls,
        probability: float,
    ) -> str:

        if probability < cls.LOW_THRESHOLD:
            return "low"

        if probability < cls.HIGH_THRESHOLD:
            return "medium"

        return "high"


def predict_leak_probability(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "leak-probability",
    model_id: str | None = "deterministic-leak-baseline",
) -> IntelligenceResult:

    return LeakProbabilityEngine().predict(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
