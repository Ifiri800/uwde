from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningEngine,
    CompetitivePositioningResult,
    PositioningDimension,
    PositioningLevel,
)
from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal


@dataclass(frozen=True)
class CompetitiveBenchmarkEntry:
    competitor_id: str
    overall_score: float
    level: PositioningLevel
    confidence: float
    positioning: CompetitivePositioningResult

    def __post_init__(self) -> None:
        if not self.competitor_id.strip():
            raise ValueError("competitor_id is required")

        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(
                "overall_score must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if self.positioning.competitor_id != self.competitor_id:
            raise ValueError(
                "positioning competitor_id must match competitor_id"
            )

    def to_dict(self) -> dict:
        return {
            "competitor_id": self.competitor_id,
            "overall_score": self.overall_score,
            "level": self.level.value,
            "confidence": self.confidence,
            "positioning": self.positioning.to_dict(),
        }


@dataclass(frozen=True)
class CompetitiveBenchmarkDimension:
    dimension: PositioningDimension
    rankings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension.value,
            "rankings": list(self.rankings),
        }


@dataclass(frozen=True)
class CompetitiveBenchmarkResult:
    company_id: str
    competitors: tuple[CompetitiveBenchmarkEntry, ...]
    dimensions: tuple[CompetitiveBenchmarkDimension, ...]
    overall_ranking: tuple[str, ...]
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
            "competitors": [
                competitor.to_dict()
                for competitor in self.competitors
            ],
            "dimensions": [
                dimension.to_dict()
                for dimension in self.dimensions
            ],
            "overall_ranking": list(self.overall_ranking),
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


