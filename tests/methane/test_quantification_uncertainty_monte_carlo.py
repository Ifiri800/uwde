from math import isclose

import pytest

from backend.app.services.intelligence.methane.quantification.uncertainty.monte_carlo import (
    MonteCarloResult,
    MonteCarloSimulation,
    simulate_monte_carlo,
)


def test_monte_carlo_result_contains_summary_statistics():
    result = MonteCarloResult(
        samples=(90.0, 100.0, 110.0),
        mean=100.0,
        median=100.0,
        standard_deviation=10.0,
        lower_percentile=90.0,
        upper_percentile=110.0,
    )

    assert result.samples == (90.0, 100.0, 110.0)
    assert result.mean == 100.0
    assert result.median == 100.0
    assert result.standard_deviation == 10.0
    assert result.lower_percentile == 90.0
    assert result.upper_percentile == 110.0


def test_monte_carlo_result_rejects_empty_samples():
    with pytest.raises(ValueError):
        MonteCarloResult(
            samples=(),
            mean=0.0,
            median=0.0,
            standard_deviation=0.0,
            lower_percentile=0.0,
            upper_percentile=0.0,
        )


def test_monte_carlo_result_rejects_invalid_percentile_order():
    with pytest.raises(ValueError):
        MonteCarloResult(
            samples=(100.0,),
            mean=100.0,
            median=100.0,
            standard_deviation=0.0,
            lower_percentile=110.0,
            upper_percentile=90.0,
        )


def test_simulation_accepts_valid_configuration():
    simulation = MonteCarloSimulation(
        iterations=1000,
        seed=42,
    )

    assert simulation.iterations == 1000
    assert simulation.seed == 42


def test_simulation_rejects_zero_iterations():
    with pytest.raises(ValueError):
        MonteCarloSimulation(iterations=0)


def test_simulation_rejects_negative_iterations():
    with pytest.raises(ValueError):
        MonteCarloSimulation(iterations=-1)


def test_simulation_rejects_negative_seed():
    with pytest.raises(ValueError):
        MonteCarloSimulation(
            iterations=100,
            seed=-1,
        )


def test_monte_carlo_is_reproducible_with_seed():
    simulation = MonteCarloSimulation(
        iterations=1000,
        seed=42,
    )

    first = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    second = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    assert first.samples == second.samples


def test_monte_carlo_generates_requested_number_of_samples():
    simulation = MonteCarloSimulation(
        iterations=500,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    assert len(result.samples) == 500


def test_monte_carlo_mean_is_close_to_input_mean():
    simulation = MonteCarloSimulation(
        iterations=10_000,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    assert abs(result.mean - 100.0) < 0.5


def test_monte_carlo_standard_deviation_is_reasonable():
    simulation = MonteCarloSimulation(
        iterations=10_000,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    assert 9.0 < result.standard_deviation < 11.0


def test_monte_carlo_rejects_negative_standard_deviation():
    simulation = MonteCarloSimulation(
        iterations=100,
        seed=42,
    )

    with pytest.raises(ValueError):
        simulate_monte_carlo(
            simulation=simulation,
            mean=100.0,
            standard_deviation=-1.0,
        )


def test_monte_carlo_accepts_zero_standard_deviation():
    simulation = MonteCarloSimulation(
        iterations=100,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=0.0,
    )

    assert all(
        isclose(sample, 100.0)
        for sample in result.samples
    )

    assert result.mean == pytest.approx(100.0)
    assert result.median == pytest.approx(100.0)
    assert result.standard_deviation == pytest.approx(0.0)
    assert result.lower_percentile == pytest.approx(100.0)
    assert result.upper_percentile == pytest.approx(100.0)


def test_monte_carlo_percentiles_are_ordered():
    simulation = MonteCarloSimulation(
        iterations=5000,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
    )

    assert result.lower_percentile <= result.median
    assert result.median <= result.upper_percentile


def test_monte_carlo_supports_custom_confidence_level():
    simulation = MonteCarloSimulation(
        iterations=5000,
        seed=42,
    )

    result = simulate_monte_carlo(
        simulation=simulation,
        mean=100.0,
        standard_deviation=10.0,
        confidence_level=0.90,
    )

    assert result.lower_percentile < result.upper_percentile


def test_monte_carlo_rejects_invalid_confidence_level():
    simulation = MonteCarloSimulation(
        iterations=100,
        seed=42,
    )

    with pytest.raises(ValueError):
        simulate_monte_carlo(
            simulation=simulation,
            mean=100.0,
            standard_deviation=10.0,
            confidence_level=1.5,
        )
