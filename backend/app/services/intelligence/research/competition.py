from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Competitor:
    name: str
    description: str = ""
    market_position: str | None = None
    products: tuple[str, ...] = ()
    geographies: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompetitionAnalysisResult:
    competitors: tuple[Competitor, ...]
    competitive_factors: tuple[str, ...]
    market_gaps: tuple[str, ...]


def analyze_competition(
    competitors: list[Competitor],
    *,
    competitive_factors: list[str] | None = None,
    market_gaps: list[str] | None = None,
) -> CompetitionAnalysisResult:

    names: set[str] = set()

    for competitor in competitors:
        if not competitor.name.strip():
            raise ValueError("competitor name is required")

        key = competitor.name.casefold()

        if key in names:
            raise ValueError(
                f"Duplicate competitor: {competitor.name}"
            )

        names.add(key)

    return CompetitionAnalysisResult(
        competitors=tuple(competitors),
        competitive_factors=tuple(competitive_factors or []),
        market_gaps=tuple(market_gaps or []),
    )
