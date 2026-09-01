from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IPCCMethod(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


@dataclass(frozen=True)
class IPCCMethodology:
    """
    IPCC methodology classification used by methane quantification.
    """

    method: IPCCMethod
    name: str
    description: str = ""


def validate_ipcc_methodology(
    methodology: IPCCMethodology,
) -> IPCCMethodology:
    """
    Validate an IPCC methodology definition.
    """

    if not isinstance(
        methodology,
        IPCCMethodology,
    ):
        raise ValueError(
            "methodology must be an IPCCMethodology instance"
        )

    if not methodology.name.strip():
        raise ValueError("name is required")

    return methodology


def create_ipcc_methodology(
    method: IPCCMethod,
    name: str,
    description: str = "",
) -> IPCCMethodology:
    """
    Create and validate an IPCC methodology definition.
    """

    methodology = IPCCMethodology(
        method=method,
        name=name,
        description=description,
    )

    return validate_ipcc_methodology(methodology)
