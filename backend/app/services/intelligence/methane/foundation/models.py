from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class FrameworkStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    DRAFT = "draft"


@dataclass(frozen=True)
class RegulatoryFramework:
    """Canonical regulatory, methodological, or standards framework."""

    framework_id: str
    name: str
    jurisdiction: str
    authority: str
    version: str = ""
    effective_date: date | None = None
    status: FrameworkStatus = FrameworkStatus.ACTIVE
    description: str = ""

    def __post_init__(self) -> None:
        if not self.framework_id.strip():
            raise ValueError("framework_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.jurisdiction.strip():
            raise ValueError("jurisdiction is required")

        if not self.authority.strip():
            raise ValueError("authority is required")


@dataclass(frozen=True)
class RegulatoryRequirement:
    """A requirement that can be traced to a regulatory framework."""

    requirement_id: str
    framework_id: str
    title: str
    description: str
    requirement_code: str = ""
    mandatory: bool = True
    applicability: str = ""
    evidence_types: tuple[str, ...] = ()
    reporting_frequency: str = ""

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("requirement_id is required")

        if not self.framework_id.strip():
            raise ValueError("framework_id is required")

        if not self.title.strip():
            raise ValueError("title is required")

        if not self.description.strip():
            raise ValueError("description is required")


@dataclass(frozen=True)
class MethodologyReference:
    """Reference to an emissions or MRV methodology."""

    methodology_id: str
    name: str
    publisher: str
    version: str = ""
    scope: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.methodology_id.strip():
            raise ValueError("methodology_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.publisher.strip():
            raise ValueError("publisher is required")


@dataclass(frozen=True)
class ApplicabilityRule:
    """Defines when a framework or requirement applies."""

    rule_id: str
    framework_id: str
    condition: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id is required")

        if not self.framework_id.strip():
            raise ValueError("framework_id is required")

        if not self.condition.strip():
            raise ValueError("condition is required")
