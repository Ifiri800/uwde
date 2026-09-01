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


class PatternRecognitionEngine:
    """
    Deterministic baseline for methane emission pattern recognition.

    The engine identifies recurring directional patterns from an
    ordered sequence of normalized intelligence features.

    A positive trend indicates increasing values, a negative trend
    indicates decreasing values, and a stable pattern indicates
    negligible change.
    """

    DEFAULT_TOLERANCE = 0.05

    def analyze(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        tolerance: float = DEFAULT_TOLERANCE,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "pattern-recognition",
        model_id: str | None = "deterministic-pattern-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        if tolerance < 0.0:
            raise ValueError("tolerance cannot be negative")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        pattern, magnitude = self._detect_pattern(
            normalized,
            tolerance,
        )

        confidence = self._confidence(normalized)

        explanation = (
            f"Pattern recognition identified a {pattern} pattern "
            f"with magnitude {magnitude:.6f} from "
            f"{len(normalized)} normalized features."
        )

        prediction = IntelligencePrediction(
            prediction_id=prediction_id,
            entity_id=entity_id,
            intelligence_type=IntelligenceType.PATTERN,
            method=IntelligenceMethod.DETERMINISTIC,
            value=magnitude,
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
                "pattern": pattern,
                "magnitude": magnitude,
                "tolerance": tolerance,
            },
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.PATTERN,
            predictions=(prediction,),
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                f"Detected {pattern} pattern.",
            ),
            metadata={
                "pattern": pattern,
                "magnitude": magnitude,
                "tolerance": tolerance,
            },
        )

    @staticmethod
    def _detect_pattern(
        features: tuple[IntelligenceFeature, ...],
        tolerance: float,
    ) -> tuple[str, float]:

        if len(features) == 1:
            return "stable", 0.0

        values = tuple(
            feature.value
            for feature in features
        )

        differences = tuple(
            current - previous
            for previous, current
            in zip(
                values,
                values[1:],
            )
        )

        average_change = (
            sum(differences) / len(differences)
        )

        magnitude = abs(average_change)

        if magnitude <= tolerance:
            return "stable", magnitude

        if average_change > 0.0:
            return "increasing", magnitude

        return "decreasing", magnitude

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


def recognize_patterns(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    tolerance: float = PatternRecognitionEngine.DEFAULT_TOLERANCE,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "pattern-recognition",
    model_id: str | None = "deterministic-pattern-baseline",
) -> IntelligenceResult:

    return PatternRecognitionEngine().analyze(
        entity_id,
        features,
        tolerance=tolerance,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
