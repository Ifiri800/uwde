from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping

from .spatial import BoundingBox, SpatialPoint


@dataclass(frozen=True)
class PlumeGeometry:
    """
    Spatial characteristics of a detected methane plume.
    """

    centroid: SpatialPoint
    bounds: BoundingBox
    area_km2: float
    length_km: float
    width_km: float

    def __post_init__(self) -> None:
        if not isinstance(self.centroid, SpatialPoint):
            raise ValueError("centroid must be a SpatialPoint")

        if not isinstance(self.bounds, BoundingBox):
            raise ValueError("bounds must be a BoundingBox")

        if self.area_km2 < 0:
            raise ValueError("area_km2 cannot be negative")

        if self.length_km < 0:
            raise ValueError("length_km cannot be negative")

        if self.width_km < 0:
            raise ValueError("width_km cannot be negative")


@dataclass(frozen=True)
class PlumeObservation:
    """
    Detected methane plume associated with a top-down observation.
    """

    plume_id: str
    site_id: str
    observed_at: datetime
    geometry: PlumeGeometry

    methane_enhancement: float
    enhancement_unit: str = "ppb"

    detection_confidence: float = 0.0

    source: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlumeQuantification:
    """
    Quantified methane emission associated with a detected plume.
    """

    plume_id: str
    emission_rate: float
    emission_rate_unit: str = "kg/h"

    uncertainty: float | None = None
    uncertainty_unit: str | None = None

    method: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_plume_observation(
    observation: PlumeObservation,
) -> PlumeObservation:
    """
    Validate a detected methane plume observation.
    """

    if not isinstance(observation, PlumeObservation):
        raise ValueError(
            "observation must be a PlumeObservation instance"
        )

    if not observation.plume_id.strip():
        raise ValueError("plume_id is required")

    if not observation.site_id.strip():
        raise ValueError("site_id is required")

    if observation.observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")

    if observation.methane_enhancement < 0:
        raise ValueError(
            "methane_enhancement cannot be negative"
        )

    if not observation.enhancement_unit.strip():
        raise ValueError("enhancement_unit is required")

    if not 0.0 <= observation.detection_confidence <= 1.0:
        raise ValueError(
            "detection_confidence must be between 0 and 1"
        )

    if observation.source is not None and not observation.source.strip():
        raise ValueError("source cannot be empty")

    if not isinstance(observation.metadata, Mapping):
        raise ValueError("metadata must be a mapping")

    return observation


def validate_plume_quantification(
    quantification: PlumeQuantification,
) -> PlumeQuantification:
    """
    Validate a quantified methane plume emission.
    """

    if not isinstance(quantification, PlumeQuantification):
        raise ValueError(
            "quantification must be a PlumeQuantification instance"
        )

    if not quantification.plume_id.strip():
        raise ValueError("plume_id is required")

    if quantification.emission_rate < 0:
        raise ValueError(
            "emission_rate cannot be negative"
        )

    if not quantification.emission_rate_unit.strip():
        raise ValueError(
            "emission_rate_unit is required"
        )

    if (
        quantification.uncertainty is not None
        and quantification.uncertainty < 0
    ):
        raise ValueError(
            "uncertainty cannot be negative"
        )

    if (
        quantification.uncertainty is not None
        and quantification.uncertainty_unit is not None
        and not quantification.uncertainty_unit.strip()
    ):
        raise ValueError(
            "uncertainty_unit cannot be empty"
        )

    if quantification.method is not None and not quantification.method.strip():
        raise ValueError("method cannot be empty")

    if not isinstance(quantification.metadata, Mapping):
        raise ValueError("metadata must be a mapping")

    return quantification
