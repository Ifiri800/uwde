import pytest

from backend.app.services.intelligence.methane.intelligence.feature_engineering import (
    MethaneFeatureEngineer,
    build_methane_features,
)
from backend.app.services.intelligence.methane.reconciliation.models import (
    ConfidenceAssessment,
    DiscrepancyResult,
    ReconciledEstimate,
    ReconciliationInput,
    ReconciliationResult,
    ReconciliationStatus,
)
from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)


def make_estimate(
    estimate_id: str,
    method: QuantificationMethod,
    value: float,
) -> EmissionEstimate:
    return EmissionEstimate(
        estimate_id=estimate_id,
        method=method,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit="kg/h",
    )


def make_result(
    *,
    uncertainty: float | None = None,
) -> ReconciliationResult:
    inputs = (
        ReconciliationInput(
            input_id="input-1",
            estimate=make_estimate(
                "estimate-1",
                QuantificationMethod.BOTTOM_UP,
                10.0,
            ),
        ),
        ReconciliationInput(
            input_id="input-2",
            estimate=make_estimate(
                "estimate-2",
                QuantificationMethod.MEASUREMENT,
                12.0,
            ),
        ),
    )

    discrepancies = (
        DiscrepancyResult(
            input_id="input-1",
            method=QuantificationMethod.BOTTOM_UP,
            estimate_value=10.0,
            fused_value=11.0,
            absolute_difference=1.0,
            relative_difference=1.0 / 11.0,
        ),
    )

    estimate = ReconciledEstimate(
        reconciliation_id="reconciliation-1",
        value=11.0,
        unit="kg/h",
        status=ReconciliationStatus.RECONCILED,
        inputs=inputs,
        discrepancies=discrepancies,
        uncertainty=uncertainty,
    )

    confidence = ConfidenceAssessment(
        score=0.85,
        level="high",
    )

    return ReconciliationResult(
        estimate=estimate,
        discrepancies=discrepancies,
        confidence=confidence,
    )


def test_feature_engineer_builds_layer_10_features():
    result = make_result(
        uncertainty=0.5,
    )

    features = MethaneFeatureEngineer().build(result)

    names = {
        feature.name
        for feature in features
    }

    assert "reconciled_emission_value" in names
    assert "input_count" in names
    assert "discrepancy_count" in names
    assert "reconciliation_confidence" in names
    assert "reconciled_uncertainty" in names


def test_features_are_deterministically_sorted():
    features = build_methane_features(
        make_result()
    )

    names = [
        feature.name
        for feature in features
    ]

    assert names == sorted(names)


def test_feature_values_reflect_layer_9_output():
    features = build_methane_features(
        make_result(
            uncertainty=0.5,
        )
    )

    values = {
        feature.name: feature.value
        for feature in features
    }

    assert values["reconciled_emission_value"] == 11.0
    assert values["input_count"] == 2.0
    assert values["discrepancy_count"] == 1.0
    assert values["reconciliation_confidence"] == 0.85
    assert values["reconciled_uncertainty"] == 0.5
    assert values["uncertainty_available"] == 1.0


def test_missing_uncertainty_is_explicitly_encoded():
    features = build_methane_features(
        make_result()
    )

    values = {
        feature.name: feature.value
        for feature in features
    }

    assert values["reconciled_uncertainty"] == 0.0
    assert values["uncertainty_available"] == 0.0


def test_invalid_reconciliation_type_is_rejected():
    with pytest.raises(TypeError):
        MethaneFeatureEngineer().build(
            "invalid"
        )
