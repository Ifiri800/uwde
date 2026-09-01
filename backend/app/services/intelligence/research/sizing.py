from __future__ import annotations

from dataclasses import dataclass

from .models import MarketEstimate
from .normalization import normalize_numeric


@dataclass(frozen=True)
class MarketSizingResult:
    estimates: tuple[MarketEstimate, ...]
    current_estimate: MarketEstimate | None
    historical_estimates: tuple[MarketEstimate, ...]
    forecast_estimates: tuple[MarketEstimate, ...]


def create_market_estimate(
    *,
    estimate_id: str,
    market_name: str,
    value: int | float,
    year: int,
    currency: str,
    unit: str = "value",
    methodology: str = "evidence_based",
    evidence_ids: tuple[str, ...] = (),
    assumptions: tuple[str, ...] = (),
    confidence: float = 0.0,
) -> MarketEstimate:

    normalized = normalize_numeric(
        value,
        unit=unit,
        currency=currency,
        year=year,
    )

    if not estimate_id.strip():
        raise ValueError("estimate_id is required")

    if not market_name.strip():
        raise ValueError("market_name is required")

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0.0 and 1.0"
        )

    return MarketEstimate(
        estimate_id=estimate_id,
        market_name=market_name,
        value=normalized.value,
        year=year,
        currency=normalized.currency or currency.upper(),
        unit=normalized.unit,
        methodology=methodology,
        evidence_ids=list(evidence_ids),
        assumptions=list(assumptions),
        confidence=confidence,
    )


def summarize_market_sizing(
    estimates: list[MarketEstimate],
    *,
    base_year: int | None = None,
    forecast_year: int | None = None,
) -> MarketSizingResult:

    ordered = sorted(
        estimates,
        key=lambda item: item.year,
    )

    historical = [
        item
        for item in ordered
        if base_year is None
        or item.year <= base_year
    ]

    forecast = [
        item
        for item in ordered
        if forecast_year is not None
        and item.year > (base_year or item.year)
        and item.year <= forecast_year
    ]

    current = ordered[-1] if ordered else None

    return MarketSizingResult(
        estimates=tuple(ordered),
        current_estimate=current,
        historical_estimates=tuple(historical),
        forecast_estimates=tuple(forecast),
    )
