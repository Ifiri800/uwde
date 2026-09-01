from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketTrend:
    name: str
    description: str
    direction: str = "stable"
    strength: float = 0.0
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrendsAnalysisResult:
    trends: tuple[MarketTrend, ...]
    dominant_trends: tuple[str, ...]


def analyze_trends(
    trends: list[MarketTrend],
    *,
    dominance_threshold: float = 0.70,
) -> TrendsAnalysisResult:

    if not 0.0 <= dominance_threshold <= 1.0:
        raise ValueError(
            "dominance_threshold must be between 0.0 and 1.0"
        )

    for trend in trends:
        if not trend.name.strip():
            raise ValueError("trend name is required")

        if not 0.0 <= trend.strength <= 1.0:
            raise ValueError(
                "trend strength must be between 0.0 and 1.0"
            )

    dominant = tuple(
        trend.name
        for trend in trends
        if trend.strength >= dominance_threshold
    )

    return TrendsAnalysisResult(
        trends=tuple(trends),
        dominant_trends=dominant,
    )
