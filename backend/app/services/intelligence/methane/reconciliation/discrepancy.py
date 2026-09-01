from __future__ import annotations

from .models import (
    DiscrepancyResult,
    ReconciliationInput,
)


def calculate_discrepancy(
    input_item: ReconciliationInput,
    fused_value: float,
    *,
    tolerance: float = 0.10,
) -> DiscrepancyResult:
    """Compare one reconciliation input against the fused estimate."""

    if tolerance < 0:
        raise ValueError(
            "tolerance cannot be negative"
        )

    if fused_value < 0:
        raise ValueError(
            "fused value cannot be negative"
        )

    if input_item.unit.strip() == "":
        raise ValueError(
            "input unit is required"
        )

    difference = abs(
        input_item.value - fused_value
    )

    denominator = max(
        abs(input_item.value),
        abs(fused_value),
    )

    relative_difference = (
        difference / denominator
        if denominator > 0
        else 0.0
    )

    percent_difference = (
        relative_difference * 100.0
    )

    return DiscrepancyResult(
        input_id=input_item.input_id,
        method=input_item.method,
        estimate_value=input_item.value,
        fused_value=fused_value,
        absolute_difference=difference,
        relative_difference=relative_difference,
        percent_difference=percent_difference,
        within_tolerance=(
            relative_difference <= tolerance
        ),
    )


def calculate_pairwise_discrepancies(
    inputs: tuple[ReconciliationInput, ...],
    *,
    tolerance: float = 0.10,
) -> tuple[DiscrepancyResult, ...]:
    """Compare every input against the reconciled fused estimate."""

    values = tuple(inputs)

    if not values:
        return ()

    from .fusion import weighted_fusion

    fused_value = weighted_fusion(values)

    return tuple(
        calculate_discrepancy(
            item,
            fused_value,
            tolerance=tolerance,
        )
        for item in values
    )
