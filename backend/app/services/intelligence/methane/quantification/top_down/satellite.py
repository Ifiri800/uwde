from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class SatelliteObservation:
    """
    Satellite-derived methane observation.
    """

    observation_id: str
    site_id: str
    observed_at: datetime
    concentration: float
    unit: str
    satellite: str
    product: str
    latitude: float | None = None
    longitude: float | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_satellite_observation(
    observation: SatelliteObservation,
) -> SatelliteObservation:
    """
    Validate a satellite-derived methane observation.
    """

    if not isinstance(observation, SatelliteObservation):
        raise ValueError(
            "observation must be a SatelliteObservation instance"
        )

    if not observation.observation_id.strip():
        raise ValueError("observation_id is required")

    if not observation.site_id.strip():
        raise ValueError("site_id is required")

    if observation.concentration < 0:
        raise ValueError("concentration cannot be negative")

    if not observation.unit.strip():
        raise ValueError("unit is required")

    if not observation.satellite.strip():
        raise ValueError("satellite is required")

    if not observation.product.strip():
        raise ValueError("product is required")

    if observation.latitude is not None:
        if not -90.0 <= observation.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

    if observation.longitude is not None:
        if not -180.0 <= observation.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

    if (
        observation.uncertainty is not None
        and observation.uncertainty < 0
    ):
        raise ValueError("uncertainty cannot be negative")

    return observation
