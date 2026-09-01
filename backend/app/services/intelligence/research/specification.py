from __future__ import annotations

from uuid import uuid4

from .errors import InvalidResearchSpecification
from .models import MarketResearchSpecification
from .schemas import MarketResearchRequest


def create_specification(
    request: MarketResearchRequest,
) -> MarketResearchSpecification:
    """Create a validated market research specification."""

    if not isinstance(request, MarketResearchRequest):
        raise TypeError(
            "request must be a MarketResearchRequest"
        )

    objective = request.objective.strip()
    market_name = request.market_name.strip()

    if not objective:
        raise InvalidResearchSpecification(
            "Research objective cannot be empty."
        )

    if not market_name:
        raise InvalidResearchSpecification(
            "Market name cannot be empty."
        )

    if (
        request.base_year is not None
        and request.forecast_year is not None
        and request.forecast_year < request.base_year
    ):
        raise InvalidResearchSpecification(
            "Forecast year cannot be earlier than base year."
        )

    return MarketResearchSpecification(
        research_id=str(uuid4()),
        objective=objective,
        market_name=market_name,
        market_definition=request.market_definition,
        inclusions=list(request.inclusions),
        exclusions=list(request.exclusions),
        geography=list(request.geography),
        base_year=request.base_year,
        forecast_year=request.forecast_year,
        currency=request.currency.upper(),
        measurement_unit=request.measurement_unit,
        segments=list(request.segments),
        customer_groups=list(request.customer_groups),
        competitor_scope=list(request.competitor_scope),
        research_questions=list(request.research_questions),
        required_outputs=list(request.required_outputs),
        confidence_threshold=request.confidence_threshold,
    )
