from __future__ import annotations

from dataclasses import dataclass

from .models import (
    ApplicabilityRule,
    MethodologyReference,
    RegulatoryFramework,
    RegulatoryRequirement,
)


@dataclass(frozen=True)
class FoundationValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


def validate_framework(
    framework: RegulatoryFramework,
) -> FoundationValidationResult:
    errors: list[str] = []

    if not framework.framework_id.strip():
        errors.append("framework_id is required")

    if not framework.name.strip():
        errors.append("name is required")

    if not framework.jurisdiction.strip():
        errors.append("jurisdiction is required")

    if not framework.authority.strip():
        errors.append("authority is required")

    return FoundationValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_requirement(
    requirement: RegulatoryRequirement,
) -> FoundationValidationResult:
    errors: list[str] = []

    if not requirement.requirement_id.strip():
        errors.append("requirement_id is required")

    if not requirement.framework_id.strip():
        errors.append("framework_id is required")

    if not requirement.title.strip():
        errors.append("title is required")

    if not requirement.description.strip():
        errors.append("description is required")

    return FoundationValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_methodology(
    methodology: MethodologyReference,
) -> FoundationValidationResult:
    errors: list[str] = []

    if not methodology.methodology_id.strip():
        errors.append("methodology_id is required")

    if not methodology.name.strip():
        errors.append("name is required")

    if not methodology.publisher.strip():
        errors.append("publisher is required")

    return FoundationValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_applicability_rule(
    rule: ApplicabilityRule,
) -> FoundationValidationResult:
    errors: list[str] = []

    if not rule.rule_id.strip():
        errors.append("rule_id is required")

    if not rule.framework_id.strip():
        errors.append("framework_id is required")

    if not rule.condition.strip():
        errors.append("condition is required")

    return FoundationValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )
