from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeographicMarket:
    name: str
    description: str = ""
    opportunity_score: float = 0.0
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeographyAnalysisResult:
    markets: tuple[GeographicMarket, ...]
    priority_markets: tuple[str, ...]


def analyze_geography(
    markets: list[GeographicMarket],
    *,
    priority_threshold: float = 0.70,
) -> GeographyAnalysisResult:

    if not 0.0 <= priority_threshold <= 1.0:
        raise ValueError(
            "priority_threshold must be between 0.0 and 1.0"
        )

    for market in markets:
        if not market.name.strip():
            raise ValueError(
                "geographic market name is required"
            )

        if not 0.0 <= market.opportunity_score <= 1.0:
            raise ValueError(
                "opportunity_score must be between 0.0 and 1.0"
            )

    priority = tuple(
        market.name
        for market in markets
        if market.opportunity_score >= priority_threshold
    )

    return GeographyAnalysisResult(
        markets=tuple(markets),
        priority_markets=priority,
    )
