import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.confidence import (
    calculate_reconciliation_confidence,
    confidence_from_uncertainty,
)
from backend.app.services.intelligence.methane.reconciliation.inputs import (
    create_reconciliation_input,
)


def make_input(
    input_id: str,
    value: float = 100.0,
    uncertainty: float | None = None,
):
    estimate = EmissionEstimate(
        estimate_id=input_id,
        method=QuantificationMethod.BOTTOM_UP,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit="kg CH4/day",
    )

    return create_reconciliation_input(
        input_id,
        estimate,
        uncertainty=uncertainty,
    )


def test_confidence_from_uncertainty_no_uncertainty():
    assert confidence_from_uncertainty(100.0, None) == 0.5


def test_confidence_from_uncertainty_zero_uncertainty():
    assert confidence_from_uncertainty(100.0, 0.0) == 1.0


def test_confidence_from_uncertainty_ten_percent():
    assert confidence_from_uncertainty(100.0, 10.0) == pytest.approx(0.9)


def test_confidence_from_uncertainty_fifty_percent():
    assert confidence_from_uncertainty(100.0, 50.0) == pytest.approx(0.5)


def test_confidence_from_uncertainty_large_uncertainty_is_zero():
    assert confidence_from_uncertainty(100.0, 150.0) == 0.0


def test_confidence_from_uncertainty_zero_value_zero_uncertainty():
    assert confidence_from_uncertainty(0.0, 0.0) == 1.0


def test_confidence_from_uncertainty_zero_value_with_uncertainty():
    assert confidence_from_uncertainty(0.0, 10.0) == 0.0


def test_confidence_from_uncertainty_rejects_negative_value():
    with pytest.raises(ValueError):
        confidence_from_uncertainty(-1.0, 1.0)


def test_confidence_from_uncertainty_rejects_negative_uncertainty():
    with pytest.raises(ValueError):
        confidence_from_uncertainty(100.0, -1.0)


def test_confidence_is_bounded():
    assert 0.0 <= confidence_from_uncertainty(100.0, 0.0) <= 1.0
    assert 0.0 <= confidence_from_uncertainty(100.0, 50.0) <= 1.0
    assert 0.0 <= confidence_from_uncertainty(100.0, 500.0) <= 1.0


def test_reconciliation_confidence_single_input():
    item = make_input(
        "input-1",
        uncertainty=10.0,
    )

    assert calculate_reconciliation_confidence([item]) == pytest.approx(0.9)


def test_reconciliation_confidence_averages_inputs():
    first = make_input(
        "first",
        uncertainty=10.0,
    )
    second = make_input(
        "second",
        uncertainty=20.0,
    )

    result = calculate_reconciliation_confidence(
        [first, second],
    )

    assert result == pytest.approx(0.85)


def test_reconciliation_confidence_without_uncertainty():
    first = make_input("first")
    second = make_input("second")

    assert calculate_reconciliation_confidence(
        [first, second],
    ) == 0.5


def test_reconciliation_confidence_is_bounded():
    item = make_input(
        "input-1",
        uncertainty=1000.0,
    )

    result = calculate_reconciliation_confidence([item])

    assert 0.0 <= result <= 1.0


def test_reconciliation_confidence_rejects_empty_inputs():
    with pytest.raises(ValueError):
        calculate_reconciliation_confidence([])


def test_reconciliation_confidence_rejects_negative_penalty():
    item = make_input("input-1")

    with pytest.raises(ValueError):
        calculate_reconciliation_confidence(
            [item],
            discrepancy_penalty=-0.01,
        )


def test_reconciliation_confidence_rejects_penalty_above_one():
    item = make_input("input-1")

    with pytest.raises(ValueError):
        calculate_reconciliation_confidence(
            [item],
            discrepancy_penalty=1.01,
        )


def test_reconciliation_confidence_is_deterministic():
    first = make_input(
        "first",
        uncertainty=10.0,
    )
    second = make_input(
        "second",
        uncertainty=20.0,
    )

    result_a = calculate_reconciliation_confidence(
        [first, second],
    )
    result_b = calculate_reconciliation_confidence(
        [first, second],
    )

    assert result_a == result_b
