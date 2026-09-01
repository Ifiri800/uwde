from __future__ import annotations

from dataclasses import dataclass

from .models import MRVPlan
from .roles import has_required_roles


@dataclass(frozen=True)
class GovernanceValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_mrv_plan(
    plan: MRVPlan,
) -> GovernanceValidationResult:
    if not isinstance(plan, MRVPlan):
        raise TypeError("plan must be an MRVPlan")

    errors: list[str] = []
    warnings: list[str] = []

    if not plan.organizational_boundary:
        errors.append("organizational boundary is required")

    if not plan.operational_boundary:
        errors.append("operational boundary is required")

    if not plan.roles:
        errors.append("governance roles are required")
    elif not has_required_roles(plan.roles):
        errors.append("required governance roles are incomplete")

    if not plan.data_rules:
        errors.append("data governance rules are required")

    if not plan.qa_qc_procedures:
        errors.append("QA/QC procedures are required")

    if not plan.verification_protocols:
        errors.append("verification protocols are required")

    if plan.ldar_strategy is None:
        errors.append("LDAR strategy is required")

    if not plan.objectives:
        warnings.append("MRV plan has no stated objectives")

    return GovernanceValidationResult(
        valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
