from datetime import datetime, timezone

from backend.app.services.intelligence.methane.acquisition.models import (
    AcquisitionCategory,
    AcquisitionObservation,
)


def test_observation_creation():
    observation = AcquisitionObservation(
        id="obs-1",
        category=AcquisitionCategory.DIRECT_MEASUREMENT,
        method="sensor",
        observed_at=datetime.now(timezone.utc),
        value=12.5,
        unit="kg/h",
        component_id="component-1",
    )

    assert observation.id == "obs-1"
    assert observation.value == 12.5


def test_coordinates_are_validated():
    try:
        AcquisitionObservation(
            id="obs-1",
            category=AcquisitionCategory.SATELLITE,
            method="satellite",
            observed_at=datetime.now(timezone.utc),
            latitude=100,
        )
    except ValueError:
        return

    raise AssertionError("invalid latitude was accepted")


def test_categories_are_distinct():
    assert AcquisitionCategory.LDAR != AcquisitionCategory.SATELLITE
