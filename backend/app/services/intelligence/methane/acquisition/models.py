from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AcquisitionCategory(str, Enum):
    INVENTORY = "inventory"
    DIRECT_MEASUREMENT = "direct_measurement"
    LDAR = "ldar"
    OGI = "ogi"
    SENSOR = "sensor"
    MOBILE = "mobile"
    SITE_SURVEY = "site_survey"
    CONTINUOUS = "continuous"
    REMOTE_SENSING = "remote_sensing"
    SATELLITE = "satellite"
    AIRCRAFT = "aircraft"
    DRONE = "drone"
    ATMOSPHERIC = "atmospheric"
    METEOROLOGY = "meteorology"
    SPATIAL = "spatial"


@dataclass(frozen=True)
class AcquisitionObservation:
    id: str
    category: AcquisitionCategory
    method: str
    observed_at: datetime
    value: float | None = None
    unit: str | None = None
    component_id: str | None = None
    facility_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")

        if not self.method.strip():
            raise ValueError("method is required")

        if not isinstance(self.observed_at, datetime):
            raise TypeError("observed_at must be a datetime")

        if self.value is not None:
            if self.value < 0:
                raise ValueError("value cannot be negative")

        if self.latitude is not None:
            if not -90.0 <= self.latitude <= 90.0:
                raise ValueError("latitude must be between -90 and 90")

        if self.longitude is not None:
            if not -180.0 <= self.longitude <= 180.0:
                raise ValueError("longitude must be between -180 and 180")


@dataclass
class AcquisitionRegistry:
    observations: dict[str, AcquisitionObservation] = field(
        default_factory=dict
    )

    def add(self, observation: AcquisitionObservation) -> None:
        if observation.id in self.observations:
            raise ValueError(
                f"duplicate acquisition observation: {observation.id}"
            )

        self.observations[observation.id] = observation

    def get(self, observation_id: str) -> AcquisitionObservation | None:
        return self.observations.get(observation_id)

    def by_category(
        self,
        category: AcquisitionCategory,
    ) -> list[AcquisitionObservation]:
        return [
            observation
            for observation in self.observations.values()
            if observation.category == category
        ]
