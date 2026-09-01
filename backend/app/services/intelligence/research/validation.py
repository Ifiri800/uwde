from __future__ import annotations

from dataclasses import dataclass

from .evidence import ResearchEvidenceSet
from .models import MarketResearchProject


@dataclass(frozen=True)
class ResearchValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate_research_project(
    project: MarketResearchProject,
) -> ResearchValidationResult:
    """Run deterministic structural quality checks."""

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(project, MarketResearchProject):
        raise TypeError(
            "project must be a MarketResearchProject"
        )

    specification = project.specification

    if not specification.objective.strip():
        errors.append("Research objective is missing.")

    if not specification.market_name.strip():
        errors.append("Market name is missing.")

    if (
        specification.base_year is not None
        and specification.forecast_year is not None
        and specification.forecast_year
        < specification.base_year
    ):
        errors.append(
            "Forecast year cannot be earlier than base year."
        )

    if not project.evidence:
        warnings.append(
            "Research project contains no evidence."
        )

    if not project.findings:
        warnings.append(
            "Research project contains no findings."
        )

    return ResearchValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def validate_evidence(
    evidence: ResearchEvidenceSet,
) -> ResearchValidationResult:
    """Validate the structural integrity of an evidence set."""

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(evidence, ResearchEvidenceSet):
        raise TypeError(
            "evidence must be a ResearchEvidenceSet"
        )

    seen: set[str] = set()

    for item in evidence.items:
        if item.evidence_id in seen:
            errors.append(
                f"Duplicate evidence ID: {item.evidence_id}"
            )

        seen.add(item.evidence_id)

        if item.confidence < 0.70:
            warnings.append(
                f"Low-confidence evidence: {item.evidence_id}"
            )

    return ResearchValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
