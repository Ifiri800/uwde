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


class EquipmentRiskPredictionEngine:
    """
    Deterministic equipment risk prediction engine.

    Produces an explainable baseline risk score from normalized
    equipment-related intelligence features.

    Feature confidence is incorporated into the weighted risk score.
    The result is bounded to [0.0, 1.0].
    """

    def predict(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "equipment-risk",
        model_id: str | None = "deterministic-risk-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        risk_score = self._risk_score(normalized)
        confidence = self._confidence(normalized)

        feature_names = tuple(
            feature.name
            for feature in normalized
        )

        explanation = (
            "Equipment risk prediction derived from "
            f"{len(normalized)} normalized equipment-risk features "
            "using a deterministic confidence-weighted baseline."
        )

        prediction = IntelligencePrediction(
            prediction_id=prediction_id,
            entity_id=entity_id,
            intelligence_type=IntelligenceType.EQUIPMENT_RISK,
            method=IntelligenceMethod.DETERMINISTIC,
            value=risk_score,
            confidence=confidence,
            feature_names=feature_names,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id=model_id,
            explanation=explanation,
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.EQUIPMENT_RISK,
            predictions=(prediction,),
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                "Equipment risk is calculated from normalized "
                "risk indicators and feature confidence.",
            ),
        )

    @staticmethod
    def _risk_score(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:

        total_weight = sum(
            feature.confidence
            for feature in features
        )

        if total_weight <= 0.0:
            return 0.0

        weighted_score = sum(
            min(1.0, max(0.0, feature.value))
            * feature.confidence
            for feature in features
        ) / total_weight

        return min(
            1.0,
            max(0.0, weighted_score),
        )

    @staticmethod
    def _confidence(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:

        if not features:
            return 0.0

        confidence = sum(
            feature.confidence
            for feature in features
        ) / len(features)

        return min(
            1.0,
            max(0.0, confidence),
        )


def predict_equipment_risk(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "equipment-risk",
    model_id: str | None = "deterministic-risk-baseline",
) -> IntelligenceResult:

    return EquipmentRiskPredictionEngine().predict(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
