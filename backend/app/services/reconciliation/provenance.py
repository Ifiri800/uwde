from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Provenance:
    """
    Records the origin and extraction context of a value.
    """

    source_url: str
    source_id: str | None = None
    field_name: str | None = None
    extraction_method: str | None = None
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_url:
            raise ValueError("source_url cannot be empty")

        if self.confidence is not None and not (
            0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass(frozen=True)
class SourcedValue:
    """
    Associates an extracted value with its provenance.
    """

    value: Any
    provenance: Provenance

    @property
    def confidence(self) -> float | None:
        return self.provenance.confidence


def create_provenance(
    source_url: str,
    *,
    source_id: str | None = None,
    field_name: str | None = None,
    extraction_method: str | None = None,
    confidence: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> Provenance:
    """
    Create a provenance record using the current UTC timestamp.
    """

    return Provenance(
        source_url=source_url,
        source_id=source_id,
        field_name=field_name,
        extraction_method=extraction_method,
        confidence=confidence,
        metadata=metadata or {},
    )


def attach_provenance(
    value: Any,
    provenance: Provenance,
) -> SourcedValue:
    """
    Attach provenance information to an extracted value.
    """

    return SourcedValue(
        value=value,
        provenance=provenance,
    )