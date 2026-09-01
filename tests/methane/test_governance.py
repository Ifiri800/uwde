from backend.app.services.intelligence.methane.governance.models import (
    AssetBoundary,
    BoundaryType,
    DataGovernanceRule,
    Frequency,
    GovernanceRole,
    LDARStrategy,
    MRVPlan,
    OwnershipType,
    QAQCProcedure,
    RoleType,
    VerificationLevel,
    VerificationProtocol,
)
from backend.app.services.intelligence.methane.governance.validation import (
    validate_mrv_plan,
)


def test_asset_boundary_requires_identity():
    try:
        AssetBoundary(
            asset_id="",
            name="Asset",
            boundary_type=BoundaryType.OPERATIONAL,
            ownership=OwnershipType.OPERATED,
        )
    except ValueError:
        return

    assert False


def test_asset_boundary_valid():
    asset = AssetBoundary(
        asset_id="A-001",
        name="Test Asset",
        boundary_type=BoundaryType.OPERATIONAL,
        ownership=OwnershipType.OPERATED,
    )

    assert asset.asset_id == "A-001"
    assert asset.included is True


def test_governance_role_requires_name():
    try:
        GovernanceRole(
            role=RoleType.MRV_OWNER,
            name="",
        )
    except ValueError:
        return

    assert False


def test_data_rule_requires_owner():
    try:
        DataGovernanceRule(
            data_domain="emissions",
            owner="",
        )
    except ValueError:
        return

    assert False


def test_qa_qc_requires_acceptance_criteria():
    try:
        QAQCProcedure(
            procedure_id="QA-001",
            name="Completeness",
            frequency=Frequency.MONTHLY,
            acceptance_criteria="",
            responsible_role=RoleType.QA_QC_OWNER,
        )
    except ValueError:
        return

    assert False


def test_verification_requires_scope():
    try:
        VerificationProtocol(
            protocol_id="V-001",
            level=VerificationLevel.INTERNAL,
            scope=(),
            evidence_required=("records",),
        )
    except ValueError:
        return


def test_ldar_requires_detection_method():
    try:
        LDARStrategy(
            strategy_id="LDAR-001",
            detection_frequency=Frequency.MONTHLY,
            detection_methods=(),
        )
    except ValueError:
        return


def test_empty_plan_is_invalid():
    plan = MRVPlan(
        plan_id="MRV-001",
        version="1.0",
    )

    result = validate_mrv_plan(plan)

    assert result.valid is False
    assert "organizational boundary is required" in result.errors


def test_complete_plan_is_valid():
    asset = AssetBoundary(
        asset_id="A-001",
        name="Test Asset",
        boundary_type=BoundaryType.OPERATIONAL,
        ownership=OwnershipType.OPERATED,
    )

    role_types = (
        RoleType.MRV_OWNER,
        RoleType.DATA_OWNER,
        RoleType.QA_QC_OWNER,
        RoleType.VERIFIER,
        RoleType.LDAR_MANAGER,
    )

    roles = tuple(
        GovernanceRole(role=role, name=role.value)
        for role in role_types
    )

    plan = MRVPlan(
        plan_id="MRV-001",
        version="1.0",
        organizational_boundary=(asset,),
        operational_boundary=(asset,),
        roles=roles,
        data_rules=(
            DataGovernanceRule(
                data_domain="emissions",
                owner="data-owner",
            ),
        ),
        qa_qc_procedures=(
            QAQCProcedure(
                procedure_id="QA-001",
                name="Completeness",
                frequency=Frequency.MONTHLY,
                acceptance_criteria="All required records present",
                responsible_role=RoleType.QA_QC_OWNER,
            ),
        ),
        verification_protocols=(
            VerificationProtocol(
                protocol_id="V-001",
                level=VerificationLevel.INDEPENDENT,
                scope=("emissions",),
                evidence_required=("measurements", "calculations"),
                independence_required=True,
            ),
        ),
        ldar_strategy=LDARStrategy(
            strategy_id="LDAR-001",
            detection_frequency=Frequency.MONTHLY,
            detection_methods=("OGI", "sensor"),
        ),
        objectives=["Maintain methane MRV integrity"],
    )

    result = validate_mrv_plan(plan)

    assert result.valid is True
    assert result.errors == ()
