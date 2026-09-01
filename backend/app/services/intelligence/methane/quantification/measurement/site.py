from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class SiteMeasurement:
    """
    Site-level methane measurement.
    """

    measurement_id: str
    site_id: str
    measured_at: datetime
    value: float
    unit: str
    method: str
    duration_minutes: float | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_site_measurement(
    measurement: SiteMeasurement,
) -> SiteMeasurement:
    """
    Validate a site-level methane measurement.
    """

    if not isinstance(measurement, SiteMeasurement):
        raise ValueError(
            "measurement must be a SiteMeasurement instance"
        )

    if not measurement.measurement_id.strip():
        raise ValueError("measurement_id is required")

    if not measurement.site_id.strip():
        raise ValueError("site_id is required")

    if measurement.value < 0:
        raise ValueError("value cannot be negative")

    if not measurement.unit.strip():
        raise ValueError("unit is required")

    if not measurement.method.strip():
        raise ValueError("method is required")

    if (
        measurement.duration_minutes is not None
        and measurement.duration_minutes < 0
    ):
        raise ValueError("duration_minutes cannot be negative")

    if (
        measurement.uncertainty is not None
        and measurement.uncertainty < 0
    ):
        raise ValueError("uncertainty cannot be negative")

    return measurement
