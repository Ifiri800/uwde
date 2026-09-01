from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class IngestionSourceType(str, Enum):
    API = "api"
    FILE = "file"
    SENSOR = "sensor"
    SATELLITE = "satellite"
    GIS = "gis"
    MANUAL = "manual"
    DATABASE = "database"


class ObservationStatus(str, Enum):
    RAW = "raw"
    STANDARDIZED = "standardized"
    REJECTED = "rejected"


@dataclass(frozen=True)
class IngestionMetadata:
    source_id: str
    source_type: IngestionSourceType
    source_name: str
    acquired_at: datetime
    provider: str | None = None
    dataset_id: str | None = None
    version: str | None = None
    checksum: str | None = None
    license: str | None = None
    quality_notes: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")

        if not self.source_name.strip():
            raise ValueError("source_name is required")

        if not isinstance(self.acquired_at, datetime):
            raise TypeError("acquired_at must be a datetime")


@dataclass(frozen=True)
class GeospatialReference:
    latitude: float | None = None
    longitude: float | None = None
    crs: str | None = None
    geometry: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.latitude is not None and not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if self.longitude is not None and not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")


@dataclass(frozen=True)
class TemporalReference:
    observed_at: datetime
    timezone: str | None = None
    duration_seconds: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be a datetime")

        if (
            self.duration_seconds is not None
            and self.duration_seconds < 0
        ):
            raise ValueError("duration_seconds cannot be negative")


@dataclass(frozen=True)
class UnitValue:
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError("value must be numeric")

        if not self.unit.strip():
            raise ValueError("unit is required")


@dataclass(frozen=True)
class IngestionRecord:
    record_id: str
    data: Mapping[str, Any]
    metadata: IngestionMetadata
    status: ObservationStatus = ObservationStatus.RAW
    temporal: TemporalReference | None = None
    geospatial: GeospatialReference | None = None
    schema_version: str = "1.0"
    record_version: int = 1

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id is required")

        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")

        if self.record_version < 1:
            raise ValueError("record_version must be >= 1")


@dataclass(frozen=True)
class IngestionBatch:
    batch_id: str
    records: tuple[IngestionRecord, ...]
    created_at: datetime
    source_type: IngestionSourceType

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id is required")

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
