from __future__ import annotations

from .models import (
    AssetBoundary,
    DataGovernanceRule,
    GovernanceRole,
    LDARStrategy,
    MRVPlan,
    QAQCProcedure,
    VerificationProtocol,
)
from .validation import validate_mrv_plan


def create_mrv_plan(
    *,
    plan_id: str,
    version: str,
    organizational_boundary: tuple[AssetBoundary, ...],
    operational_boundary: tuple[AssetBoundary, ...],
    roles: tuple[GovernanceRole, ...],
    data_rules: tuple[DataGovernanceRule, ...],
    qa_qc_procedures: tuple[QAQCProcedure, ...],
    verification_protocols: tuple[VerificationProtocol, ...],
    ldar_strategy: LDARStrategy,
    objectives: list[str] | None = None,
) -> MRVPlan:
    plan = MRVPlan(
        plan_id=plan_id,
        version=version,
        organizational_boundary=organizational_boundary,
        operational_boundary=operational_boundary,
        roles=roles,
        data_rules=data_rules,
        qa_qc_procedures=qa_qc_procedures,
        verification_protocols=verification_protocols,
        ldar_strategy=ldar_strategy,
        objectives=objectives or [],
    )

    validation = validate_mrv_plan(plan)

    if not validation.valid:
        raise ValueError(
            "invalid MRV plan: " + "; ".join(validation.errors)
        )

    return plan
