from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceType:
    GOVERNMENT = "government"
    REGULATORY = "regulatory"
    COMPANY = "company"
    INDUSTRY = "industry"
    ACADEMIC = "academic"
    TRADE = "trade"
    STATISTICAL = "statistical"
    MARKET = "market"
    PRICING = "pricing"
    NEWS = "news"
    OTHER = "other"


@dataclass(frozen=True)
class ResearchSource:
    source_id: str
    url: str
    title: str
    publisher: str
    source_type: str = SourceType.OTHER
    jurisdiction: str | None = None
    publication_date: datetime | None = None
    accessed_at: datetime | None = None
    authority_score: float = 0.0
    reliability_score: float = 0.0
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")

        if not self.url.strip():
            raise ValueError("url is required")

        if not self.title.strip():
            raise ValueError("title is required")

        if not self.publisher.strip():
            raise ValueError("publisher is required")

        if not 0.0 <= self.authority_score <= 1.0:
            raise ValueError(
                "authority_score must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.reliability_score <= 1.0:
            raise ValueError(
                "reliability_score must be between 0.0 and 1.0"
            )

    @property
    def quality_score(self) -> float:
        return round(
            (
                self.authority_score
                + self.reliability_score
            )
            / 2.0,
            6,
        )

    @property
    def effective_accessed_at(self) -> datetime:
        return self.accessed_at or utc_now()


@dataclass(frozen=True)
class SourceAnalysisResult:
    sources: tuple[ResearchSource, ...]
    authoritative_sources: tuple[ResearchSource, ...]
    high_quality_sources: tuple[ResearchSource, ...]
    source_types: tuple[str, ...]
    jurisdictions: tuple[str, ...]
    average_quality: float


def analyze_sources(
    sources: list[ResearchSource],
    *,
    authority_threshold: float = 0.70,
    quality_threshold: float = 0.70,
) -> SourceAnalysisResult:
    if not 0.0 <= authority_threshold <= 1.0:
        raise ValueError(
            "authority_threshold must be between 0.0 and 1.0"
        )

    if not 0.0 <= quality_threshold <= 1.0:
        raise ValueError(
            "quality_threshold must be between 0.0 and 1.0"
        )

    seen: set[str] = set()

    for source in sources:
        if source.source_id in seen:
            raise ValueError(
                f"Duplicate source ID: {source.source_id}"
            )

        seen.add(source.source_id)

    ordered = tuple(
        sorted(
            sources,
            key=lambda source: (
                source.quality_score,
                source.authority_score,
                source.source_id,
            ),
            reverse=True,
        )
    )

    authoritative = tuple(
        source
        for source in ordered
        if source.authority_score >= authority_threshold
    )

    high_quality = tuple(
        source
        for source in ordered
        if source.quality_score >= quality_threshold
    )

    source_types = tuple(
        dict.fromkeys(
            source.source_type
            for source in ordered
        )
    )

    jurisdictions = tuple(
        dict.fromkeys(
            source.jurisdiction
            for source in ordered
            if source.jurisdiction
        )
    )

    average_quality = (
        round(
            sum(
                source.quality_score
                for source in ordered
            )
            / len(ordered),
            6,
        )
        if ordered
        else 0.0
    )

    return SourceAnalysisResult(
        sources=ordered,
        authoritative_sources=authoritative,
        high_quality_sources=high_quality,
        source_types=source_types,
        jurisdictions=jurisdictions,
        average_quality=average_quality,
    )


def select_sources(
    sources: list[ResearchSource],
    *,
    minimum_quality: float = 0.70,
    limit: int | None = None,
) -> tuple[ResearchSource, ...]:
    if not 0.0 <= minimum_quality <= 1.0:
        raise ValueError(
            "minimum_quality must be between 0.0 and 1.0"
        )

    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1")

    selected = [
        source
        for source in sources
        if source.quality_score >= minimum_quality
    ]

    selected.sort(
        key=lambda source: (
            source.quality_score,
            source.authority_score,
            source.source_id,
        ),
        reverse=True,
    )

    if limit is not None:
        selected = selected[:limit]

    return tuple(selected)


def create_source(
    *,
    source_id: str,
    url: str,
    title: str,
    publisher: str,
    source_type: str = SourceType.OTHER,
    jurisdiction: str | None = None,
    publication_date: datetime | None = None,
    accessed_at: datetime | None = None,
    authority_score: float = 0.0,
    reliability_score: float = 0.0,
    evidence_ids: tuple[str, ...] = (),
) -> ResearchSource:
    return ResearchSource(
        source_id=source_id,
        url=url,
        title=title,
        publisher=publisher,
        source_type=source_type,
        jurisdiction=jurisdiction,
        publication_date=publication_date,
        accessed_at=accessed_at or utc_now(),
        authority_score=authority_score,
        reliability_score=reliability_score,
        evidence_ids=evidence_ids,
    )
