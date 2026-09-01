import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.inputs import (
    create_reconciliation_input,
)
from backend.app.services.intelligence.methane.reconciliation.reconciliation import (
    reconcile,
)
from backend.app.services.intelligence.methane.reconciliation.models import (
    ReconciliationStatus,
)


def make_input(
    input_id: str,
    value: float,
    method: QuantificationMethod,
    *,
    uncertainty: float | None = None,
    weight: float = 1.0,
):
    estimate = EmissionEstimate(
        estimate_id=input_id,
        method=method,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit="kg CH4/day",
    )

    return create_reconciliation_input(
        input_id,
        estimate,
        uncertainty=uncertainty,
        weight=weight,
    )


def complete_inputs():
    return [
        make_input(
            "bottom-up",
            100.0,
            QuantificationMethod.BOTTOM_UP,
            uncertainty=10.0,
        ),
        make_input(
            "measurement",
            110.0,
            QuantificationMethod.MEASUREMENT,
            uncertainty=10.0,
        ),
        make_input(
            "top-down",
            90.0,
            QuantificationMethod.TOP_DOWN,
            uncertainty=10.0,
        ),
    ]


def test_reconcile_returns_reconciled_estimate():
    result = reconcile(
        complete_inputs(),
        reconciliation_id="rec-1",
    )

    assert result.estimate.reconciliation_id == "rec-1"
    assert result.estimate.status == ReconciliationStatus.RECONCILED
    assert result.estimate.value == pytest.approx(100.0)
    assert result.estimate.unit == "kg CH4/day"


def test_reconcile_preserves_inputs():
    inputs = complete_inputs()

    result = reconcile(inputs)

    assert result.estimate.inputs == tuple(inputs)
    assert result.input_count == 3


def test_reconcile_calculates_uncertainty():
    result = reconcile(complete_inputs())

    assert result.estimate.uncertainty is not None
    assert result.estimate.uncertainty > 0


def test_reconcile_calculates_confidence():
    result = reconcile(complete_inputs())

    assert result.confidence is not None
    assert 0.0 <= result.confidence.score <= 1.0
    assert result.estimate.confidence is not None


def test_reconcile_calculates_pairwise_discrepancies():
    result = reconcile(complete_inputs())

    assert len(result.discrepancies) == 3
    assert result.estimate.discrepancy_count == 3


def test_reconcile_generates_warning_for_large_discrepancy():
    inputs = [
        make_input(
            "bottom-up",
            100.0,
            QuantificationMethod.BOTTOM_UP,
        ),
        make_input(
            "measurement",
            200.0,
            QuantificationMethod.MEASUREMENT,
        ),
        make_input(
            "top-down",
            100.0,
            QuantificationMethod.TOP_DOWN,
        ),
    ]

    result = reconcile(
        inputs,
        tolerance=0.10,
    )

    assert result.has_warnings
    assert len(result.warnings) == 1


def test_reconcile_no_warning_when_within_tolerance():
    inputs = [
        make_input(
            "bottom-up",
            100.0,
            QuantificationMethod.BOTTOM_UP,
        ),
        make_input(
            "measurement",
            105.0,
            QuantificationMethod.MEASUREMENT,
        ),
        make_input(
            "top-down",
            95.0,
            QuantificationMethod.TOP_DOWN,
        ),
    ]

    result = reconcile(
        inputs,
        tolerance=0.10,
    )

    assert not result.has_warnings


def test_reconcile_rejects_mismatched_units():
    first = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    second_estimate = EmissionEstimate(
        estimate_id="measurement",
        method=QuantificationMethod.MEASUREMENT,
        level=QuantificationLevel.FACILITY,
        value=100.0,
        unit="tonnes CH4/year",
    )

    second = create_reconciliation_input(
        "measurement",
        second_estimate,
    )

    result = reconcile([first, second])

    assert result.estimate.status == ReconciliationStatus.REJECTED
    assert result.has_warnings


def test_reconcile_empty_inputs_is_rejected():
    result = reconcile([])

    assert result.estimate.status == ReconciliationStatus.REJECTED
    assert result.value == 0.0
    assert result.has_warnings


def test_reconcile_custom_id_is_preserved():
    result = reconcile(
        complete_inputs(),
        reconciliation_id="custom-reconciliation-id",
    )

    assert (
        result.estimate.reconciliation_id
        == "custom-reconciliation-id"
    )


def test_reconcile_generates_id_when_missing():
    result = reconcile(complete_inputs())

    assert result.estimate.reconciliation_id.startswith("rec-")


def test_reconcile_is_deterministic_for_same_inputs():
    inputs = complete_inputs()

    first = reconcile(
        inputs,
        reconciliation_id="rec-a",
    )
    second = reconcile(
        inputs,
        reconciliation_id="rec-b",
    )

    assert first.value == pytest.approx(second.value)
    assert first.estimate.uncertainty == pytest.approx(
        second.estimate.uncertainty
    )
    assert first.confidence.score == pytest.approx(
        second.confidence.score
    )


def test_reconcile_respects_explicit_weights():
    inputs = [
        make_input(
            "bottom-up",
            100.0,
            QuantificationMethod.BOTTOM_UP,
            weight=3.0,
        ),
        make_input(
            "measurement",
            200.0,
            QuantificationMethod.MEASUREMENT,
            weight=1.0,
        ),
        make_input(
            "top-down",
            100.0,
            QuantificationMethod.TOP_DOWN,
            weight=1.0,
        ),
    ]

    result = reconcile(inputs)

    assert result.value == pytest.approx(120.0)
