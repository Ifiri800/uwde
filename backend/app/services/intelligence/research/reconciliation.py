from __future__ import annotations

from dataclasses import dataclass

from .models import MarketEstimate


@dataclass(frozen=True)
class EstimateComparison:
    estimate_id: str
    value: float
    difference_from_reference: float
    relative_difference: float


@dataclass(frozen=True)
class ReconciliationResult:
    market_name: str
    reference_estimate: MarketEstimate | None
    comparisons: tuple[EstimateComparison, ...]
    reconciled_value: float | None
    reconciled_year: int | None
    confidence: float
    explanation: str


def reconcile_estimates(
    estimates: list[MarketEstimate],
) -> ReconciliationResult:

    if not estimates:
        return ReconciliationResult(
            market_name="",
            reference_estimate=None,
            comparisons=(),
            reconciled_value=None,
            reconciled_year=None,
            confidence=0.0,
            explanation="No market estimates were supplied.",
        )

    market_names = {
        estimate.market_name.casefold()
        for estimate in estimates
    }

    if len(market_names) != 1:
        raise ValueError(
            "All estimates must refer to the same market"
        )

    currencies = {
        estimate.currency.upper()
        for estimate in estimates
    }

    units = {
        estimate.unit
        for estimate in estimates
    }

    if len(currencies) != 1:
        raise ValueError(
            "All estimates must use the same currency"
        )

    if len(units) != 1:
        raise ValueError(
            "All estimates must use the same unit"
        )

    ordered = sorted(
        estimates,
        key=lambda estimate: (
            estimate.confidence,
            estimate.year,
        ),
        reverse=True,
    )

    reference = ordered[0]

    comparisons: list[EstimateComparison] = []

    for estimate in estimates:
        difference = estimate.value - reference.value

        relative_difference = (
            difference / reference.value
            if reference.value != 0
            else 0.0
        )

        comparisons.append(
            EstimateComparison(
                estimate_id=estimate.estimate_id,
                value=estimate.value,
                difference_from_reference=round(
                    difference,
                    6,
                ),
                relative_difference=round(
                    relative_difference,
                    6,
                ),
            )
        )

    total_weight = sum(
        max(estimate.confidence, 0.01)
        for estimate in estimates
    )

    reconciled_value = sum(
        estimate.value
        * max(estimate.confidence, 0.01)
        for estimate in estimates
    ) / total_weight

    average_confidence = sum(
        estimate.confidence
        for estimate in estimates
    ) / len(estimates)

    spread = (
        max(estimate.value for estimate in estimates)
        - min(estimate.value for estimate in estimates)
    )

    normalized_spread = (
        spread / reference.value
        if reference.value != 0
        else 0.0
    )

    consistency_factor = max(
        0.0,
        1.0 - min(1.0, normalized_spread),
    )

    confidence = round(
        average_confidence * consistency_factor,
        6,
    )

    explanation = (
        f"Reconciled {len(estimates)} estimates using "
        f"confidence-weighted aggregation. "
        f"Reference estimate: {reference.estimate_id}. "
        f"Estimate dispersion was "
        f"{normalized_spread:.3f} relative to the reference."
    )

    return ReconciliationResult(
        market_name=reference.market_name,
        reference_estimate=reference,
        comparisons=tuple(comparisons),
        reconciled_value=round(
            reconciled_value,
            6,
        ),
        reconciled_year=reference.year,
        confidence=confidence,
        explanation=explanation,
    )
