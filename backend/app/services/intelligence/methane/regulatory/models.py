from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class RegulatorySourceType(str, Enum):
    REGULATION = "regulation"
    GUIDANCE = "guidance"
    TEMPLATE = "template"
    METHODOLOGY = "methodology"
    STANDARD = "standard"
    FRAMEWORK = "framework"


class SourceStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    DRAFT = "draft"


@dataclass(frozen=True)
class RegulatorySource:
    """Authoritative source used to establish an MRV requirement."""

    source_id: str
    title: str
    publisher: str
    source_type: RegulatorySourceType
    jurisdiction: str = ""
    version: str = ""
    publication_date: date | None = None
    effective_date: date | None = None
    status: SourceStatus = SourceStatus.ACTIVE
    canonical_url: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id is required")

        if not self.title.strip():
            raise ValueError("title is required")

        if not self.publisher.strip():
            raise ValueError("publisher is required")


@dataclass(frozen=True)
class RequirementTrace:
    """Traceability between a requirement and its authoritative source."""

    trace_id: str
    requirement_id: str
    source_id: str
    reference: str = ""
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.trace_id.strip():
            raise ValueError("trace_id is required")

        if not self.requirement_id.strip():
            raise ValueError("requirement_id is required")

        if not self.source_id.strip():
            raise ValueError("source_id is required")
