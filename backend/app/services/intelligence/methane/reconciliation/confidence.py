from __future__ import annotations

from collections.abc import Iterable

from .models import ReconciliationInput


def confidence_from_uncertainty(
    value: float,
    uncertainty: float | None,
) -> float:
    """Return a bounded confidence score based on relative uncertainty."""

    if value < 0:
        raise ValueError("value cannot be negative")

    if uncertainty is not None and uncertainty < 0:
        raise ValueError("uncertainty cannot be negative")

    if uncertainty is None:
        return 0.5

    if value == 0:
        return 1.0 if uncertainty == 0 else 0.0

    relative_uncertainty = uncertainty / value

    return max(
        0.0,
        min(
            1.0,
            1.0 - relative_uncertainty,
        ),
    )


def calculate_reconciliation_confidence(
    inputs: Iterable[ReconciliationInput],
    *,
    discrepancy_penalty: float = 0.25,
) -> float:
    """Calculate a deterministic confidence score for reconciled inputs."""

    if not 0.0 <= discrepancy_penalty <= 1.0:
        raise ValueError(
            "discrepancy_penalty must be between 0 and 1"
        )

    values = tuple(inputs)

    if not values:
        raise ValueError("at least one input is required")

    scores = [
        confidence_from_uncertainty(
            item.value,
            item.uncertainty,
        )
        for item in values
    ]

    return max(
        0.0,
        min(
            1.0,
            sum(scores) / len(scores),
        ),
    )
