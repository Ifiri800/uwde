from __future__ import annotations

from .models import AcquisitionObservation


def validate_observations(
    observations: list[AcquisitionObservation],
) -> list[str]:
    errors: list[str] = []

    ids = [observation.id for observation in observations]

    if len(ids) != len(set(ids)):
        errors.append("duplicate acquisition observation IDs")

    for observation in observations:
        if observation.value is not None and observation.value < 0:
            errors.append(
                f"{observation.id}: negative observation value"
            )

    return errors
