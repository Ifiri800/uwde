from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class BoundaryType(str, Enum):
    ORGANIZATIONAL = "organizational"
    OPERATIONAL = "operational"


class OwnershipType(str, Enum):
    OPERATED = "operated"
    NON_OPERATED = "non_operated"
    JOINT_VENTURE = "joint_venture"
    CONTRACTED = "contracted"
    UNKNOWN = "unknown"


class RoleType(str, Enum):
    MRV_OWNER = "mrv_owner"
    DATA_OWNER = "data_owner"
    QA_QC_OWNER = "qa_qc_owner"
    VERIFIER = "verifier"
    LDAR_MANAGER = "ldar_manager"
    ASSET_MANAGER = "asset_manager"
    EMISSIONS_ANALYST = "emissions_analyst"


class Frequency(str, Enum):
    CONTINUOUS = "continuous"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT_BASED = "event_based"


class VerificationLevel(str, Enum):
    INTERNAL = "internal"
    SECOND_PARTY = "second_party"
    INDEPENDENT = "independent"


@dataclass(frozen=True)
class AssetBoundary:
    asset_id: str
    name: str
    boundary_type: BoundaryType
    ownership: OwnershipType
    included: bool = True

    def __post_init__(self) -> None:
        if not self.asset_id.strip():
            raise ValueError("asset_id is required")
        if not self.name.strip():
            raise ValueError("name is required")


@dataclass(frozen=True)
class GovernanceRole:
    role: RoleType
    name: str
    responsibilities: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")


@dataclass(frozen=True)
class DataGovernanceRule:
    data_domain: str
    owner: str
    retention_days: int | None = None
    version_controlled: bool = True
    audit_required: bool = True

    def __post_init__(self) -> None:
        if not self.data_domain.strip():
            raise ValueError("data_domain is required")
        if not self.owner.strip():
            raise ValueError("owner is required")
        if self.retention_days is not None and self.retention_days < 1:
            raise ValueError("retention_days must be at least 1")


@dataclass(frozen=True)
class QAQCProcedure:
    procedure_id: str
    name: str
    frequency: Frequency
    acceptance_criteria: str
    responsible_role: RoleType
    mandatory: bool = True

    def __post_init__(self) -> None:
        if not self.procedure_id.strip():
            raise ValueError("procedure_id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.acceptance_criteria.strip():
            raise ValueError("acceptance_criteria is required")


@dataclass(frozen=True)
class VerificationProtocol:
    protocol_id: str
    level: VerificationLevel
    scope: Tuple[str, ...]
    evidence_required: Tuple[str, ...]
    independence_required: bool = False

    def __post_init__(self) -> None:
        if not self.protocol_id.strip():
            raise ValueError("protocol_id is required")
        if not self.scope:
            raise ValueError("scope is required")
        if not self.evidence_required:
            raise ValueError("evidence_required is required")


@dataclass(frozen=True)
class LDARStrategy:
    strategy_id: str
    detection_frequency: Frequency
    detection_methods: Tuple[str, ...]
    confirmation_required: bool = True
    quantification_required: bool = True
    repair_required: bool = True
    remeasurement_required: bool = True
    verification_required: bool = True

    def __post_init__(self) -> None:
        if not self.strategy_id.strip():
            raise ValueError("strategy_id is required")
        if not self.detection_methods:
            raise ValueError("detection_methods is required")


@dataclass
class MRVPlan:
    plan_id: str
    version: str
    organizational_boundary: Tuple[AssetBoundary, ...] = ()
    operational_boundary: Tuple[AssetBoundary, ...] = ()
    roles: Tuple[GovernanceRole, ...] = ()
    data_rules: Tuple[DataGovernanceRule, ...] = ()
    qa_qc_procedures: Tuple[QAQCProcedure, ...] = ()
    verification_protocols: Tuple[VerificationProtocol, ...] = ()
    ldar_strategy: LDARStrategy | None = None
    objectives: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.plan_id.strip():
            raise ValueError("plan_id is required")
        if not self.version.strip():
            raise ValueError("version is required")

    @property
    def asset_count(self) -> int:
        return len(
            {
                asset.asset_id
                for asset in (
                    self.organizational_boundary
                    + self.operational_boundary
                )
            }
        )

    @property
    def role_count(self) -> int:
        return len(self.roles)

    @property
    def qa_qc_count(self) -> int:
        return len(self.qa_qc_procedures)

    @property
    def verification_count(self) -> int:
        return len(self.verification_protocols)
