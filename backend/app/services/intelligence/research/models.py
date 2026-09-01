from __future__ import annotations

from dataclasses import dataclass, field

from backend.app.services.intelligence.domain.evidence import Evidence


@dataclass(frozen=True)
class MarketResearchSpecification:
    research_id: str
    objective: str
    market_name: str

    market_definition: str | None = None

    inclusions: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)

    geography: list[str] = field(default_factory=list)

    base_year: int | None = None
    forecast_year: int | None = None

    currency: str = "USD"
    measurement_unit: str = "value"

    segments: list[str] = field(default_factory=list)
    customer_groups: list[str] = field(default_factory=list)
    competitor_scope: list[str] = field(default_factory=list)

    research_questions: list[str] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)

    confidence_threshold: float = 0.70


@dataclass(frozen=True)
class MarketEstimate:
    estimate_id: str
    market_name: str
    value: float
    year: int

    currency: str = "USD"
    unit: str = "value"
    methodology: str = "unknown"

    evidence_ids: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    confidence: float = 0.0


@dataclass(frozen=True)
class ResearchQualityScore:
    source_quality: float = 0.0
    evidence_coverage: float = 0.0
    numerical_consistency: float = 0.0
    segmentation_quality: float = 0.0
    forecast_confidence: float = 0.0
    citation_coverage: float = 0.0
    overall_score: float = 0.0


@dataclass
class MarketResearchProject:
    specification: MarketResearchSpecification

    evidence: list[Evidence] = field(default_factory=list)
    estimates: list[MarketEstimate] = field(default_factory=list)

    quality: ResearchQualityScore | None = None

    findings: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    status: str = "created"
