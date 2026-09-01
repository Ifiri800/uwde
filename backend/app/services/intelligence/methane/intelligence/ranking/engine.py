from __future__ import annotations

from collections.abc import Iterable

from .models import IntelligenceRanking


def rank_assets(
    observations: Iterable[tuple[str, float]],
    *,
    category: str = "methane_risk",
) -> tuple[IntelligenceRanking, ...]:

    ordered = sorted(
        observations,
        key=lambda item: (-item[1], item[0]),
    )

    return tuple(
        IntelligenceRanking(
            entity_id=entity_id,
            rank=index,
            score=max(0.0, min(1.0, score)),
            category=category,
            rationale=(f"Ranked using {category} score.",),
        )
        for index, (entity_id, score) in enumerate(ordered, start=1)
    )
