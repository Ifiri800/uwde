from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MarketResearchReport:
    research_id: str
    title: str
    executive_summary: str

    market_definition: dict[str, Any] = field(default_factory=dict)
    market_size: dict[str, Any] = field(default_factory=dict)
    segmentation: list[dict[str, Any]] = field(default_factory=list)
    customers: list[dict[str, Any]] = field(default_factory=list)
    competition: list[dict[str, Any]] = field(default_factory=list)
    pricing: list[dict[str, Any]] = field(default_factory=list)
    drivers: list[dict[str, Any]] = field(default_factory=list)
    barriers: list[dict[str, Any]] = field(default_factory=list)
    regulation: list[dict[str, Any]] = field(default_factory=list)
    geography: list[dict[str, Any]] = field(default_factory=list)
    trends: list[dict[str, Any]] = field(default_factory=list)

    findings: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)

    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_id": self.research_id,
            "title": self.title,
            "executive_summary": self.executive_summary,
            "market_definition": self.market_definition,
            "market_size": self.market_size,
            "segmentation": self.segmentation,
            "customers": self.customers,
            "competition": self.competition,
            "pricing": self.pricing,
            "drivers": self.drivers,
            "barriers": self.barriers,
            "regulation": self.regulation,
            "geography": self.geography,
            "trends": self.trends,
            "findings": self.findings,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "sources": self.sources,
            "confidence": self.confidence,
        }


def generate_report(
    *,
    research_id: str,
    market_name: str,
    executive_summary: str,
    findings: list[str] | None = None,
    insights: list[str] | None = None,
    recommendations: list[Any] | None = None,
    sources: list[str] | None = None,
    confidence: float = 0.0,
    market_definition: dict[str, Any] | None = None,
    market_size: dict[str, Any] | None = None,
    segmentation: list[dict[str, Any]] | None = None,
    customers: list[dict[str, Any]] | None = None,
    competition: list[dict[str, Any]] | None = None,
    pricing: list[dict[str, Any]] | None = None,
    drivers: list[dict[str, Any]] | None = None,
    barriers: list[dict[str, Any]] | None = None,
    regulation: list[dict[str, Any]] | None = None,
    geography: list[dict[str, Any]] | None = None,
    trends: list[dict[str, Any]] | None = None,
) -> MarketResearchReport:

    if not research_id.strip():
        raise ValueError("research_id is required")

    if not market_name.strip():
        raise ValueError("market_name is required")

    if not executive_summary.strip():
        raise ValueError("executive_summary is required")

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0.0 and 1.0"
        )

    recommendation_dicts: list[dict[str, Any]] = []

    for recommendation in recommendations or []:
        if hasattr(recommendation, "__dict__"):
            recommendation_dicts.append(
                dict(recommendation.__dict__)
            )
        elif isinstance(recommendation, dict):
            recommendation_dicts.append(
                dict(recommendation)
            )
        else:
            recommendation_dicts.append(
                {"value": str(recommendation)}
            )

    return MarketResearchReport(
        research_id=research_id,
        title=f"Market Research Report: {market_name}",
        executive_summary=executive_summary,
        market_definition=market_definition or {},
        market_size=market_size or {},
        segmentation=segmentation or [],
        customers=customers or [],
        competition=competition or [],
        pricing=pricing or [],
        drivers=drivers or [],
        barriers=barriers or [],
        regulation=regulation or [],
        geography=geography or [],
        trends=trends or [],
        findings=list(findings or []),
        insights=list(insights or []),
        recommendations=recommendation_dicts,
        sources=list(sources or []),
        confidence=confidence,
    )
