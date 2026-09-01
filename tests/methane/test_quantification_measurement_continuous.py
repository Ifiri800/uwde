from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.measurement.continuous import (
    ContinuousMeasurement,
    validate_continuous_measurement,
)


def make_measurement(**overrides):
    values = {
        "measurement_id": "CONT-001",
        "site_id": "SITE-001",
        "observed_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "value": 10.0,
        "unit": "kg/h",
        "interval_seconds": 60.0,
    }
    values.update(overrides)
    return ContinuousMeasurement(**values)


def test_valid_continuous_measurement():
    measurement = make_measurement()
    assert validate_continuous_measurement(measurement) == measurement


def test_zero_value_is_valid():
    measurement = make_measurement(value=0.0)
    assert validate_continuous_measurement(measurement) == measurement


def test_negative_value_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(make_measurement(value=-1.0))


def test_missing_measurement_id_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(measurement_id="")
        )


def test_missing_site_id_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(site_id="")
        )


def test_missing_unit_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(unit="")
        )


def test_zero_interval_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(interval_seconds=0.0)
        )


def test_negative_interval_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(interval_seconds=-1.0)
        )


def test_uncertainty_is_supported():
    measurement = make_measurement(
        uncertainty=0.5,
        instrument_id="INST-001",
        quality_flag="good",
    )

    result = validate_continuous_measurement(measurement)

    assert result.uncertainty == 0.5
    assert result.instrument_id == "INST-001"
    assert result.quality_flag == "good"


def test_negative_uncertainty_is_rejected():
    with pytest.raises(ValueError):
        validate_continuous_measurement(
            make_measurement(uncertainty=-0.5)
        )
