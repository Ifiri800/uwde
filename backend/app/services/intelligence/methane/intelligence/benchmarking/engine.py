from __future__ import annotations

from collections.abc import Iterable

from .models import IntelligenceRanking


def benchmark_facilities(
    observations: Iterable[tuple[str, float]],
) -> tuple[IntelligenceRanking, ...]:

    values = tuple(observations)

    if not values:
        return ()

    mean = sum(value for _, value in values) / len(values)

    return tuple(
        IntelligenceRanking(
            entity_id=entity_id,
            rank=1,
            score=value,
            category=(
                "above_benchmark"
                if value > mean
                else "at_or_below_benchmark"
            ),
            rationale=(
                f"Facility value {value:.4f}; "
                f"peer benchmark {mean:.4f}.",
            ),
            metadata={"peer_mean": mean},
        )
        for entity_id, value in values
    )
