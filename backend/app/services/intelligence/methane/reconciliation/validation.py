from __future__ import annotations

from collections.abc import Iterable

from .inputs import validate_input_compatibility
from .models import ReconciliationInput


def validate_reconciliation_inputs(
    inputs: Iterable[ReconciliationInput],
) -> list[str]:
    """Validate all Layer 9 reconciliation inputs."""

    values = tuple(inputs)

    errors = validate_input_compatibility(values)

    for item in values:
        if item.value < 0:
            errors.append(
                f"{item.estimate_id}: value cannot be negative"
            )

        if (
            item.uncertainty is not None
            and item.uncertainty < 0
        ):
            errors.append(
                f"{item.estimate_id}: uncertainty cannot be negative"
            )

    return errors
