from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MarketResearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=5000)
    market_name: str = Field(min_length=1, max_length=500)

    market_definition: str | None = Field(
        default=None,
        max_length=5000,
    )

    inclusions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)

    geography: list[str] = Field(default_factory=list)

    base_year: int | None = Field(
        default=None,
        ge=1900,
        le=2200,
    )

    forecast_year: int | None = Field(
        default=None,
        ge=1900,
        le=2200,
    )

    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
    )

    measurement_unit: str = Field(
        default="value",
        min_length=1,
        max_length=100,
    )

    segments: list[str] = Field(default_factory=list)
    customer_groups: list[str] = Field(default_factory=list)
    competitor_scope: list[str] = Field(default_factory=list)

    research_questions: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)

    confidence_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
    )


class ResearchPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    steps: list[str]
    required_sources: list[str]
    required_outputs: list[str]


class MarketResearchStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_id: str
    status: str
