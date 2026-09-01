from __future__ import annotations

from dataclasses import dataclass

from .models import MarketResearchSpecification


@dataclass(frozen=True)
class MarketDefinitionResult:
    market_name: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]
    geographies: tuple[str, ...]


def define_market(
    specification: MarketResearchSpecification,
) -> MarketDefinitionResult:
    if not isinstance(
        specification,
        MarketResearchSpecification,
    ):
        raise TypeError(
            "specification must be a MarketResearchSpecification"
        )

    definition = specification.market_definition

    if not definition:
        definition = (
            f"The {specification.market_name} market comprises "
            "the products, services, technologies, providers, "
            "and demand represented within the specified scope."
        )

    return MarketDefinitionResult(
        market_name=specification.market_name,
        definition=definition,
        inclusions=tuple(specification.inclusions),
        exclusions=tuple(specification.exclusions),
        geographies=tuple(specification.geography),
    )
