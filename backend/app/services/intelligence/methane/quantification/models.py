from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class QuantificationMethod(str, Enum):
    BOTTOM_UP = "bottom_up"
    MEASUREMENT = "measurement"
    TOP_DOWN = "top_down"


class QuantificationLevel(str, Enum):
    SOURCE = "source"
    EQUIPMENT = "equipment"
    FACILITY = "facility"
    SITE = "site"
    ASSET = "asset"
    FIELD = "field"
    CORPORATE = "corporate"


class EstimateStatus(str, Enum):
    ESTIMATED = "estimated"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class QuantificationInput:
    """
    Input data supplied to an emissions quantification method.
    """

    input_id: str
    method: QuantificationMethod
    level: QuantificationLevel
    value: float
    unit: str
    source_id: str | None = None
    record_id: str | None = None
    timestamp: datetime | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class EmissionEstimate:
    """
    Calculated methane emission estimate.
    """

    estimate_id: str
    method: QuantificationMethod
    level: QuantificationLevel
    value: float
    unit: str
    status: EstimateStatus = EstimateStatus.ESTIMATED
    source_id: str | None = None
    record_id: str | None = None
    timestamp: datetime | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def has_uncertainty(self) -> bool:
        return self.uncertainty is not None


@dataclass(frozen=True)
class QuantificationResult:
    """
    Result produced by a quantification operation.
    """

    estimate: EmissionEstimate
    inputs: tuple[QuantificationInput, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def input_count(self) -> int:
        return len(self.inputs)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def value(self) -> float:
        return self.estimate.value


@dataclass(frozen=True)
class EmissionFactor:
    """
    Emission factor used by bottom-up quantification.
    """

    factor_id: str
    value: float
    unit: str
    source: str
    methodology: str | None = None
    tier: str | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ActivityData:
    """
    Activity data used in bottom-up quantification.
    """

    activity_id: str
    value: float
    unit: str
    activity_type: str
    source_id: str | None = None
    timestamp: datetime | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class Measurement:
    """
    Direct or continuous methane measurement.
    """

    measurement_id: str
    value: float
    unit: str
    measurement_type: str
    instrument_id: str | None = None
    source_id: str | None = None
    timestamp: datetime | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class RemoteObservation:
    """
    Top-down remote or atmospheric observation.
    """

    observation_id: str
    value: float
    unit: str
    observation_type: str
    source_id: str | None = None
    timestamp: datetime | None = None
    latitude: float | None = None
    longitude: float | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )
