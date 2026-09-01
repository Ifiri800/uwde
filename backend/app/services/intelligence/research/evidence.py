from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.services.intelligence.domain.evidence import Evidence


@dataclass(frozen=True)
class ResearchEvidenceSet:
    """Collection of evidence assembled for a market research project."""

    items: tuple[Evidence, ...] = ()

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        return tuple(item.evidence_id for item in self.items)

    def add(self, evidence: Evidence) -> "ResearchEvidenceSet":
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence must be an Evidence instance")

        if evidence.evidence_id in self.evidence_ids:
            return self

        return ResearchEvidenceSet(
            items=self.items + (evidence,)
        )


@dataclass(frozen=True)
class ResearchFinding:
    """A research finding explicitly supported by evidence."""

    finding_id: str
    topic: str
    statement: str
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("finding_id is required")

        if not self.topic.strip():
            raise ValueError("topic is required")

        if not self.statement.strip():
            raise ValueError("statement is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )
