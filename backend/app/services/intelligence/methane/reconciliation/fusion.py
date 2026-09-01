from __future__ import annotations

import math
from collections.abc import Iterable

from .models import ReconciliationInput


def calculate_weight(
    item: ReconciliationInput,
) -> float:
    """Calculate the fusion weight for an input.

    Explicit weights take precedence. Otherwise uncertainty-based
    inverse-variance weighting is used. Inputs without uncertainty
    receive a neutral weight of 1.
    """

    if item.weight is not None:
        return item.weight

    if item.uncertainty is not None and item.uncertainty > 0:
        return 1.0 / (item.uncertainty ** 2)

    return 1.0


def weighted_fusion(
    inputs: Iterable[ReconciliationInput],
) -> float:
    """Produce a weighted reconciled emission estimate."""

    values = tuple(inputs)

    if not values:
        raise ValueError("at least one input is required")

    weights = tuple(calculate_weight(item) for item in values)
    total_weight = sum(weights)

    if total_weight <= 0:
        raise ValueError("total fusion weight must be greater than zero")

    return sum(
        item.value * weight
        for item, weight in zip(values, weights)
    ) / total_weight


def fused_uncertainty(
    inputs: Iterable[ReconciliationInput],
) -> float | None:
    """Estimate uncertainty of the fused result."""

    values = tuple(inputs)

    if not values:
        raise ValueError("at least one input is required")

    known = [
        item.uncertainty
        for item in values
        if item.uncertainty is not None
    ]

    if not known:
        return None

    weights = tuple(calculate_weight(item) for item in values)

    if sum(weights) <= 0:
        return None

    weighted_variance = sum(
        weight * (uncertainty ** 2)
        for weight, uncertainty in zip(weights, [
            item.uncertainty or 0.0
            for item in values
        ])
    ) / sum(weights)

    return math.sqrt(weighted_variance)
