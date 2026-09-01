from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRecommendation:
    title: str
    action: str
    rationale: str
    priority: float = 0.0
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationsResult:
    recommendations: tuple[MarketRecommendation, ...]
    priority_recommendations: tuple[MarketRecommendation, ...]


def generate_recommendations(
    recommendations: list[MarketRecommendation],
    *,
    priority_threshold: float = 0.70,
) -> RecommendationsResult:

    if not 0.0 <= priority_threshold <= 1.0:
        raise ValueError(
            "priority_threshold must be between 0.0 and 1.0"
        )

    for recommendation in recommendations:
        if not recommendation.title.strip():
            raise ValueError(
                "recommendation title is required"
            )

        if not recommendation.action.strip():
            raise ValueError(
                "recommendation action is required"
            )

        if not recommendation.rationale.strip():
            raise ValueError(
                "recommendation rationale is required"
            )

        if not 0.0 <= recommendation.priority <= 1.0:
            raise ValueError(
                "recommendation priority must be between 0.0 and 1.0"
            )

        if not 0.0 <= recommendation.confidence <= 1.0:
            raise ValueError(
                "recommendation confidence must be between 0.0 and 1.0"
            )

    ordered = tuple(
        sorted(
            recommendations,
            key=lambda item: (
                item.priority,
                item.confidence,
                item.title.casefold(),
            ),
            reverse=True,
        )
    )

    priority = tuple(
        recommendation
        for recommendation in ordered
        if recommendation.priority >= priority_threshold
    )

    return RecommendationsResult(
        recommendations=ordered,
        priority_recommendations=priority,
    )
