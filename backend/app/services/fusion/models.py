from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class FusionSource:
    """
    Identifies a source contributing data to a fusion operation.
    """

    source_id: str
    source_url: str | None = None
    source_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id cannot be empty")


@dataclass(frozen=True)
class FusionObservation:
    """
    A single normalized observation available for fusion.
    """

    field_name: str
    value: Any
    source: FusionSource
    confidence: float | None = None
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name cannot be empty")

        if self.confidence is not None and not (
            0.0 <= self.confidence <= 1.0
        ):
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass
class FusionField:
    """
    Represents the fused value of one logical field.
    """

    field_name: str
    value: Any = None
    observations: list[FusionObservation] = field(
        default_factory=list
    )
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass
class FusionRecord:
    """
    Represents one logical entity assembled from multiple sources.
    """

    record_id: str
    fields: dict[str, FusionField] = field(
        default_factory=dict
    )
    sources: list[FusionSource] = field(
        default_factory=list
    )
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id cannot be empty")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )


@dataclass
class FusionResult:
    """
    Result returned by a data fusion operation.
    """

    records: list[FusionRecord] = field(
        default_factory=list
    )
    observations_processed: int = 0
    sources_processed: int = 0
    conflicts_detected: int = 0
    duplicates_detected: int = 0
    requires_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.observations_processed < 0:
            raise ValueError(
                "observations_processed cannot be negative"
            )

        if self.sources_processed < 0:
            raise ValueError(
                "sources_processed cannot be negative"
            )

        if self.conflicts_detected < 0:
            raise ValueError(
                "conflicts_detected cannot be negative"
            )

        if self.duplicates_detected < 0:
            raise ValueError(
                "duplicates_detected cannot be negative"
            )
