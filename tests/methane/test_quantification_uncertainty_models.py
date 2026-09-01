import pytest

from backend.app.services.intelligence.methane.quantification.uncertainty.models import (
    DistributionType,
    MonteCarloConfig,
    MonteCarloResult,
    UncertaintyAssessment,
    UncertaintyComponent,
    UncertaintySource,
)


def test_uncertainty_sources_are_defined():
    assert UncertaintySource.ACTIVITY_DATA.value == "activity_data"
    assert UncertaintySource.EMISSION_FACTOR.value == "emission_factor"
    assert UncertaintySource.INSTRUMENT.value == "instrument"
    assert UncertaintySource.MEASUREMENT.value == "measurement"
    assert UncertaintySource.MODEL.value == "model"
    assert UncertaintySource.REMOTE_SENSING.value == "remote_sensing"


def test_distribution_types_are_defined():
    assert DistributionType.NORMAL.value == "normal"
    assert DistributionType.LOGNORMAL.value == "lognormal"
    assert DistributionType.UNIFORM.value == "uniform"


def test_uncertainty_component_accepts_valid_data():
    component = UncertaintyComponent(
        component_id="activity-001",
        source=UncertaintySource.ACTIVITY_DATA,
        value=10.0,
        unit="kg/h",
        distribution=DistributionType.NORMAL,
        standard_deviation=2.0,
    )

    assert component.component_id == "activity-001"
    assert component.source == UncertaintySource.ACTIVITY_DATA
    assert component.value == 10.0
    assert component.standard_deviation == 2.0


def test_uncertainty_assessment_defaults():
    assessment = UncertaintyAssessment(
        assessment_id="UA-001",
        estimate_id="EST-001",
    )

    assert assessment.component_count == 0
    assert assessment.has_uncertainty is False
    assert assessment.confidence_level == pytest.approx(0.95)


def test_uncertainty_assessment_with_components():
    component = UncertaintyComponent(
        component_id="measurement-001",
        source=UncertaintySource.MEASUREMENT,
        value=5.0,
        unit="kg/h",
    )

    assessment = UncertaintyAssessment(
        assessment_id="UA-002",
        estimate_id="EST-002",
        components=(component,),
        combined_uncertainty=5.0,
        uncertainty_unit="kg/h",
    )

    assert assessment.component_count == 1
    assert assessment.has_uncertainty is True
    assert assessment.combined_uncertainty == 5.0


def test_monte_carlo_config_defaults():
    config = MonteCarloConfig()

    assert config.iterations == 10_000
    assert config.random_seed is None
    assert config.lower_percentile == 5.0
    assert config.upper_percentile == 95.0


def test_monte_carlo_config_accepts_custom_values():
    config = MonteCarloConfig(
        iterations=5000,
        random_seed=42,
        lower_percentile=2.5,
        upper_percentile=97.5,
    )

    assert config.iterations == 5000
    assert config.random_seed == 42
    assert config.lower_percentile == 2.5
    assert config.upper_percentile == 97.5


def test_monte_carlo_config_rejects_zero_iterations():
    with pytest.raises(ValueError):
        MonteCarloConfig(iterations=0)


def test_monte_carlo_config_rejects_negative_iterations():
    with pytest.raises(ValueError):
        MonteCarloConfig(iterations=-1)


def test_monte_carlo_config_rejects_invalid_lower_percentile():
    with pytest.raises(ValueError):
        MonteCarloConfig(lower_percentile=-1.0)


def test_monte_carlo_config_rejects_invalid_upper_percentile():
    with pytest.raises(ValueError):
        MonteCarloConfig(upper_percentile=101.0)


def test_monte_carlo_config_rejects_reversed_percentiles():
    with pytest.raises(ValueError):
        MonteCarloConfig(
            lower_percentile=95.0,
            upper_percentile=5.0,
        )


def test_monte_carlo_config_rejects_equal_percentiles():
    with pytest.raises(ValueError):
        MonteCarloConfig(
            lower_percentile=50.0,
            upper_percentile=50.0,
        )


def test_monte_carlo_result_uncertainty():
    result = MonteCarloResult(
        simulation_id="MC-001",
        iterations=1000,
        mean=100.0,
        median=98.0,
        standard_deviation=10.0,
        lower_percentile=80.0,
        upper_percentile=120.0,
        unit="kg/h",
    )

    assert result.uncertainty == pytest.approx(20.0)


def test_monte_carlo_result_accepts_samples():
    result = MonteCarloResult(
        simulation_id="MC-002",
        iterations=3,
        mean=10.0,
        median=10.0,
        standard_deviation=1.0,
        lower_percentile=9.0,
        upper_percentile=11.0,
        samples=(9.0, 10.0, 11.0),
        unit="kg/h",
    )

    assert result.samples == (9.0, 10.0, 11.0)
    assert result.iterations == 3
