from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .models import IngestionMetadata


def validate_metadata(metadata: IngestionMetadata) -> None:
    if not isinstance(metadata, IngestionMetadata):
        raise TypeError("metadata must be an IngestionMetadata instance")


def enrich_metadata(
    metadata: IngestionMetadata,
    **attributes: object,
) -> IngestionMetadata:
    merged = dict(metadata.attributes)
    merged.update(attributes)

    return replace(metadata, attributes=merged)


def with_quality_note(
    metadata: IngestionMetadata,
    quality_notes: str,
) -> IngestionMetadata:
    if not quality_notes.strip():
        raise ValueError("quality_notes cannot be empty")

    return replace(metadata, quality_notes=quality_notes)


def metadata_age_seconds(
    metadata: IngestionMetadata,
    *,
    now: datetime,
) -> float:
    if not isinstance(now, datetime):
        raise TypeError("now must be a datetime")

    return (now - metadata.acquired_at).total_seconds()
