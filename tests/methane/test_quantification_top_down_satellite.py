from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.top_down.satellite import (
    SatelliteObservation,
    validate_satellite_observation,
)


def make_observation(**overrides):
    values = {
        "observation_id": "SAT-001",
        "site_id": "SITE-001",
        "observed_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "concentration": 1850.0,
        "unit": "ppb",
        "satellite": "Sentinel-5P",
        "product": "methane",
    }
    values.update(overrides)
    return SatelliteObservation(**values)


def test_valid_satellite_observation():
    observation = make_observation()
    assert validate_satellite_observation(observation) == observation


def test_zero_concentration_is_valid():
    observation = make_observation(concentration=0.0)
    assert validate_satellite_observation(observation) == observation


def test_negative_concentration_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(concentration=-1.0)
        )


def test_missing_observation_id_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(observation_id="")
        )


def test_missing_site_id_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(site_id="")
        )


def test_missing_unit_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(unit="")
        )


def test_missing_satellite_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(satellite="")
        )


def test_missing_product_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(product="")
        )


def test_invalid_coordinates_are_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(latitude=91.0)
        )

    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(longitude=181.0)
        )


def test_uncertainty_is_supported():
    observation = make_observation(
        latitude=4.8156,
        longitude=7.0498,
        uncertainty=25.0,
    )

    result = validate_satellite_observation(observation)

    assert result.latitude == 4.8156
    assert result.longitude == 7.0498
    assert result.uncertainty == 25.0


def test_negative_uncertainty_is_rejected():
    with pytest.raises(ValueError):
        validate_satellite_observation(
            make_observation(uncertainty=-1.0)
        )
