from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Mapping

from ..quantification.models import (
    EmissionEstimate,
    QuantificationMethod,
)

from .models import ReconciliationInput


def create_reconciliation_input(
    input_id: str,
    estimate: EmissionEstimate,
    *,
    weight: float = 1.0,
    uncertainty: float | None = None,
    quality_score: float = 1.0,
    metadata: Mapping[str, Any] | None = None,
) -> ReconciliationInput:
    """Create a validated Layer 9 reconciliation input."""

    return ReconciliationInput(
        input_id=input_id,
        estimate=estimate,
        weight=weight,
        uncertainty=uncertainty,
        quality_score=quality_score,
        metadata=metadata or {},
    )


def from_emission_estimate(
    estimate: EmissionEstimate,
    *,
    input_id: str | None = None,
    weight: float = 1.0,
    uncertainty: float | None = None,
    quality_score: float = 1.0,
    metadata: Mapping[str, Any] | None = None,
) -> ReconciliationInput:
    """Convert a Layer 7 emission estimate into a Layer 9 input."""

    return create_reconciliation_input(
        input_id=input_id or estimate.estimate_id,
        estimate=estimate,
        weight=weight,
        uncertainty=uncertainty,
        quality_score=quality_score,
        metadata=metadata,
    )


def normalize_inputs(
    inputs: Iterable[ReconciliationInput],
) -> tuple[ReconciliationInput, ...]:
    """Normalize inputs while preserving order and rejecting duplicates."""

    normalized = tuple(inputs)

    if not normalized:
        raise ValueError(
            "at least one reconciliation input is required"
        )

    ids = [item.input_id for item in normalized]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "duplicate reconciliation input IDs"
        )

    return normalized


def validate_input_units(
    inputs: Iterable[ReconciliationInput],
) -> str:
    """Validate that all inputs use the same emissions unit."""

    normalized = normalize_inputs(inputs)

    units = {item.unit for item in normalized}

    if len(units) != 1:
        raise ValueError(
            "reconciliation inputs must use matching units"
        )

    return normalized[0].unit


def validate_input_compatibility(
    inputs: Iterable[ReconciliationInput],
) -> list[str]:
    """Validate compatibility of Layer 9 inputs."""

    values = tuple(inputs)

    errors: list[str] = []

    if not values:
        errors.append(
            "at least one reconciliation input is required"
        )
        return errors

    ids = [item.input_id for item in values]

    if len(ids) != len(set(ids)):
        errors.append(
            "duplicate reconciliation input IDs"
        )

    units = {item.unit for item in values}

    if len(units) > 1:
        errors.append(
            "reconciliation inputs must use matching units"
        )

    levels = {item.level for item in values}

    if len(levels) > 1:
        errors.append(
            "reconciliation inputs must use matching quantification levels"
        )

    return errors


def inputs_for_method(
    inputs: Iterable[ReconciliationInput],
    method: QuantificationMethod | str,
) -> tuple[ReconciliationInput, ...]:
    """Return inputs belonging to a quantification method."""

    normalized = normalize_inputs(inputs)

    try:
        method = QuantificationMethod(method)
    except ValueError as exc:
        raise ValueError(
            f"unsupported quantification method: {method}"
        ) from exc

    return tuple(
        item
        for item in normalized
        if item.method == method
    )


def require_method_coverage(
    inputs: Iterable[ReconciliationInput],
) -> None:
    """Require Bottom-Up, Measurement and Top-Down estimates."""

    normalized = normalize_inputs(inputs)

    required = {
        QuantificationMethod.BOTTOM_UP,
        QuantificationMethod.MEASUREMENT,
        QuantificationMethod.TOP_DOWN,
    }

    available = {
        item.method
        for item in normalized
    }

    missing = required - available

    if missing:
        names = ", ".join(
            method.value
            for method in sorted(
                missing,
                key=lambda value: value.value,
            )
        )

        raise ValueError(
            f"missing quantification methods: {names}"
        )


def prepare_inputs(
    estimates: Iterable[EmissionEstimate],
) -> tuple[ReconciliationInput, ...]:
    """Prepare Layer 7 estimates for Layer 9 reconciliation."""

    return tuple(
        from_emission_estimate(estimate)
        for estimate in estimates
    )
