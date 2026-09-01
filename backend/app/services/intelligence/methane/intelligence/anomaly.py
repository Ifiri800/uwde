from __future__ import annotations

from collections.abc import Iterable

from backend.app.services.intelligence.methane.intelligence.features import (
    feature_map,
    normalize_features,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligencePrediction,
    IntelligenceResult,
    IntelligenceType,
)


class MethaneAnomalyDetector:
    """
    Deterministic anomaly detector for Layer 10.

    The detector identifies unusual conditions from normalized
    methane intelligence features. It does not assign operational
    risk, LDAR priority, or recommended actions.
    """

    DEFAULT_THRESHOLD = 0.50

    def __init__(
        self,
        *,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0 and 1"
            )

        self.threshold = threshold

    def detect(
        self,
        entity_id: str,
        features: Iterable[IntelligenceFeature],
        *,
        signal_ids: tuple[str, ...] = (),
        evidence_ids: tuple[str, ...] = (),
    ) -> IntelligenceResult:
        if not isinstance(entity_id, str):
            raise TypeError(
                "entity_id must be a string"
            )

        if not entity_id.strip():
            raise ValueError(
                "entity_id is required"
            )

        normalized = normalize_features(features)
        values = feature_map(normalized)

        score, reasons = self._calculate_score(
            values
        )

        is_anomaly = score >= self.threshold

        prediction = IntelligencePrediction(
            prediction_id=f"{entity_id}:anomaly",
            entity_id=entity_id,
            intelligence_type=IntelligenceType.ANOMALY,
            method=IntelligenceMethod.DETERMINISTIC,
            value=score,
            confidence=self._confidence(
                normalized
            ),
            feature_names=tuple(
                feature.name
                for feature in normalized
            ),
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            explanation=self._explanation(
                entity_id=entity_id,
                score=score,
                is_anomaly=is_anomaly,
            ),
        )

        return IntelligenceResult(
            entity_id=entity_id,
            intelligence_type=IntelligenceType.ANOMALY,
            predictions=(prediction,),
            features=normalized,
            confidence=prediction.confidence,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _calculate_score(
        values: dict[str, float],
    ) -> tuple[float, list[str]]:
        """
        Calculate a bounded anomaly score.

        Current deterministic indicators:
        - relative reconciliation discrepancy
        - maximum reconciliation discrepancy
        - uncertainty
        - limited multi-method coverage
        """

        score = 0.0
        reasons: list[str] = []

        mean_discrepancy = min(
            1.0,
            abs(
                values.get(
                    "mean_relative_discrepancy",
                    0.0,
                )
            ),
        )

        maximum_discrepancy = min(
            1.0,
            abs(
                values.get(
                    "maximum_relative_discrepancy",
                    0.0,
                )
            ),
        )

        uncertainty = min(
            1.0,
            abs(
                values.get(
                    "reconciled_uncertainty",
                    0.0,
                )
            ),
        )

        method_diversity = values.get(
            "quantification_method_diversity",
            0.0,
        )

        discrepancy_component = (
            0.60 * mean_discrepancy
            + 0.40 * maximum_discrepancy
        )

        score += 0.70 * discrepancy_component
        score += 0.20 * uncertainty

        if method_diversity < 1.0:
            score += 0.10
            reasons.append(
                "quantification method coverage is limited"
            )

        if mean_discrepancy > 0.10:
            reasons.append(
                "mean reconciliation discrepancy is elevated"
            )

        if maximum_discrepancy > 0.20:
            reasons.append(
                "maximum reconciliation discrepancy is elevated"
            )

        if uncertainty > 0.20:
            reasons.append(
                "reconciled uncertainty is elevated"
            )

        return min(1.0, score), reasons

    @staticmethod
    def _confidence(
        features: tuple[IntelligenceFeature, ...],
    ) -> float:
        if not features:
            return 0.0

        return round(
            sum(
                feature.confidence
                for feature in features
            )
            / len(features),
            6,
        )

    @staticmethod
    def _explanation(
        *,
        entity_id: str,
        score: float,
        is_anomaly: bool,
    ) -> str:
        classification = (
            "anomalous"
            if is_anomaly
            else "within the deterministic baseline"
        )

        return (
            f"{entity_id} has an anomaly score of "
            f"{score:.6f} and is classified as "
            f"{classification}."
        )


def detect_methane_anomaly(
    entity_id: str,
    features: Iterable[IntelligenceFeature],
    *,
    signal_ids: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
) -> IntelligenceResult:
    """
    Convenience function using the default anomaly detector.
    """
    return MethaneAnomalyDetector().detect(
        entity_id,
        features,
        signal_ids=signal_ids,
        evidence_ids=evidence_ids,
    )
