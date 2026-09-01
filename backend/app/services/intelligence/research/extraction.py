from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.services.intelligence.domain.evidence import Evidence
from .evidence import ResearchEvidenceSet, ResearchFinding


@dataclass(frozen=True)
class ExtractionObservation:
    evidence_id: str
    source_url: str
    observed_value: Any
    entity_id: str | None = None
    field_name: str | None = None
    extraction_method: str | None = None
    confidence: float = 1.0
    source_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class ExtractionResult:
    evidence: ResearchEvidenceSet
    findings: tuple[ResearchFinding, ...]
    observation_count: int


def extract_observation(
    observation: ExtractionObservation,
) -> Evidence:
    if not observation.evidence_id.strip():
        raise ValueError("evidence_id is required")

    if not observation.source_url.strip():
        raise ValueError("source_url is required")

    if not 0.0 <= observation.confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0.0 and 1.0"
        )

    return Evidence(
        evidence_id=observation.evidence_id,
        source_url=observation.source_url,
        source_id=observation.source_id,
        entity_id=observation.entity_id,
        field_name=observation.field_name,
        observed_value=observation.observed_value,
        extraction_method=observation.extraction_method,
        confidence=observation.confidence,
        metadata=dict(observation.metadata or {}),
    )


def extract_observations(
    observations: list[ExtractionObservation],
) -> ExtractionResult:
    evidence_items: list[Evidence] = []

    seen: set[str] = set()

    for observation in observations:
        if observation.evidence_id in seen:
            raise ValueError(
                f"Duplicate evidence ID: {observation.evidence_id}"
            )

        seen.add(observation.evidence_id)

        evidence_items.append(
            extract_observation(observation)
        )

    evidence_set = ResearchEvidenceSet(
        items=evidence_items,
    )

    return ExtractionResult(
        evidence=evidence_set,
        findings=(),
        observation_count=len(evidence_items),
    )


def create_finding(
    *,
    finding_id: str,
    statement: str,
    evidence_ids: tuple[str, ...] = (),
    confidence: float = 0.0,
) -> ResearchFinding:
    if not finding_id.strip():
        raise ValueError("finding_id is required")

    if not statement.strip():
        raise ValueError("statement is required")

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0.0 and 1.0"
        )

    return ResearchFinding(
        finding_id=finding_id,
        statement=statement,
        evidence_ids=evidence_ids,
        confidence=confidence,
    )
