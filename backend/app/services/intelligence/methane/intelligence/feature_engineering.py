from __future__ import annotations

from collections.abc import Iterable

from backend.app.services.intelligence.methane.intelligence.features import (
    normalize_features,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
)
from backend.app.services.intelligence.methane.reconciliation.models import (
    ReconciliationResult,
)


class MethaneFeatureEngineer:
    """
    Deterministic Layer 10 feature engineering.

    Converts Layer 9 reconciliation output into normalized,
    explainable features for downstream intelligence engines.

    This component does not predict, classify, prioritize, or
    recommend actions.
    """

    def build(
        self,
        reconciliation: ReconciliationResult,
    ) -> tuple[IntelligenceFeature, ...]:
        if not isinstance(
            reconciliation,
            ReconciliationResult,
        ):
            raise TypeError(
                "reconciliation must be a ReconciliationResult"
            )

        estimate = reconciliation.estimate

        features: list[IntelligenceFeature] = []

        features.extend(
            self._estimate_features(
                reconciliation,
            )
        )

        features.extend(
            self._input_features(
                reconciliation,
            )
        )

        features.extend(
            self._discrepancy_features(
                reconciliation,
            )
        )

        features.extend(
            self._confidence_features(
                reconciliation,
            )
        )

        features.extend(
            self._uncertainty_features(
                reconciliation,
            )
        )

        return normalize_features(features)

    @staticmethod
    def _estimate_features(
        reconciliation: ReconciliationResult,
    ) -> list[IntelligenceFeature]:
        estimate = reconciliation.estimate

        return [
            IntelligenceFeature(
                name="reconciled_emission_value",
                value=estimate.value,
                source="layer_9_reconciliation",
                unit=estimate.unit,
            ),
            IntelligenceFeature(
                name="input_count",
                value=float(estimate.input_count),
                source="layer_9_reconciliation",
                unit="count",
            ),
            IntelligenceFeature(
                name="discrepancy_count",
                value=float(estimate.discrepancy_count),
                source="layer_9_reconciliation",
                unit="count",
            ),
        ]

    @staticmethod
    def _input_features(
        reconciliation: ReconciliationResult,
    ) -> list[IntelligenceFeature]:
        inputs = reconciliation.estimate.inputs

        if not inputs:
            return [
                IntelligenceFeature(
                    name="input_coverage",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit="ratio",
                )
            ]

        methods = {
            item.method.value
            for item in inputs
        }

        return [
            IntelligenceFeature(
                name="input_coverage",
                value=min(1.0, len(inputs) / 3.0),
                source="layer_9_reconciliation",
                unit="ratio",
            ),
            IntelligenceFeature(
                name="quantification_method_diversity",
                value=min(1.0, len(methods) / 3.0),
                source="layer_9_reconciliation",
                unit="ratio",
            ),
        ]

    @staticmethod
    def _discrepancy_features(
        reconciliation: ReconciliationResult,
    ) -> list[IntelligenceFeature]:
        discrepancies = reconciliation.discrepancies

        if not discrepancies:
            return [
                IntelligenceFeature(
                    name="mean_relative_discrepancy",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit="ratio",
                ),
                IntelligenceFeature(
                    name="maximum_relative_discrepancy",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit="ratio",
                ),
            ]

        relative_values = [
            abs(item.relative_difference)
            for item in discrepancies
        ]

        return [
            IntelligenceFeature(
                name="mean_relative_discrepancy",
                value=sum(relative_values) / len(relative_values),
                source="layer_9_reconciliation",
                unit="ratio",
            ),
            IntelligenceFeature(
                name="maximum_relative_discrepancy",
                value=max(relative_values),
                source="layer_9_reconciliation",
                unit="ratio",
            ),
        ]

    @staticmethod
    def _confidence_features(
        reconciliation: ReconciliationResult,
    ) -> list[IntelligenceFeature]:
        confidence = reconciliation.confidence

        if confidence is None:
            return [
                IntelligenceFeature(
                    name="reconciliation_confidence",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit="ratio",
                )
            ]

        return [
            IntelligenceFeature(
                name="reconciliation_confidence",
                value=confidence.score,
                source="layer_9_reconciliation",
                unit="ratio",
            )
        ]

    @staticmethod
    def _uncertainty_features(
        reconciliation: ReconciliationResult,
    ) -> list[IntelligenceFeature]:
        estimate = reconciliation.estimate

        if estimate.uncertainty is None:
            return [
                IntelligenceFeature(
                    name="reconciled_uncertainty",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit=None,
                ),
                IntelligenceFeature(
                    name="uncertainty_available",
                    value=0.0,
                    source="layer_9_reconciliation",
                    unit="boolean",
                ),
            ]

        return [
            IntelligenceFeature(
                name="reconciled_uncertainty",
                value=estimate.uncertainty,
                source="layer_9_reconciliation",
                unit=estimate.unit,
            ),
            IntelligenceFeature(
                name="uncertainty_available",
                value=1.0,
                source="layer_9_reconciliation",
                unit="boolean",
            ),
        ]


def build_methane_features(
    reconciliation: ReconciliationResult,
) -> tuple[IntelligenceFeature, ...]:
    """
    Convenience function using the default methane feature engineer.
    """
    return MethaneFeatureEngineer().build(
        reconciliation
    )
