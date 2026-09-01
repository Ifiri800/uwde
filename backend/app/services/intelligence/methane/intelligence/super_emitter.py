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


class SuperEmitterDetectionEngine:
    """
    Deterministic super-emitter detection engine.

    A feature is treated as a candidate super-emitter when its value
    meets or exceeds the configured absolute threshold.

    This is intentionally a transparent baseline. Statistical and
    machine-learning classifiers can later replace this detector
    while preserving the Layer 10 result contract.
    """

    DEFAULT_THRESHOLD = 100.0

    def detect(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        threshold: float = DEFAULT_THRESHOLD,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
    ) -> IntelligenceResult:

        if not isinstance(entity_id, str):
            raise TypeError("entity_id must be a string")

        if not entity_id.strip():
            raise ValueError("entity_id is required")

        if threshold < 0.0:
            raise ValueError("threshold cannot be negative")

        normalized = normalize_features(features)

        if not normalized:
            raise ValueError("at least one feature is required")

        candidates = tuple(
            feature
            for feature in normalized
            if feature.value >= threshold
        )

        predictions = tuple(
            self._build_prediction(
                entity_id=entity_id,
                feature=feature,
                threshold=threshold,
                index=index,
                signal_ids=signal_ids,
                evidence_ids=evidence_ids,
            )
            for index, feature in enumerate(candidates, start=1)
        )

        confidence = (
            sum(
                feature.confidence
                for feature in candidates
            )
            / len(candidates)
            if candidates
            else 0.0
        )

        reasons = (
            (
                f"{len(candidates)} feature(s) met or exceeded "
                f"the super-emitter threshold of {threshold}."
            )
            if candidates
            else (
                "No feature met or exceeded the configured "
                f"super-emitter threshold of {threshold}."
            )
        )

        warnings = (
            (
                "Super-emitter detection is threshold-based and "
                "does not constitute independent source verification."
            ),
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.SUPER_EMITTER,
            predictions=predictions,
            features=normalized,
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            warnings=warnings,
            reasons=(reasons,),
            metadata={
                "threshold": threshold,
                "candidate_count": len(candidates),
            },
        )

    @staticmethod
    def _build_prediction(
        *,
        entity_id: str,
        feature: IntelligenceFeature,
        threshold: float,
        index: int,
        signal_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
    ) -> IntelligencePrediction:

        ratio = (
            feature.value / threshold
            if threshold > 0.0
            else 1.0
        )

        confidence = min(
            1.0,
            max(
                feature.confidence,
                feature.confidence * min(ratio, 2.0) / 2.0,
            ),
        )

        explanation = (
            f"Feature '{feature.name}' has value "
            f"{feature.value}, which meets or exceeds the "
            f"super-emitter threshold of {threshold}."
        )

        return IntelligencePrediction(
            prediction_id=(
                f"super-emitter-{index}-{feature.name}"
            ),
            entity_id=entity_id,
            intelligence_type=IntelligenceType.SUPER_EMITTER,
            method=IntelligenceMethod.DETERMINISTIC,
            value=feature.value,
            confidence=confidence,
            feature_names=(feature.name,),
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            model_id="deterministic-threshold",
            explanation=explanation,
            metadata={
                "threshold": threshold,
                "threshold_ratio": ratio,
                "feature_source": feature.source,
                "feature_unit": feature.unit,
            },
        )


def detect_super_emitters(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    threshold: float = SuperEmitterDetectionEngine.DEFAULT_THRESHOLD,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
) -> IntelligenceResult:

    return SuperEmitterDetectionEngine().detect(
        entity_id,
        features,
        threshold=threshold,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
    )
