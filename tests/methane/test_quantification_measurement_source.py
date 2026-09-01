from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.measurement.source import (
    SourceMeasurement,
    validate_source_measurement,
)


def test_valid_source_measurement():
    measurement = SourceMeasurement(
        measurement_id="MEAS-001",
        source_id="SRC-001",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=12.5,
        unit="kg/h",
        method="OGI",
    )

    assert validate_source_measurement(measurement) == measurement


def test_zero_value_is_valid():
    measurement = SourceMeasurement(
        measurement_id="MEAS-002",
        source_id="SRC-002",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=0.0,
        unit="kg/h",
        method="sensor",
    )

    assert validate_source_measurement(measurement) == measurement


def test_negative_value_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="MEAS-003",
        source_id="SRC-003",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=-1.0,
        unit="kg/h",
        method="sensor",
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)


def test_missing_measurement_id_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="",
        source_id="SRC-004",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="sensor",
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)


def test_missing_source_id_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="MEAS-005",
        source_id="",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="sensor",
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)


def test_missing_unit_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="MEAS-006",
        source_id="SRC-006",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="",
        method="sensor",
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)


def test_missing_method_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="MEAS-007",
        source_id="SRC-007",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="",
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)


def test_uncertainty_is_supported():
    measurement = SourceMeasurement(
        measurement_id="MEAS-008",
        source_id="SRC-008",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=10.0,
        unit="kg/h",
        method="sensor",
        instrument_id="INST-001",
        uncertainty=0.5,
    )

    result = validate_source_measurement(measurement)

    assert result.instrument_id == "INST-001"
    assert result.uncertainty == 0.5


def test_negative_uncertainty_is_rejected():
    measurement = SourceMeasurement(
        measurement_id="MEAS-009",
        source_id="SRC-009",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=10.0,
        unit="kg/h",
        method="sensor",
        uncertainty=-0.5,
    )

    with pytest.raises(ValueError):
        validate_source_measurement(measurement)
