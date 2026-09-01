from __future__ import annotations

from .models import MarketResearchSpecification
from .schemas import ResearchPlanResponse


DEFAULT_RESEARCH_STEPS = (
    "Define market scope and boundaries",
    "Identify authoritative sources",
    "Acquire market evidence",
    "Extract structured observations",
    "Normalize units, dates, currency and geography",
    "Estimate historical and current market size",
    "Build market segmentation",
    "Analyze customers and demand",
    "Analyze competitive landscape",
    "Analyze pricing",
    "Analyze market drivers",
    "Analyze market barriers",
    "Analyze regulatory environment",
    "Analyze geographic opportunities",
    "Analyze market trends",
    "Reconcile competing market estimates",
    "Generate market forecast",
    "Validate evidence and calculations",
    "Generate market insights",
    "Generate strategic recommendations",
    "Generate final research report",
)


DEFAULT_SOURCE_CATEGORIES = (
    "Government and regulatory sources",
    "Company and corporate sources",
    "Industry sources",
    "Academic and research sources",
    "Trade and statistical sources",
    "Relevant market and pricing sources",
)


def create_research_plan(
    specification: MarketResearchSpecification,
) -> ResearchPlanResponse:

    if not isinstance(
        specification,
        MarketResearchSpecification,
    ):
        raise TypeError(
            "specification must be a MarketResearchSpecification"
        )

    required_outputs = list(
        specification.required_outputs
    )

    if not required_outputs:
        required_outputs = [
            "Executive Summary",
            "Market Definition",
            "Market Size",
            "Segmentation",
            "Competitive Landscape",
            "Customer Analysis",
            "Pricing",
            "Market Drivers",
            "Market Barriers",
            "Regulatory Environment",
            "Geographic Opportunities",
            "Trends",
            "Forecast",
            "Recommendations",
            "Sources",
        ]

    return ResearchPlanResponse(
        research_id=specification.research_id,
        steps=list(DEFAULT_RESEARCH_STEPS),
        required_sources=list(DEFAULT_SOURCE_CATEGORIES),
        required_outputs=required_outputs,
    )
