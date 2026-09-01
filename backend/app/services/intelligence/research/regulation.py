from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegulatoryRequirement:
    name: str
    jurisdiction: str
    description: str
    status: str = "unknown"
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegulatoryAnalysisResult:
    requirements: tuple[RegulatoryRequirement, ...]
    jurisdictions: tuple[str, ...]


def analyze_regulation(
    requirements: list[RegulatoryRequirement],
) -> RegulatoryAnalysisResult:

    jurisdictions: list[str] = []

    for requirement in requirements:
        if not requirement.name.strip():
            raise ValueError(
                "regulatory requirement name is required"
            )

        if not requirement.jurisdiction.strip():
            raise ValueError(
                "jurisdiction is required"
            )

        if requirement.jurisdiction not in jurisdictions:
            jurisdictions.append(
                requirement.jurisdiction
            )

    return RegulatoryAnalysisResult(
        requirements=tuple(requirements),
        jurisdictions=tuple(jurisdictions),
    )
