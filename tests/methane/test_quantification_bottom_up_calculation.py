from math import isclose

import pytest

from backend.app.services.intelligence.methane.quantification.bottom_up.calculation import (
    BottomUpCalculation,
    BottomUpResult,
    calculate_bottom_up,
)


def test_bottom_up_calculation_accepts_valid_inputs():
    calculation = BottomUpCalculation(
        activity=100.0,
        emission_factor=0.25,
    )

    assert calculation.activity == 100.0
    assert calculation.emission_factor == 0.25


def test_bottom_up_calculation_rejects_negative_activity():
    with pytest.raises(ValueError):
        BottomUpCalculation(
            activity=-1.0,
            emission_factor=0.25,
        )


def test_bottom_up_calculation_rejects_negative_emission_factor():
    with pytest.raises(ValueError):
        BottomUpCalculation(
            activity=100.0,
            emission_factor=-0.25,
        )


def test_bottom_up_result_contains_calculated_emissions():
    result = BottomUpResult(
        activity=100.0,
        emission_factor=0.25,
        methane_emissions=25.0,
    )

    assert result.activity == 100.0
    assert result.emission_factor == 0.25
    assert result.methane_emissions == 25.0


def test_bottom_up_result_rejects_negative_emissions():
    with pytest.raises(ValueError):
        BottomUpResult(
            activity=100.0,
            emission_factor=0.25,
            methane_emissions=-1.0,
        )


def test_calculation_returns_expected_methane_emissions():
    calculation = BottomUpCalculation(
        activity=100.0,
        emission_factor=0.25,
    )

    result = calculate_bottom_up(
        calculation=calculation,
    )

    assert result.methane_emissions == pytest.approx(25.0)


def test_calculation_preserves_inputs():
    calculation = BottomUpCalculation(
        activity=250.0,
        emission_factor=0.4,
    )

    result = calculate_bottom_up(
        calculation=calculation,
    )

    assert result.activity == calculation.activity
    assert result.emission_factor == calculation.emission_factor


def test_calculation_handles_zero_activity():
    calculation = BottomUpCalculation(
        activity=0.0,
        emission_factor=0.5,
    )

    result = calculate_bottom_up(
        calculation=calculation,
    )

    assert isclose(
        result.methane_emissions,
        0.0,
    )


def test_calculation_handles_zero_emission_factor():
    calculation = BottomUpCalculation(
        activity=100.0,
        emission_factor=0.0,
    )

    result = calculate_bottom_up(
        calculation=calculation,
    )

    assert isclose(
        result.methane_emissions,
        0.0,
    )


def test_calculation_rejects_invalid_calculation_object():
    with pytest.raises(ValueError):
        calculate_bottom_up(
            calculation=None,
        )
