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


class EmissionPredictionEngine:
    """
    Deterministic methane emission prediction engine.

    This implementation provides a transparent baseline prediction
    from normalized intelligence features. It is intentionally
    bounded and explainable so that statistical and ML models can
    replace or extend it later without changing the public result
    contract.
    """

    def predict(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "emission-prediction",
        model_id: str | None = "deterministic-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        prediction_value = self._predict_value(normalized)
        confidence = self._confidence(normalized)

        feature_names = tuple(
            feature.name
            for feature in normalized
        )

        explanation = (
            "Emission prediction derived from "
            f"{len(normalized)} normalized intelligence features "
            "using a deterministic bounded baseline."
        )

        prediction = IntelligencePrediction(
            prediction_id=prediction_id,
            entity_id=entity_id,
            intelligence_type=(
                IntelligenceType.EMISSION_PREDICTION
            ),
            method=IntelligenceMethod.DETERMINISTIC,
            value=prediction_value,
            confidence=confidence,
            feature_names=feature_names,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id=model_id,
            explanation=explanation,
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=(
                IntelligenceType.EMISSION_PREDICTION
            ),
            predictions=(prediction,),
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                "Prediction is based on normalized "
                "intelligence features.",
            ),
        )

    @staticmethod
    def _predict_value(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:
        """
        Calculate a bounded weighted feature prediction.

        Feature confidence acts as the weighting factor. The result
        is the confidence-weighted mean of the supplied feature
        values and is therefore deterministic and non-negative.
        """

        total_weight = sum(
            feature.confidence
            for feature in features
        )

        if total_weight <= 0.0:
            return 0.0

        value = sum(
            feature.value * feature.confidence
            for feature in features
        ) / total_weight

        return max(0.0, value)

    @staticmethod
    def _confidence(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:
        """
        Derive prediction confidence from feature confidence.
        """

        if not features:
            return 0.0

        confidence = sum(
            feature.confidence
            for feature in features
        ) / len(features)

        return min(1.0, max(0.0, confidence))


def predict_emissions(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "emission-prediction",
    model_id: str | None = "deterministic-baseline",
) -> IntelligenceResult:

    return EmissionPredictionEngine().predict(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
