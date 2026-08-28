from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    """
    A verifiable observation supporting an intelligence entity,
    field, relationship, or signal.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1, max_length=200)

    source_url: HttpUrl
    source_id: str | None = Field(
        default=None,
        max_length=200,
    )

    entity_id: str | None = Field(
        default=None,
        max_length=200,
    )

    field_name: str | None = Field(
        default=None,
        max_length=300,
    )

    observed_value: Any

    extraction_method: str | None = Field(
        default=None,
        max_length=200,
    )

    observed_at: datetime = Field(
        default_factory=utc_now,
    )

    extracted_at: datetime = Field(
        default_factory=utc_now,
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    lineage_reference: str | None = Field(
        default=None,
        max_length=500,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @property
    def source(self) -> str:
        """Return the canonical source URL."""
        return str(self.source_url)

    @property
    def has_lineage(self) -> bool:
        """Return whether this evidence references UWDE lineage."""
        return bool(self.lineage_reference)
