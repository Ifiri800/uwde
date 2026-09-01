from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceObservation:
    product: str
    price: float
    currency: str
    unit: str
    observed_at: object
    source_id: str | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PricingAnalysisResult:
    observations: tuple[PriceObservation, ...]
    minimum_price: float | None
    maximum_price: float | None
    average_price: float | None
    currency: str | None
    unit: str | None


def analyze_pricing(
    observations: list[PriceObservation],
) -> PricingAnalysisResult:

    if not observations:
        return PricingAnalysisResult(
            observations=(),
            minimum_price=None,
            maximum_price=None,
            average_price=None,
            currency=None,
            unit=None,
        )

    for observation in observations:
        if observation.price < 0:
            raise ValueError("price cannot be negative")

        if not observation.currency.strip():
            raise ValueError("currency is required")

        if not observation.unit.strip():
            raise ValueError("unit is required")

    prices = [
        observation.price
        for observation in observations
    ]

    currencies = {
        observation.currency.upper()
        for observation in observations
    }

    units = {
        observation.unit
        for observation in observations
    }

    return PricingAnalysisResult(
        observations=tuple(observations),
        minimum_price=min(prices),
        maximum_price=max(prices),
        average_price=round(
            sum(prices) / len(prices),
            6,
        ),
        currency=(
            currencies.pop()
            if len(currencies) == 1
            else None
        ),
        unit=(
            units.pop()
            if len(units) == 1
            else None
        ),
    )
