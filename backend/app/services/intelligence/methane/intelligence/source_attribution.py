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


class SourceAttributionEngine:
    """
    Deterministic source-attribution engine.

    Scores normalized candidate source features and identifies the
    highest-confidence contributors to an observed methane signal.

    Feature values are treated as non-negative attribution strengths.
    Feature confidence is incorporated into the attribution score.
    """

    def predict(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
        prediction_id: str = "source-attribution",
        model_id: str | None = "deterministic-attribution-baseline",
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        scores = self._scores(normalized)

        predictions = tuple(
            self._build_prediction(
                entity_id=entity_id,
                feature=feature,
                score=score,
                index=index,
                signal_ids=signal_ids,
                evidence_ids=evidence_ids,
                prediction_id=prediction_id,
                model_id=model_id,
            )
            for index, (feature, score) in enumerate(
                scores,
                start=1,
            )
        )

        confidence = self._confidence(normalized)

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.SOURCE_ATTRIBUTION,
            predictions=predictions,
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=(
                "Source attribution is based on normalized "
                "candidate-source strength and feature confidence.",
            ),
        )

    @staticmethod
    def _scores(
        features: tuple[IntelligenceFeature, ...],
    ) -> tuple[tuple[IntelligenceFeature, float], ...]:

        weighted = tuple(
            (
                feature,
                max(0.0, feature.value)
                * feature.confidence,
            )
            for feature in features
        )

        total = sum(score for _, score in weighted)

        if total <= 0.0:
            return tuple(
                (feature, 0.0)
                for feature, _ in weighted
            )

        return tuple(
            (feature, score / total)
            for feature, score in weighted
        )

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

    @staticmethod
    def _build_prediction(
        *,
        entity_id: str,
        feature: IntelligenceFeature,
        score: float,
        index: int,
        signal_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        prediction_id: str,
        model_id: str | None,
    ) -> IntelligencePrediction:

        explanation = (
            f"Candidate source '{feature.name}' received an "
            f"attribution score of {score:.6f} based on its "
            "normalized source strength and feature confidence."
        )

        return IntelligencePrediction(
            prediction_id=(
                f"{prediction_id}-{index}-{feature.name}"
            ),
            entity_id=entity_id,
            intelligence_type=IntelligenceType.SOURCE_ATTRIBUTION,
            method=IntelligenceMethod.DETERMINISTIC,
            value=score,
            confidence=feature.confidence,
            feature_names=(feature.name,),
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id=model_id,
            explanation=explanation,
            metadata={
                "source": feature.source,
                "unit": feature.unit,
                "attribution_score": score,
            },
        )


def attribute_sources(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    prediction_id: str = "source-attribution",
    model_id: str | None = "deterministic-attribution-baseline",
) -> IntelligenceResult:

    return SourceAttributionEngine().predict(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
        prediction_id=prediction_id,
        model_id=model_id,
    )
