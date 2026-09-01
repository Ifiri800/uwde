from __future__ import annotations

from datetime import datetime

from .models import AcquisitionCategory, AcquisitionObservation


def create_direct_measurement(
    observation_id: str,
    method: str,
    observed_at: datetime,
    *,
    value: float | None = None,
    unit: str | None = None,
    component_id: str | None = None,
    facility_id: str | None = None,
    metadata: dict | None = None,
) -> AcquisitionObservation:
    return AcquisitionObservation(
        id=observation_id,
        category=AcquisitionCategory.DIRECT_MEASUREMENT,
        method=method,
        observed_at=observed_at,
        value=value,
        unit=unit,
        component_id=component_id,
        facility_id=facility_id,
        metadata=metadata or {},
    )
