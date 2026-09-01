import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    EstimateStatus,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.inputs import (
    create_reconciliation_input,
    inputs_for_method,
    normalize_inputs,
    require_method_coverage,
    validate_input_units,
)


def make_estimate(
    value: float = 100.0,
    unit: str = "kg CH4/day",
    method: QuantificationMethod = QuantificationMethod.BOTTOM_UP,
) -> EmissionEstimate:
    return EmissionEstimate(
        estimate_id="est-1",
        method=method,
        level=QuantificationLevel.FACILITY,
        value=value,
        unit=unit,
        status=EstimateStatus.ESTIMATED,
    )


def test_create_reconciliation_input():
    item = create_reconciliation_input(
        "input-1",
        make_estimate(),
        weight=2.0,
        uncertainty=5.0,
        quality_score=0.9,
    )

    assert item.input_id == "input-1"
    assert item.weight == 2.0
    assert item.uncertainty == 5.0
    assert item.quality_score == 0.9


def test_create_reconciliation_input_rejects_negative_estimate():
    with pytest.raises(ValueError):
        create_reconciliation_input(
            "input-1",
            make_estimate(value=-1.0),
        )


def test_create_reconciliation_input_rejects_nonfinite_value():
    with pytest.raises(ValueError):
        create_reconciliation_input(
            "input-1",
            make_estimate(value=float("nan")),
        )


def test_normalize_inputs_preserves_order():
    first = create_reconciliation_input("first", make_estimate())
    second = create_reconciliation_input("second", make_estimate())

    result = normalize_inputs([first, second])

    assert result == (first, second)


def test_normalize_inputs_rejects_duplicates():
    first = create_reconciliation_input("input-1", make_estimate())
    second = create_reconciliation_input("input-1", make_estimate())

    with pytest.raises(ValueError):
        normalize_inputs([first, second])


def test_normalize_inputs_rejects_empty_collection():
    with pytest.raises(ValueError):
        normalize_inputs([])


def test_validate_input_units_accepts_matching_units():
    first = create_reconciliation_input(
        "first",
        make_estimate(unit="kg CH4/day"),
    )
    second = create_reconciliation_input(
        "second",
        make_estimate(unit="kg CH4/day"),
    )

    assert validate_input_units([first, second]) == "kg CH4/day"


def test_validate_input_units_rejects_mismatched_units():
    first = create_reconciliation_input(
        "first",
        make_estimate(unit="kg CH4/day"),
    )
    second = create_reconciliation_input(
        "second",
        make_estimate(unit="tonnes CH4/year"),
    )

    with pytest.raises(ValueError):
        validate_input_units([first, second])


def test_inputs_for_method_filters_correctly():
    bottom_up = create_reconciliation_input(
        "bottom-up",
        make_estimate(
            method=QuantificationMethod.BOTTOM_UP,
        ),
    )
    measurement = create_reconciliation_input(
        "measurement",
        make_estimate(
            method=QuantificationMethod.MEASUREMENT,
        ),
    )

    result = inputs_for_method(
        [bottom_up, measurement],
        "measurement",
    )

    assert result == (measurement,)


def test_require_method_coverage_accepts_complete_set():
    inputs = [
        create_reconciliation_input(
            "bottom-up",
            make_estimate(
                method=QuantificationMethod.BOTTOM_UP,
            ),
        ),
        create_reconciliation_input(
            "measurement",
            make_estimate(
                method=QuantificationMethod.MEASUREMENT,
            ),
        ),
        create_reconciliation_input(
            "top-down",
            make_estimate(
                method=QuantificationMethod.TOP_DOWN,
            ),
        ),
    ]

    require_method_coverage(inputs)


def test_require_method_coverage_rejects_missing_method():
    inputs = [
        create_reconciliation_input(
            "bottom-up",
            make_estimate(
                method=QuantificationMethod.BOTTOM_UP,
            ),
        ),
        create_reconciliation_input(
            "measurement",
            make_estimate(
                method=QuantificationMethod.MEASUREMENT,
            ),
        ),
    ]

    with pytest.raises(ValueError):
        require_method_coverage(inputs)
