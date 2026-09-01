from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerGroup:
    name: str
    description: str
    needs: tuple[str, ...] = ()
    demand_signals: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class CustomerAnalysisResult:
    groups: tuple[CustomerGroup, ...]
    demand_drivers: tuple[str, ...]
    unmet_needs: tuple[str, ...]


def analyze_customers(
    groups: list[CustomerGroup],
    *,
    demand_drivers: list[str] | None = None,
    unmet_needs: list[str] | None = None,
) -> CustomerAnalysisResult:

    names: set[str] = set()

    for group in groups:
        if not group.name.strip():
            raise ValueError("customer group name is required")

        key = group.name.casefold()

        if key in names:
            raise ValueError(
                f"Duplicate customer group: {group.name}"
            )

        names.add(key)

    return CustomerAnalysisResult(
        groups=tuple(groups),
        demand_drivers=tuple(demand_drivers or []),
        unmet_needs=tuple(unmet_needs or []),
    )
