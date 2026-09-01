from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.top_down.plume import (
    PlumeGeometry,
    PlumeObservation,
    PlumeQuantification,
    validate_plume_observation,
    validate_plume_quantification,
)
from backend.app.services.intelligence.methane.quantification.top_down.spatial import (
    BoundingBox,
    SpatialPoint,
)


def make_geometry() -> PlumeGeometry:
    return PlumeGeometry(
        centroid=SpatialPoint(
            latitude=4.8156,
            longitude=7.0498,
        ),
        bounds=BoundingBox(
            min_latitude=4.80,
            min_longitude=7.03,
            max_latitude=4.83,
            max_longitude=7.07,
        ),
        area_km2=10.0,
        length_km=5.0,
        width_km=2.0,
    )


def make_observation() -> PlumeObservation:
    return PlumeObservation(
        plume_id="PLUME-001",
        site_id="SITE-001",
        observed_at=datetime(
            2026,
            1,
            15,
            tzinfo=timezone.utc,
        ),
        geometry=make_geometry(),
        methane_enhancement=185.0,
        detection_confidence=0.95,
        source="Sentinel-5P",
    )


def test_plume_geometry():
    geometry = make_geometry()

    assert geometry.centroid.latitude == 4.8156
    assert geometry.centroid.longitude == 7.0498
    assert geometry.area_km2 == 10.0
    assert geometry.length_km == 5.0
    assert geometry.width_km == 2.0


def test_plume_geometry_rejects_negative_area():
    with pytest.raises(ValueError):
        PlumeGeometry(
            centroid=SpatialPoint(4.8, 7.0),
            bounds=BoundingBox(4.7, 6.9, 4.9, 7.1),
            area_km2=-1.0,
            length_km=5.0,
            width_km=2.0,
        )


def test_plume_observation():
    observation = make_observation()

    assert observation.plume_id == "PLUME-001"
    assert observation.site_id == "SITE-001"
    assert observation.methane_enhancement == 185.0
    assert observation.enhancement_unit == "ppb"
    assert observation.detection_confidence == 0.95
    assert observation.source == "Sentinel-5P"


def test_plume_observation_validation():
    observation = make_observation()

    assert validate_plume_observation(observation) is observation


def test_plume_observation_requires_id():
    observation = make_observation()

    invalid = PlumeObservation(
        plume_id="",
        site_id=observation.site_id,
        observed_at=observation.observed_at,
        geometry=observation.geometry,
        methane_enhancement=observation.methane_enhancement,
    )

    with pytest.raises(ValueError, match="plume_id is required"):
        validate_plume_observation(invalid)


def test_plume_observation_requires_site():
    observation = make_observation()

    invalid = PlumeObservation(
        plume_id=observation.plume_id,
        site_id="",
        observed_at=observation.observed_at,
        geometry=observation.geometry,
        methane_enhancement=observation.methane_enhancement,
    )

    with pytest.raises(ValueError, match="site_id is required"):
        validate_plume_observation(invalid)


def test_plume_observation_requires_timezone():
    observation = make_observation()

    invalid = PlumeObservation(
        plume_id=observation.plume_id,
        site_id=observation.site_id,
        observed_at=datetime(2026, 1, 15),
        geometry=observation.geometry,
        methane_enhancement=observation.methane_enhancement,
    )

    with pytest.raises(
        ValueError,
        match="observed_at must be timezone-aware",
    ):
        validate_plume_observation(invalid)


def test_negative_methane_enhancement_rejected():
    observation = make_observation()

    invalid = PlumeObservation(
        plume_id=observation.plume_id,
        site_id=observation.site_id,
        observed_at=observation.observed_at,
        geometry=observation.geometry,
        methane_enhancement=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="methane_enhancement cannot be negative",
    ):
        validate_plume_observation(invalid)


def test_detection_confidence_must_be_between_zero_and_one():
    observation = make_observation()

    invalid = PlumeObservation(
        plume_id=observation.plume_id,
        site_id=observation.site_id,
        observed_at=observation.observed_at,
        geometry=observation.geometry,
        methane_enhancement=100.0,
        detection_confidence=1.1,
    )

    with pytest.raises(
        ValueError,
        match="detection_confidence must be between 0 and 1",
    ):
        validate_plume_observation(invalid)


def test_plume_quantification():
    quantification = PlumeQuantification(
        plume_id="PLUME-001",
        emission_rate=125.0,
        uncertainty=20.0,
        uncertainty_unit="kg/h",
        method="integrated_plume",
    )

    assert quantification.plume_id == "PLUME-001"
    assert quantification.emission_rate == 125.0
    assert quantification.emission_rate_unit == "kg/h"
    assert quantification.uncertainty == 20.0
    assert quantification.uncertainty_unit == "kg/h"
    assert quantification.method == "integrated_plume"


def test_plume_quantification_validation():
    quantification = PlumeQuantification(
        plume_id="PLUME-001",
        emission_rate=125.0,
    )

    assert validate_plume_quantification(quantification) is quantification


def test_negative_emission_rate_rejected():
    quantification = PlumeQuantification(
        plume_id="PLUME-001",
        emission_rate=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="emission_rate cannot be negative",
    ):
        validate_plume_quantification(quantification)


def test_negative_uncertainty_rejected():
    quantification = PlumeQuantification(
        plume_id="PLUME-001",
        emission_rate=100.0,
        uncertainty=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="uncertainty cannot be negative",
    ):
        validate_plume_quantification(quantification)


def test_quantification_requires_plume_id():
    quantification = PlumeQuantification(
        plume_id="",
        emission_rate=100.0,
    )

    with pytest.raises(
        ValueError,
        match="plume_id is required",
    ):
        validate_plume_quantification(quantification)


def test_zero_emission_rate_is_valid():
    quantification = PlumeQuantification(
        plume_id="PLUME-002",
        emission_rate=0.0,
    )

    assert validate_plume_quantification(quantification) is quantification
