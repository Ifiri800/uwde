from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.measurement.site import (
    SiteMeasurement,
    validate_site_measurement,
)


def test_valid_site_measurement():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-001",
        site_id="SITE-001",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=25.0,
        unit="kg/h",
        method="site survey",
    )

    assert validate_site_measurement(measurement) == measurement


def test_zero_value_is_valid():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-002",
        site_id="SITE-002",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=0.0,
        unit="kg/h",
        method="site survey",
    )

    assert validate_site_measurement(measurement) == measurement


def test_negative_value_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-003",
        site_id="SITE-003",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=-1.0,
        unit="kg/h",
        method="site survey",
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_missing_measurement_id_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="",
        site_id="SITE-004",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="site survey",
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_missing_site_id_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-005",
        site_id="",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="site survey",
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_missing_unit_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-006",
        site_id="SITE-006",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="",
        method="site survey",
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_missing_method_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-007",
        site_id="SITE-007",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=1.0,
        unit="kg/h",
        method="",
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_duration_is_supported_and_validated():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-008",
        site_id="SITE-008",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=10.0,
        unit="kg/h",
        method="site survey",
        duration_minutes=60.0,
    )

    result = validate_site_measurement(measurement)

    assert result.duration_minutes == 60.0


def test_negative_duration_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-009",
        site_id="SITE-009",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=10.0,
        unit="kg/h",
        method="site survey",
        duration_minutes=-5.0,
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)


def test_negative_uncertainty_is_rejected():
    measurement = SiteMeasurement(
        measurement_id="SITE-MEAS-010",
        site_id="SITE-010",
        measured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        value=10.0,
        unit="kg/h",
        method="site survey",
        uncertainty=-0.5,
    )

    with pytest.raises(ValueError):
        validate_site_measurement(measurement)
