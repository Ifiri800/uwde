from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from ..quantification.models import (
    EmissionEstimate,
    QuantificationLevel,
    QuantificationMethod,
)


class ReconciliationMethod(str, Enum):
    WEIGHTED = "weighted"
    SIMPLE_MEAN = "simple_mean"


class ReconciliationStatus(str, Enum):
    RECONCILED = "reconciled"
    PARTIAL = "partial"
    REJECTED = "rejected"


@dataclass(frozen=True)
class ReconciliationInput:
    """Normalized Layer 9 input derived from a Layer 7 estimate."""

    input_id: str
    estimate: EmissionEstimate

    weight: float = 1.0
    uncertainty: float | None = None
    quality_score: float = 1.0

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def estimate_id(self) -> str:
        return self.estimate.estimate_id

    @property
    def method(self) -> QuantificationMethod:
        return self.estimate.method

    @property
    def level(self) -> QuantificationLevel:
        return self.estimate.level

    @property
    def value(self) -> float:
        return self.estimate.value

    @property
    def unit(self) -> str:
        return self.estimate.unit

    def __post_init__(self) -> None:
        if not self.input_id.strip():
            raise ValueError("input_id is required")

        if self.value < 0:
            raise ValueError(
                "estimate value cannot be negative"
            )

        if not float("-inf") < self.value < float("inf"):
            raise ValueError(
                "estimate value must be finite"
            )

        if self.weight < 0:
            raise ValueError(
                "weight cannot be negative"
            )

        if not float("-inf") < self.weight < float("inf"):
            raise ValueError(
                "weight must be finite"
            )

        if self.uncertainty is not None:
            if self.uncertainty < 0:
                raise ValueError(
                    "uncertainty cannot be negative"
                )

            if not float("-inf") < self.uncertainty < float("inf"):
                raise ValueError(
                    "uncertainty must be finite"
                )

        if not 0.0 <= self.quality_score <= 1.0:
            raise ValueError(
                "quality_score must be between 0 and 1"
            )


@dataclass(frozen=True)
class DiscrepancyResult:
    """Comparison of one estimate against the fused estimate."""

    input_id: str
    method: QuantificationMethod

    estimate_value: float
    fused_value: float

    absolute_difference: float
    relative_difference: float

    percent_difference: float | None = None
    within_tolerance: bool | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def agrees(self) -> bool:
        return self.absolute_difference == 0.0


@dataclass(frozen=True)
class FusionResult:
    """Result of combining multiple Layer 9 inputs."""

    value: float
    unit: str
    method: ReconciliationMethod

    inputs: tuple[ReconciliationInput, ...]

    total_weight: float

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def input_count(self) -> int:
        return len(self.inputs)


@dataclass(frozen=True)
class ConfidenceAssessment:
    """Confidence assigned to a reconciled estimate."""

    score: float
    level: str

    uncertainty: float | None = None

    rationale: tuple[str, ...] = ()

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0 and 1"
            )

        if (
            self.uncertainty is not None
            and self.uncertainty < 0
        ):
            raise ValueError(
                "uncertainty cannot be negative"
            )


@dataclass(frozen=True)
class ReconciledEstimate:
    """Final Layer 9 reconciled methane estimate."""

    reconciliation_id: str

    value: float
    unit: str

    status: ReconciliationStatus

    inputs: tuple[ReconciliationInput, ...] = ()

    discrepancies: tuple[DiscrepancyResult, ...] = ()

    level: QuantificationLevel | None = None

    uncertainty: float | None = None
    confidence_level: float | None = None

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def input_count(self) -> int:
        return len(self.inputs)

    @property
    def input_estimate_ids(self) -> tuple[str, ...]:
        return tuple(
            item.estimate_id
            for item in self.inputs
        )

    @property
    def discrepancy_count(self) -> int:
        return len(self.discrepancies)

    @property
    def has_uncertainty(self) -> bool:
        return self.uncertainty is not None

    @property
    def has_confidence(self) -> bool:
        return self.confidence_level is not None

    @property
    def confidence(self) -> float | None:
        """Backward-compatible access to the confidence score."""
        return self.confidence_level


@dataclass(frozen=True)
class ReconciliationResult:
    """Complete output of the Layer 9 reconciliation engine."""

    estimate: ReconciledEstimate

    fusion: FusionResult | None = None

    discrepancies: tuple[DiscrepancyResult, ...] = ()

    confidence: ConfidenceAssessment | None = None

    warnings: tuple[str, ...] = ()

    @property
    def value(self) -> float:
        return self.estimate.value

    @property
    def input_count(self) -> int:
        return self.estimate.input_count

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)
