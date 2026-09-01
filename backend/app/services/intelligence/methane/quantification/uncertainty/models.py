from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class UncertaintySource(str, Enum):
    """Supported sources of methane emissions uncertainty."""

    ACTIVITY_DATA = "activity_data"
    EMISSION_FACTOR = "emission_factor"
    INSTRUMENT = "instrument"
    MEASUREMENT = "measurement"
    MODEL = "model"
    REMOTE_SENSING = "remote_sensing"


class DistributionType(str, Enum):
    """Probability distributions supported by uncertainty analysis."""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"


@dataclass(frozen=True)
class UncertaintyComponent:
    """
    Individual uncertainty contribution associated with an estimate.
    """

    component_id: str
    source: UncertaintySource
    value: float
    unit: str

    distribution: DistributionType = DistributionType.NORMAL

    standard_deviation: float | None = None
    lower_bound: float | None = None
    upper_bound: float | None = None

    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UncertaintyAssessment:
    """
    Consolidated uncertainty assessment for an emission estimate.
    """

    assessment_id: str
    estimate_id: str

    components: tuple[UncertaintyComponent, ...] = ()

    combined_uncertainty: float | None = None
    uncertainty_unit: str | None = None

    confidence_level: float = 0.95

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def component_count(self) -> int:
        return len(self.components)

    @property
    def has_uncertainty(self) -> bool:
        return self.combined_uncertainty is not None


@dataclass(frozen=True)
class MonteCarloConfig:
    """
    Configuration for Monte Carlo uncertainty simulation.
    """

    iterations: int = 10_000
    random_seed: int | None = None

    lower_percentile: float = 5.0
    upper_percentile: float = 95.0

    def __post_init__(self) -> None:
        if self.iterations <= 0:
            raise ValueError("iterations must be greater than zero")

        if not 0.0 <= self.lower_percentile <= 100.0:
            raise ValueError(
                "lower_percentile must be between 0 and 100"
            )

        if not 0.0 <= self.upper_percentile <= 100.0:
            raise ValueError(
                "upper_percentile must be between 0 and 100"
            )

        if self.lower_percentile >= self.upper_percentile:
            raise ValueError(
                "lower_percentile must be less than upper_percentile"
            )


@dataclass(frozen=True)
class MonteCarloResult:
    """
    Statistical result produced by a Monte Carlo simulation.
    """

    simulation_id: str

    iterations: int

    mean: float
    median: float
    standard_deviation: float

    lower_percentile: float
    upper_percentile: float

    samples: tuple[float, ...] = ()

    unit: str = ""

    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def uncertainty(self) -> float:
        """
        Return the half-width of the simulated uncertainty interval.
        """

        return (
            self.upper_percentile
            - self.lower_percentile
        ) / 2.0
