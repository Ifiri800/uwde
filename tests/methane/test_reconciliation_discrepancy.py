import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.inputs import (
    create_reconciliation_input,
)
from backend.app.services.intelligence.methane.reconciliation.discrepancy import (
    calculate_discrepancy,
    calculate_pairwise_discrepancies,
)


def make_input(
    input_id: str,
    value: float,
    method: QuantificationMethod,
    unit: str = "kg CH4/day",
):
    estimate = EmissionEstimate(
        estimate_id=input_id,
        method=method,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit=unit,
    )

    return create_reconciliation_input(
        input_id,
        estimate,
    )


def test_calculate_discrepancy():
    item = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    result = calculate_discrepancy(
        item,
        120.0,
    )

    assert result.input_id == "bottom-up"
    assert result.method == QuantificationMethod.BOTTOM_UP
    assert result.estimate_value == 100.0
    assert result.fused_value == 120.0
    assert result.absolute_difference == 20.0
    assert result.relative_difference == pytest.approx(20 / 120)


def test_discrepancy_within_tolerance():
    item = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    result = calculate_discrepancy(
        item,
        105.0,
        tolerance=0.10,
    )

    assert result.within_tolerance is True


def test_discrepancy_outside_tolerance():
    item = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    result = calculate_discrepancy(
        item,
        120.0,
        tolerance=0.10,
    )

    assert result.within_tolerance is False


def test_discrepancy_zero_values():
    item = make_input(
        "bottom-up",
        0.0,
        QuantificationMethod.BOTTOM_UP,
    )

    result = calculate_discrepancy(
        item,
        0.0,
    )

    assert result.absolute_difference == 0.0
    assert result.relative_difference == 0.0
    assert result.within_tolerance is True


def test_discrepancy_rejects_negative_fused_value():
    item = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    with pytest.raises(ValueError):
        calculate_discrepancy(
            item,
            -1.0,
        )


def test_discrepancy_rejects_negative_tolerance():
    item = make_input(
        "bottom-up",
        100.0,
        QuantificationMethod.BOTTOM_UP,
    )

    with pytest.raises(ValueError):
        calculate_discrepancy(
            item,
            100.0,
            tolerance=-0.1,
        )


def test_pairwise_discrepancies():
    inputs = (
        make_input(
            "bottom-up",
            100.0,
            QuantificationMethod.BOTTOM_UP,
        ),
        make_input(
            "measurement",
            110.0,
            QuantificationMethod.MEASUREMENT,
        ),
        make_input(
            "top-down",
            90.0,
            QuantificationMethod.TOP_DOWN,
        ),
    )

    results = calculate_pairwise_discrepancies(inputs)

    assert len(results) == 3


def test_pairwise_discrepancies_empty():
    assert calculate_pairwise_discrepancies(()) == ()
