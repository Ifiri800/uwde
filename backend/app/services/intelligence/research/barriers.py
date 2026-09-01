from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketBarrier:
    name: str
    description: str
    severity: float = 0.0
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class BarriersAnalysisResult:
    barriers: tuple[MarketBarrier, ...]
    overall_severity: float


def analyze_barriers(
    barriers: list[MarketBarrier],
) -> BarriersAnalysisResult:

    for barrier in barriers:
        if not barrier.name.strip():
            raise ValueError("barrier name is required")

        if not 0.0 <= barrier.severity <= 1.0:
            raise ValueError(
                "barrier severity must be between 0.0 and 1.0"
            )

    severity = (
        sum(barrier.severity for barrier in barriers)
        / len(barriers)
        if barriers
        else 0.0
    )

    return BarriersAnalysisResult(
        barriers=tuple(barriers),
        overall_severity=round(severity, 6),
    )
