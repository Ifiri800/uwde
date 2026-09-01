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


class DataFusionEngine:
    """
    Deterministic Layer 10 intelligence data-fusion engine.

    Combines normalized intelligence features into a bounded,
    confidence-weighted intelligence signal.

    This is intentionally distinct from Layer 9 reconciliation:
    Layer 9 reconciles emission estimates, while Layer 10 fuses
    intelligence features, signals, and evidence.
    """

    def predict(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "data-fusion",
        model_id: str | None = "deterministic-fusion-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        fused_value = self._fused_value(normalized)
        confidence = self._confidence(normalized)

        feature_names = tuple(
            feature.name
            for feature in normalized
        )

        explanation = (
            "Intelligence data fusion derived from "
            f"{len(normalized)} normalized features using a "
            "deterministic confidence-weighted baseline."
        )

        prediction = IntelligencePrediction(
            prediction_id=prediction_id,
            entity_id=entity_id,
            intelligence_type=IntelligenceType.DATA_FUSION,
            method=IntelligenceMethod.DETERMINISTIC,
            value=fused_value,
            confidence=confidence,
            feature_names=feature_names,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id=model_id,
            explanation=explanation,
            metadata={
                "feature_count": len(normalized),
                "fusion_method": "confidence_weighted_mean",
            },
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.DATA_FUSION,
            predictions=(prediction,),
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                "Multiple intelligence features were fused into "
                "a single bounded intelligence signal.",
            ),
            metadata={
                "fusion_method": "confidence_weighted_mean",
                "feature_count": len(normalized),
            },
        )

    @staticmethod
    def _fused_value(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:

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


def fuse_intelligence(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "data-fusion",
    model_id: str | None = "deterministic-fusion-baseline",
) -> IntelligenceResult:

    return DataFusionEngine().predict(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