class CompetitiveBenchmarkingEngine:
    """
    Benchmarks one company against multiple competitors.

    The 9.3 CompetitivePositioningEngine remains the source of truth
    for pairwise scoring. This layer ranks and consolidates those
    structured positioning results.
    """

    def __init__(
        self,
        positioning_engine: CompetitivePositioningEngine | None = None,
    ) -> None:
        self.positioning_engine = (
            positioning_engine
            or CompetitivePositioningEngine()
        )

    def benchmark(
        self,
        company: Company,
        competitors: list[Company],
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> CompetitiveBenchmarkResult:
        if not isinstance(company, Company):
            raise TypeError("company must be a Company")

        if not isinstance(competitors, list):
            raise TypeError("competitors must be a list")

        if any(
            not isinstance(item, Company)
            for item in competitors
        ):
            raise TypeError(
                "competitors must contain only Company objects"
            )

        if any(
            item.entity_id == company.entity_id
            for item in competitors
        ):
            raise ValueError(
                "company cannot appear in competitors"
            )

        competitor_ids = [
            competitor.entity_id
            for competitor in competitors
        ]

        if len(set(competitor_ids)) != len(competitor_ids):
            raise ValueError(
                "competitors must have unique entity IDs"
            )

        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        if evidence is not None:
            if not isinstance(evidence, list):
                raise TypeError("evidence must be a list")

            if any(
                not isinstance(item, Evidence)
                for item in evidence
            ):
                raise TypeError(
                    "evidence must contain only Evidence objects"
                )

        evidence_records = evidence or []

        entries = [
            self._build_entry(
                company,
                competitor,
                signals,
                evidence_records,
            )
            for competitor in competitors
        ]

        original_entries = list(entries)

        entries.sort(
            key=lambda entry: (
                entry.overall_score,
                -entry.confidence,
                entry.competitor_id,
            )
        )

        dimensions = self._build_dimension_rankings(entries)

        strongest_dimensions, weakest_dimensions = (
            self._build_dimension_extremes(entries)
        )

        signal_ids = self._consolidate_signal_ids(original_entries)
        evidence_ids = self._consolidate_evidence_ids(original_entries)

        confidence = round(
            (
                sum(entry.confidence for entry in entries)
                / len(entries)
            )
            if entries
            else 0.0,
            4,
        )

        reasons = self._build_reasons(
            entries,
            strongest_dimensions,
            weakest_dimensions,
        )

        return CompetitiveBenchmarkResult(
            company_id=company.entity_id,
            competitors=tuple(entries),
            dimensions=tuple(dimensions),
            overall_ranking=tuple(
                entry.competitor_id
                for entry in entries
            ),
            strongest_dimensions=strongest_dimensions,
            weakest_dimensions=weakest_dimensions,
            signal_ids=signal_ids,
            evidence_ids=evidence_ids,
            confidence=confidence,
            reasons=reasons,
        )

    def _build_entry(
        self,
        company: Company,
        competitor: Company,
        signals: list[Signal],
        evidence: list[Evidence],
    ) -> CompetitiveBenchmarkEntry:
        positioning = self.positioning_engine.evaluate(
            company,
            competitor,
            signals,
            evidence,
        )

        return CompetitiveBenchmarkEntry(
            competitor_id=competitor.entity_id,
            overall_score=positioning.overall_score,
            level=positioning.level,
            confidence=positioning.confidence,
            positioning=positioning,
        )

    @staticmethod
    def _build_dimension_rankings(
        entries: list[CompetitiveBenchmarkEntry],
    ) -> list[CompetitiveBenchmarkDimension]:
        rankings: list[CompetitiveBenchmarkDimension] = []

        for dimension in PositioningDimension:
            ordered = sorted(
                entries,
                key=lambda entry: (
                    CompetitiveBenchmarkingEngine
                    ._dimension_score(
                        entry.positioning,
                        dimension,
                    ),
                    -entry.confidence,
                    entry.competitor_id,
                ),
            )

            rankings.append(
                CompetitiveBenchmarkDimension(
                    dimension=dimension,
                    rankings=tuple(
                        entry.competitor_id
                        for entry in ordered
                    ),
                )
            )

        return rankings

    @staticmethod
    def _dimension_score(
        positioning: CompetitivePositioningResult,
        dimension: PositioningDimension,
    ) -> float:
        for assessment in positioning.assessments:
            if assessment.dimension == dimension:
                return assessment.score

        return 0.0

    @staticmethod
    def _build_dimension_extremes(
        entries: list[CompetitiveBenchmarkEntry],
    ) -> tuple[
        tuple[PositioningDimension, ...],
        tuple[PositioningDimension, ...],
    ]:
        if not entries:
            return (), ()

        dimension_scores: dict[
            PositioningDimension,
            float,
        ] = {}

        for dimension in PositioningDimension:
            scores = [
                CompetitiveBenchmarkingEngine._dimension_score(
                    entry.positioning,
                    dimension,
                )
                for entry in entries
            ]

            dimension_scores[dimension] = (
                sum(scores) / len(scores)
            )

        highest = max(dimension_scores.values())
        lowest = min(dimension_scores.values())

        strongest = tuple(
            dimension
            for dimension, score in dimension_scores.items()
            if score == highest
        )

        weakest = tuple(
            dimension
            for dimension, score in dimension_scores.items()
            if score == lowest
        )

        return strongest, weakest

    @staticmethod
    def _consolidate_signal_ids(
        entries: list[CompetitiveBenchmarkEntry],
    ) -> tuple[str, ...]:
        signal_ids: list[str] = []

        for entry in entries:
            for signal_id in entry.positioning.signal_ids:
                if signal_id not in signal_ids:
                    signal_ids.append(signal_id)

        return tuple(signal_ids)

    @staticmethod
    def _consolidate_evidence_ids(
        entries: list[CompetitiveBenchmarkEntry],
    ) -> tuple[str, ...]:
        evidence_ids: list[str] = []

        for entry in entries:
            for evidence_id in entry.positioning.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        return tuple(evidence_ids)

    @staticmethod
    def _build_reasons(
        entries: list[CompetitiveBenchmarkEntry],
        strongest_dimensions: tuple[PositioningDimension, ...],
        weakest_dimensions: tuple[PositioningDimension, ...],
    ) -> tuple[str, ...]:
        reasons: list[str] = []

        if entries:
            winner = entries[0]

            reasons.append(
                f"{winner.competitor_id} ranks first overall"
            )

            reasons.append(
                f"{winner.competitor_id} has an overall positioning "
                f"score of {winner.overall_score:.4f}"
            )

        for dimension in strongest_dimensions:
            reasons.append(
                f"strongest benchmark dimension: "
                f"{dimension.value.replace('_', ' ')}"
            )

        for dimension in weakest_dimensions:
            reasons.append(
                f"weakest benchmark dimension: "
                f"{dimension.value.replace('_', ' ')}"
            )

        return tuple(reasons)


def benchmark_competitive_positioning(
    company: Company,
    competitors: list[Company],
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> CompetitiveBenchmarkResult:
    """
    Convenience function using the default benchmarking engine.
    """
    return CompetitiveBenchmarkingEngine().benchmark(
        company,
        competitors,
        signals,
        evidence,
    )
