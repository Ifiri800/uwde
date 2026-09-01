from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class SourceMeasurement:
    """
    Direct methane measurement at an emission source.
    """

    measurement_id: str
    source_id: str
    measured_at: datetime
    value: float
    unit: str
    method: str
    instrument_id: str | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_source_measurement(
    measurement: SourceMeasurement,
) -> SourceMeasurement:
    """
    Validate a source-level methane measurement.
    """

    if not isinstance(measurement, SourceMeasurement):
        raise ValueError(
            "measurement must be a SourceMeasurement instance"
        )

    if not measurement.measurement_id.strip():
        raise ValueError("measurement_id is required")

    if not measurement.source_id.strip():
        raise ValueError("source_id is required")

    if measurement.value < 0:
        raise ValueError("value cannot be negative")

    if not measurement.unit.strip():
        raise ValueError("unit is required")

    if not measurement.method.strip():
        raise ValueError("method is required")

    if measurement.uncertainty is not None and measurement.uncertainty < 0:
        raise ValueError("uncertainty cannot be negative")

    return measurement
