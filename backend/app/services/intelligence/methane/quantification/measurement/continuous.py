from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class ContinuousMeasurement:
    """
    Continuous methane measurement observation.
    """

    measurement_id: str
    site_id: str
    observed_at: datetime
    value: float
    unit: str
    interval_seconds: float
    instrument_id: str | None = None
    quality_flag: str | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_continuous_measurement(
    measurement: ContinuousMeasurement,
) -> ContinuousMeasurement:
    """
    Validate a continuous methane measurement.
    """

    if not isinstance(measurement, ContinuousMeasurement):
        raise ValueError(
            "measurement must be a ContinuousMeasurement instance"
        )

    if not measurement.measurement_id.strip():
        raise ValueError("measurement_id is required")

    if not measurement.site_id.strip():
        raise ValueError("site_id is required")

    if measurement.value < 0:
        raise ValueError("value cannot be negative")

    if not measurement.unit.strip():
        raise ValueError("unit is required")

    if measurement.interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than zero")

    if (
        measurement.uncertainty is not None
        and measurement.uncertainty < 0
    ):
        raise ValueError("uncertainty cannot be negative")

    return measurement
