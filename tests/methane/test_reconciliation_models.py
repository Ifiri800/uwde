import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    EstimateStatus,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.models import (
    ConfidenceAssessment,
    DiscrepancyResult,
    FusionResult,
    ReconciledEstimate,
    ReconciliationInput,
    ReconciliationMethod,
    ReconciliationResult,
    ReconciliationStatus,
)


def make_estimate(
    value: float = 100.0,
    method: QuantificationMethod = QuantificationMethod.BOTTOM_UP,
) -> EmissionEstimate:
    return EmissionEstimate(
        estimate_id="est-1",
        method=method,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit="kg CH4/day",
        status=EstimateStatus.ESTIMATED,
    )


def test_reconciliation_input_accepts_valid_input():
    item = ReconciliationInput(
        input_id="input-1",
        estimate=make_estimate(),
        weight=2.0,
        uncertainty=5.0,
        quality_score=0.9,
    )

    assert item.input_id == "input-1"
    assert item.weight == 2.0
    assert item.uncertainty == 5.0
    assert item.quality_score == 0.9


def test_reconciliation_input_rejects_negative_weight():
    with pytest.raises(ValueError):
        ReconciliationInput(
            input_id="input-1",
            estimate=make_estimate(),
            weight=-1.0,
        )


def test_reconciliation_input_rejects_invalid_quality_score():
    with pytest.raises(ValueError):
        ReconciliationInput(
            input_id="input-1",
            estimate=make_estimate(),
            quality_score=1.5,
        )


def test_fusion_result_reports_input_count():
    item = ReconciliationInput(
        input_id="input-1",
        estimate=make_estimate(),
    )

    result = FusionResult(
        value=100.0,
        unit="kg CH4/day",
        method=ReconciliationMethod.WEIGHTED,
        inputs=(item,),
        total_weight=1.0,
    )

    assert result.input_count == 1


def test_discrepancy_agrees_when_values_match():
    result = DiscrepancyResult(
        input_id="input-1",
        method=QuantificationMethod.BOTTOM_UP,
        estimate_value=100.0,
        fused_value=100.0,
        absolute_difference=0.0,
        relative_difference=0.0,
    )

    assert result.agrees is True


def test_confidence_assessment_rejects_invalid_score():
    with pytest.raises(ValueError):
        ConfidenceAssessment(
            score=1.5,
            level="high",
        )


def test_reconciled_estimate_properties():
    item = ReconciliationInput(
        input_id="input-1",
        estimate=make_estimate(),
    )

    estimate = ReconciledEstimate(
        reconciliation_id="rec-1",
        value=100.0,
        unit="kg CH4/day",
        status=ReconciliationStatus.RECONCILED,
        inputs=(item,),
        uncertainty=10.0,
    )

    assert estimate.input_count == 1
    assert estimate.discrepancy_count == 0
    assert estimate.has_uncertainty is True
    assert estimate.has_confidence is False


def test_reconciliation_result_exposes_value():
    item = ReconciliationInput(
        input_id="input-1",
        estimate=make_estimate(),
    )

    fusion = FusionResult(
        value=100.0,
        unit="kg CH4/day",
        method=ReconciliationMethod.WEIGHTED,
        inputs=(item,),
        total_weight=1.0,
    )

    estimate = ReconciledEstimate(
        reconciliation_id="rec-1",
        value=100.0,
        unit="kg CH4/day",
        status=ReconciliationStatus.RECONCILED,
        inputs=(item,),
    )

    result = ReconciliationResult(
        estimate=estimate,
        fusion=fusion,
    )

    assert result.value == 100.0
    assert result.input_count == 1
    assert result.has_warnings is False
