from __future__ import annotations

from datetime import datetime

from .models import AcquisitionCategory, AcquisitionObservation


def create_remote_sensing_observation(
    observation_id: str,
    category: AcquisitionCategory,
    method: str,
    observed_at: datetime,
    *,
    value: float | None = None,
    unit: str | None = None,
    facility_id: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    source_reference: str | None = None,
    metadata: dict | None = None,
) -> AcquisitionObservation:
    allowed = {
        AcquisitionCategory.REMOTE_SENSING,
        AcquisitionCategory.SATELLITE,
        AcquisitionCategory.AIRCRAFT,
        AcquisitionCategory.DRONE,
        AcquisitionCategory.ATMOSPHERIC,
        AcquisitionCategory.METEOROLOGY,
        AcquisitionCategory.SPATIAL,
    }

    if category not in allowed:
        raise ValueError(
            "category is not a supported remote-sensing category"
        )

    return AcquisitionObservation(
        id=observation_id,
        category=category,
        method=method,
        observed_at=observed_at,
        value=value,
        unit=unit,
        facility_id=facility_id,
        latitude=latitude,
        longitude=longitude,
        source_reference=source_reference,
        metadata=metadata or {},
    )
