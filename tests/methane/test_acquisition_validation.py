from datetime import datetime, timezone

from backend.app.services.intelligence.methane.acquisition.models import (
    AcquisitionCategory,
    AcquisitionObservation,
)
from backend.app.services.intelligence.methane.acquisition.validation import (
    validate_observations,
)


def test_duplicate_ids_are_detected():
    timestamp = datetime.now(timezone.utc)

    observations = [
        AcquisitionObservation(
            id="same",
            category=AcquisitionCategory.LDAR,
            method="OGI",
            observed_at=timestamp,
        ),
        AcquisitionObservation(
            id="same",
            category=AcquisitionCategory.SATELLITE,
            method="satellite",
            observed_at=timestamp,
        ),
    ]

    errors = validate_observations(observations)

    assert "duplicate acquisition observation IDs" in errors


def test_valid_observations_have_no_errors():
    observation = AcquisitionObservation(
        id="valid",
        category=AcquisitionCategory.SENSOR,
        method="fixed_sensor",
        observed_at=datetime.now(timezone.utc),
        value=10.0,
    )

    assert validate_observations([observation]) == []
