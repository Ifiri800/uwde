from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketDriver:
    name: str
    description: str
    strength: float = 0.0
    direction: str = "positive"
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DriversAnalysisResult:
    drivers: tuple[MarketDriver, ...]
    overall_strength: float


def analyze_drivers(
    drivers: list[MarketDriver],
) -> DriversAnalysisResult:

    for driver in drivers:
        if not driver.name.strip():
            raise ValueError("driver name is required")

        if not 0.0 <= driver.strength <= 1.0:
            raise ValueError(
                "driver strength must be between 0.0 and 1.0"
            )

    strength = (
        sum(driver.strength for driver in drivers)
        / len(drivers)
        if drivers
        else 0.0
    )

    return DriversAnalysisResult(
        drivers=tuple(drivers),
        overall_strength=round(strength, 6),
    )
