from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.intelligence.competitive.benchmarking import (
    CompetitiveBenchmarkResult,
)
from backend.app.services.intelligence.competitive.positioning import (
    PositioningDimension,
)


@dataclass(frozen=True)
class CompetitiveSynthesisInsight:
    """
    A single explainable competitive-intelligence conclusion.
    """

    category: str
    subject_id: str
    message: str
    confidence: float
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("category is required")

        if not self.subject_id.strip():
            raise ValueError("subject_id is required")

        if not self.message.strip():
            raise ValueError("message is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "subject_id": self.subject_id,
            "message": self.message,
            "confidence": self.confidence,
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class CompetitiveSynthesisResult:
    """
    Structured, explainable synthesis of competitive intelligence.
    """

    company_id: str
    insights: tuple[CompetitiveSynthesisInsight, ...] = ()
    strongest_competitors: tuple[str, ...] = ()
    strategic_pressures: tuple[str, ...] = ()
    strongest_dimensions: tuple[PositioningDimension, ...] = ()
    weakest_dimensions: tuple[PositioningDimension, ...] = ()
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "insights": [
                insight.to_dict()
                for insight in self.insights
            ],
            "strongest_competitors": list(
                self.strongest_competitors
            ),
            "strategic_pressures": list(
                self.strategic_pressures
            ),
            "strongest_dimensions": [
                dimension.value
                for dimension in self.strongest_dimensions
            ],
            "weakest_dimensions": [
                dimension.value
                for dimension in self.weakest_dimensions
            ],
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "reasons": list(self.reasons),
        }


class CompetitiveSynthesisEngine:
    """
    Converts competitive benchmarking output into
    higher-level strategic intelligence.

    Benchmarking remains the source of truth for
    competitor ranking and positioning dimensions.
    """

    def synthesize(
        self,
        benchmark: CompetitiveBenchmarkResult,
    ) -> CompetitiveSynthesisResult:
        if not isinstance(
            benchmark,
            CompetitiveBenchmarkResult,
        ):
            raise TypeError(
                "benchmark must be a CompetitiveBenchmarkResult"
            )

        strongest_competitors = tuple(
            entry.competitor_id
            for entry in benchmark.competitors[:3]
        )

        strategic_pressures = tuple(
            entry.competitor_id
            for entry in benchmark.competitors
            if entry.overall_score >= 0.75
        )

        insights: list[CompetitiveSynthesisInsight] = []

        if strongest_competitors:
            top = strongest_competitors[0]

            insights.append(
                CompetitiveSynthesisInsight(
                    category="competitive_strength",
                    subject_id=top,
                    message=(
                        f"{top} is the strongest competitor "
                        "in the benchmark"
                    ),
                    confidence=benchmark.confidence,
                    signal_ids=benchmark.signal_ids,
                    evidence_ids=benchmark.evidence_ids,
                )
            )

        for competitor_id in strategic_pressures:
            insights.append(
                CompetitiveSynthesisInsight(
                    category="strategic_pressure",
                    subject_id=competitor_id,
                    message=(
                        f"{competitor_id} represents significant "
                        "competitive pressure"
                    ),
                    confidence=benchmark.confidence,
                    signal_ids=benchmark.signal_ids,
                    evidence_ids=benchmark.evidence_ids,
                )
            )

        reasons = list(benchmark.reasons)

        if strongest_competitors:
            reasons.append(
                f"top competitive threat: "
                f"{strongest_competitors[0]}"
            )

        if strategic_pressures:
            reasons.append(
                f"{len(strategic_pressures)} competitor(s) "
                "meet the strategic pressure threshold"
            )

        return CompetitiveSynthesisResult(
            company_id=benchmark.company_id,
            insights=tuple(insights),
            strongest_competitors=strongest_competitors,
            strategic_pressures=strategic_pressures,
            strongest_dimensions=benchmark.strongest_dimensions,
            weakest_dimensions=benchmark.weakest_dimensions,
            signal_ids=benchmark.signal_ids,
            evidence_ids=benchmark.evidence_ids,
            confidence=benchmark.confidence,
            reasons=tuple(reasons),
        )


def synthesize_competitive_intelligence(
    benchmark: CompetitiveBenchmarkResult,
) -> CompetitiveSynthesisResult:
    """
    Convenience function using the default synthesis engine.
    """
    return CompetitiveSynthesisEngine().synthesize(benchmark)
