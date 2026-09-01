import pytest

from backend.app.services.intelligence.methane.quantification.uncertainty.models import (
    UncertaintyComponent,
    UncertaintySource,
)
from backend.app.services.intelligence.methane.quantification.uncertainty.propagation import (
    combine_absolute_uncertainties,
    combine_components,
    propagate_product_uncertainty,
    relative_uncertainty,
)


def test_combine_absolute_uncertainties():
    result = combine_absolute_uncertainties(
        [3.0, 4.0]
    )

    assert result == pytest.approx(5.0)


def test_combine_absolute_uncertainties_empty():
    result = combine_absolute_uncertainties([])

    assert result == pytest.approx(0.0)


def test_negative_absolute_uncertainty_is_rejected():
    with pytest.raises(ValueError):
        combine_absolute_uncertainties(
            [1.0, -2.0]
        )


def test_combine_components_uses_standard_deviation():
    components = (
        UncertaintyComponent(
            component_id="activity",
            source=UncertaintySource.ACTIVITY_DATA,
            value=10.0,
            unit="kg/h",
            standard_deviation=3.0,
        ),
        UncertaintyComponent(
            component_id="factor",
            source=UncertaintySource.EMISSION_FACTOR,
            value=20.0,
            unit="kg/h",
            standard_deviation=4.0,
        ),
    )

    result = combine_components(components)

    assert result == pytest.approx(5.0)


def test_combine_components_falls_back_to_value():
    component = UncertaintyComponent(
        component_id="measurement",
        source=UncertaintySource.MEASUREMENT,
        value=5.0,
        unit="kg/h",
    )

    assert combine_components([component]) == pytest.approx(5.0)


def test_propagate_product_uncertainty():
    result = propagate_product_uncertainty(
        value=100.0,
        relative_uncertainties=[0.03, 0.04],
    )

    assert result == pytest.approx(5.0)


def test_propagate_product_uncertainty_zero_value():
    result = propagate_product_uncertainty(
        value=0.0,
        relative_uncertainties=[0.03, 0.04],
    )

    assert result == pytest.approx(0.0)


def test_propagate_product_uncertainty_rejects_negative_value():
    with pytest.raises(ValueError):
        propagate_product_uncertainty(
            value=-100.0,
            relative_uncertainties=[0.03],
        )


def test_propagate_product_uncertainty_rejects_negative_uncertainty():
    with pytest.raises(ValueError):
        propagate_product_uncertainty(
            value=100.0,
            relative_uncertainties=[0.03, -0.04],
        )


def test_relative_uncertainty():
    result = relative_uncertainty(
        value=100.0,
        uncertainty=5.0,
    )

    assert result == pytest.approx(0.05)


def test_relative_uncertainty_rejects_zero_value():
    with pytest.raises(ValueError):
        relative_uncertainty(
            value=0.0,
            uncertainty=5.0,
        )


def test_relative_uncertainty_rejects_negative_value():
    with pytest.raises(ValueError):
        relative_uncertainty(
            value=-100.0,
            uncertainty=5.0,
        )


def test_relative_uncertainty_rejects_negative_uncertainty():
    with pytest.raises(ValueError):
        relative_uncertainty(
            value=100.0,
            uncertainty=-1.0,
        )
