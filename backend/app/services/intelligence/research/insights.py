from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketInsight:
    title: str
    finding: str
    implication: str
    importance: float = 0.0
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class InsightsResult:
    insights: tuple[MarketInsight, ...]
    high_priority: tuple[MarketInsight, ...]


def generate_insights(
    insights: list[MarketInsight],
    *,
    importance_threshold: float = 0.70,
) -> InsightsResult:

    if not 0.0 <= importance_threshold <= 1.0:
        raise ValueError(
            "importance_threshold must be between 0.0 and 1.0"
        )

    for insight in insights:
        if not insight.title.strip():
            raise ValueError("insight title is required")

        if not insight.finding.strip():
            raise ValueError("insight finding is required")

        if not insight.implication.strip():
            raise ValueError("insight implication is required")

        if not 0.0 <= insight.importance <= 1.0:
            raise ValueError(
                "insight importance must be between 0.0 and 1.0"
            )

        if not 0.0 <= insight.confidence <= 1.0:
            raise ValueError(
                "insight confidence must be between 0.0 and 1.0"
            )

    priority = tuple(
        insight
        for insight in insights
        if insight.importance >= importance_threshold
    )

    return InsightsResult(
        insights=tuple(insights),
        high_priority=priority,
    )
