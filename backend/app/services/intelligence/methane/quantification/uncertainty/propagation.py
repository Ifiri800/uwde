from __future__ import annotations

from math import sqrt
from typing import Iterable

from .models import UncertaintyComponent


def combine_absolute_uncertainties(
    uncertainties: Iterable[float],
) -> float:
    """
    Combine independent absolute uncertainties using
    root-sum-of-squares propagation.
    """

    values = tuple(uncertainties)

    for value in values:
        if value < 0:
            raise ValueError(
                "uncertainties cannot be negative"
            )

    return sqrt(
        sum(value ** 2 for value in values)
    )


def combine_components(
    components: Iterable[UncertaintyComponent],
) -> float:
    """
    Combine independent uncertainty components expressed
    in compatible absolute units.
    """

    components = tuple(components)

    return combine_absolute_uncertainties(
        component.standard_deviation
        if component.standard_deviation is not None
        else component.value
        for component in components
    )


def propagate_product_uncertainty(
    value: float,
    relative_uncertainties: Iterable[float],
) -> float:
    """
    Propagate independent relative uncertainties through
    a multiplicative calculation.
    """

    if value < 0:
        raise ValueError(
            "value cannot be negative"
        )

    uncertainties = tuple(relative_uncertainties)

    for uncertainty in uncertainties:
        if uncertainty < 0:
            raise ValueError(
                "relative uncertainties cannot be negative"
            )

    combined_relative = combine_absolute_uncertainties(
        uncertainties
    )

    return value * combined_relative


def relative_uncertainty(
    value: float,
    uncertainty: float,
) -> float:
    """
    Return uncertainty relative to the measured or estimated value.
    """

    if value <= 0:
        raise ValueError(
            "value must be greater than zero"
        )

    if uncertainty < 0:
        raise ValueError(
            "uncertainty cannot be negative"
        )

    return uncertainty / value
