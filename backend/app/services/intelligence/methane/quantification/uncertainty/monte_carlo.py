from __future__ import annotations

from dataclasses import dataclass
from random import Random
from statistics import mean as statistics_mean
from statistics import median
from typing import Sequence


@dataclass(frozen=True)
class MonteCarloResult:
    """Summary of a Monte Carlo uncertainty simulation."""

    samples: tuple[float, ...]
    mean: float
    median: float
    standard_deviation: float
    lower_percentile: float
    upper_percentile: float

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("samples cannot be empty")

        if self.standard_deviation < 0:
            raise ValueError(
                "standard_deviation cannot be negative"
            )

        if self.lower_percentile > self.upper_percentile:
            raise ValueError(
                "lower_percentile cannot exceed upper_percentile"
            )


@dataclass(frozen=True)
class MonteCarloSimulation:
    """Configuration for a Monte Carlo uncertainty simulation."""

    iterations: int = 10_000
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.iterations <= 0:
            raise ValueError(
                "iterations must be greater than zero"
            )

        if self.seed is not None and self.seed < 0:
            raise ValueError(
                "seed cannot be negative"
            )


def _sample_standard_deviation(
    samples: Sequence[float],
) -> float:
    """Calculate the sample standard deviation."""

    if len(samples) <= 1:
        return 0.0

    sample_mean = statistics_mean(samples)

    variance = sum(
        (sample - sample_mean) ** 2
        for sample in samples
    ) / (len(samples) - 1)

    return variance**0.5


def _percentile(
    samples: Sequence[float],
    percentile: float,
) -> float:
    """Calculate a percentile using linear interpolation."""

    if not samples:
        raise ValueError("samples cannot be empty")

    if not 0.0 <= percentile <= 100.0:
        raise ValueError(
            "percentile must be between 0 and 100"
        )

    ordered = sorted(samples)

    if len(ordered) == 1:
        return float(ordered[0])

    position = (
        percentile / 100.0
    ) * (len(ordered) - 1)

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(ordered) - 1,
    )

    fraction = position - lower_index

    lower_value = ordered[lower_index]
    upper_value = ordered[upper_index]

    return (
        lower_value
        + (upper_value - lower_value) * fraction
    )


def simulate_monte_carlo(
    *,
    simulation: MonteCarloSimulation,
    mean: float,
    standard_deviation: float,
    confidence_level: float = 0.95,
) -> MonteCarloResult:
    """
    Run a normal-distribution Monte Carlo uncertainty simulation.
    """

    if not isinstance(
        simulation,
        MonteCarloSimulation,
    ):
        raise ValueError(
            "simulation must be a MonteCarloSimulation instance"
        )

    if standard_deviation < 0:
        raise ValueError(
            "standard_deviation cannot be negative"
        )

    if not 0.0 < confidence_level < 1.0:
        raise ValueError(
            "confidence_level must be between 0 and 1"
        )

    random = Random(simulation.seed)

    samples = tuple(
        random.gauss(
            mean,
            standard_deviation,
        )
        for _ in range(simulation.iterations)
    )

    lower_percentile = (
        (1.0 - confidence_level)
        / 2.0
        * 100.0
    )

    upper_percentile = (
        1.0
        - (1.0 - confidence_level) / 2.0
    ) * 100.0

    return MonteCarloResult(
        samples=samples,
        mean=statistics_mean(samples),
        median=median(samples),
        standard_deviation=_sample_standard_deviation(
            samples
        ),
        lower_percentile=_percentile(
            samples,
            lower_percentile,
        ),
        upper_percentile=_percentile(
            samples,
            upper_percentile,
        ),
    )
