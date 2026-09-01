import pytest

from backend.app.services.intelligence.methane.quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)
from backend.app.services.intelligence.methane.reconciliation.inputs import (
    create_reconciliation_input,
)
from backend.app.services.intelligence.methane.reconciliation.fusion import (
    calculate_weight,
    fused_uncertainty,
    weighted_fusion,
)


def make_input(
    input_id: str,
    value: float,
    *,
    weight: float = 1.0,
    uncertainty: float | None = None,
    method: QuantificationMethod = QuantificationMethod.BOTTOM_UP,
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
        weight=weight,
        uncertainty=uncertainty,
    )


def test_calculate_weight_uses_explicit_weight():
    item = make_input(
        "input-1",
        100.0,
        weight=3.0,
    )

    assert calculate_weight(item) == 3.0


def test_calculate_weight_defaults_to_one():
    item = make_input(
        "input-1",
        100.0,
    )

    assert calculate_weight(item) == 1.0


def test_weighted_fusion_single_input():
    item = make_input(
        "input-1",
        100.0,
    )

    assert weighted_fusion([item]) == 100.0


def test_weighted_fusion_equal_weights():
    first = make_input(
        "first",
        100.0,
    )
    second = make_input(
        "second",
        200.0,
    )

    assert weighted_fusion([first, second]) == 150.0


def test_weighted_fusion_respects_weights():
    first = make_input(
        "first",
        100.0,
        weight=1.0,
    )
    second = make_input(
        "second",
        200.0,
        weight=3.0,
    )

    result = weighted_fusion([first, second])

    assert result == pytest.approx(175.0)


def test_weighted_fusion_rejects_empty_inputs():
    with pytest.raises(ValueError):
        weighted_fusion([])


def test_weighted_fusion_rejects_zero_total_weight():
    first = make_input(
        "first",
        100.0,
        weight=0.0,
    )
    second = make_input(
        "second",
        200.0,
        weight=0.0,
    )

    with pytest.raises(ValueError):
        weighted_fusion([first, second])


def test_fused_uncertainty_with_known_uncertainties():
    first = make_input(
        "first",
        100.0,
        weight=1.0,
        uncertainty=10.0,
    )
    second = make_input(
        "second",
        100.0,
        weight=1.0,
        uncertainty=20.0,
    )

    result = fused_uncertainty([first, second])

    assert result == pytest.approx((250.0) ** 0.5)


def test_fused_uncertainty_returns_none_without_uncertainty():
    first = make_input(
        "first",
        100.0,
    )
    second = make_input(
        "second",
        200.0,
    )

    assert fused_uncertainty([first, second]) is None


def test_fused_uncertainty_single_input():
    item = make_input(
        "input-1",
        100.0,
        uncertainty=10.0,
    )

    assert fused_uncertainty([item]) == pytest.approx(10.0)


def test_fused_uncertainty_rejects_empty_inputs():
    with pytest.raises(ValueError):
        fused_uncertainty([])
