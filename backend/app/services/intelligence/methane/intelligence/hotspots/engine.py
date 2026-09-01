from __future__ import annotations

from collections.abc import Iterable

from .models import IntelligenceRanking


def identify_hotspots(
    observations: Iterable[tuple[str, float]],
    *,
    threshold: float = 0.75,
) -> tuple[IntelligenceRanking, ...]:

    candidates = [
        (entity_id, score)
        for entity_id, score in observations
        if score >= threshold
    ]

    candidates.sort(key=lambda item: (-item[1], item[0]))

    return tuple(
        IntelligenceRanking(
            entity_id=entity_id,
            rank=index,
            score=score,
            category="methane_hotspot",
            rationale=(
                f"Hotspot score {score} meets or exceeds "
                f"threshold {threshold}.",
            ),
            metadata={"threshold": threshold},
        )
        for index, (entity_id, score) in enumerate(candidates, start=1)
    )
