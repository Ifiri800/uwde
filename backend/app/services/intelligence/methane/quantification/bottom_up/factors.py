from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EmissionFactor:
    """
    Emission factor used for bottom-up methane quantification.
    """

    factor_id: str
    value: float
    unit: str
    source: str
    methodology: str | None = None
    tier: str | None = None
    uncertainty: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_emission_factor(
    factor: EmissionFactor,
) -> EmissionFactor:
    """
    Validate an emission factor.

    Returns the original immutable factor when valid.
    """

    if not isinstance(factor, EmissionFactor):
        raise ValueError(
            "factor must be an EmissionFactor instance"
        )

    if not factor.factor_id.strip():
        raise ValueError("factor_id is required")

    if factor.value < 0:
        raise ValueError("value cannot be negative")

    if not factor.unit.strip():
        raise ValueError("unit is required")

    if not factor.source.strip():
        raise ValueError("source is required")

    if factor.uncertainty is not None:
        if factor.uncertainty < 0:
            raise ValueError(
                "uncertainty cannot be negative"
            )

    return factor
