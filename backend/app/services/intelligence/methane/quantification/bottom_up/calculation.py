from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BottomUpCalculation:
    """
    Input data for a bottom-up methane emissions calculation.
    """

    activity: float
    emission_factor: float

    def __post_init__(self) -> None:
        if not isinstance(self.activity, (int, float)):
            raise ValueError("activity must be numeric")

        if not isinstance(self.emission_factor, (int, float)):
            raise ValueError("emission_factor must be numeric")

        if self.activity < 0:
            raise ValueError("activity cannot be negative")

        if self.emission_factor < 0:
            raise ValueError("emission_factor cannot be negative")


@dataclass(frozen=True)
class BottomUpResult:
    """
    Result of a bottom-up methane emissions calculation.
    """

    activity: float
    emission_factor: float
    methane_emissions: float

    def __post_init__(self) -> None:
        if not isinstance(self.activity, (int, float)):
            raise ValueError("activity must be numeric")

        if not isinstance(self.emission_factor, (int, float)):
            raise ValueError("emission_factor must be numeric")

        if not isinstance(self.methane_emissions, (int, float)):
            raise ValueError("methane_emissions must be numeric")

        if self.activity < 0:
            raise ValueError("activity cannot be negative")

        if self.emission_factor < 0:
            raise ValueError("emission_factor cannot be negative")

        if self.methane_emissions < 0:
            raise ValueError("methane_emissions cannot be negative")


def calculate_bottom_up(
    *,
    calculation: BottomUpCalculation,
) -> BottomUpResult:
    """
    Calculate methane emissions using the bottom-up method.

    Formula:

        methane_emissions = activity * emission_factor
    """

    if not isinstance(calculation, BottomUpCalculation):
        raise ValueError(
            "calculation must be a BottomUpCalculation instance"
        )

    methane_emissions = (
        float(calculation.activity)
        * float(calculation.emission_factor)
    )

    return BottomUpResult(
        activity=calculation.activity,
        emission_factor=calculation.emission_factor,
        methane_emissions=methane_emissions,
    )
