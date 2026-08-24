from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class LineageStep:
    """
    Represents one transformation or processing step applied
    to an extracted value.
    """

    operation: str
    input_value: Any
    output_value: Any
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.operation or not self.operation.strip():
            raise ValueError("operation is required")

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware"
            )

    @property
    def is_utc(self) -> bool:
        """Return True when the timestamp is UTC."""
        return (
            self.timestamp.utcoffset() is not None
            and self.timestamp.utcoffset().total_seconds() == 0
        )


@dataclass
class LineageRecord:
    """
    Complete lineage information for one extracted field.
    """

    field_name: str
    source_url: str
    raw_value: Any
    final_value: Any
    steps: list[LineageStep] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.field_name or not self.field_name.strip():
            raise ValueError("field_name is required")

        if not self.source_url or not self.source_url.strip():
            raise ValueError("source_url is required")

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

    def add_step(
        self,
        operation: str,
        input_value: Any,
        output_value: Any,
        *,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> LineageStep:
        """
        Add a transformation step to the lineage.
        """

        step = LineageStep(
            operation=operation,
            input_value=input_value,
            output_value=output_value,
            timestamp=(
                timestamp
                if timestamp is not None
                else datetime.now(timezone.utc)
            ),
            metadata=metadata or {},
        )

        self.steps.append(step)
        self.final_value = output_value

        return step

    @property
    def step_count(self) -> int:
        """Return the number of lineage steps."""
        return len(self.steps)

    @property
    def operations(self) -> list[str]:
        """Return operations in execution order."""
        return [
            step.operation
            for step in self.steps
        ]

    @property
    def source(self) -> str:
        """Return the source URL."""
        return self.source_url

    def get_step(
        self,
        operation: str,
    ) -> LineageStep | None:
        """
        Return the first step matching an operation.
        """

        for step in self.steps:
            if step.operation == operation:
                return step

        return None


def create_lineage(
    field_name: str,
    source_url: str,
    raw_value: Any,
    *,
    metadata: dict[str, Any] | None = None,
) -> LineageRecord:
    """
    Create a new lineage record.

    The initial final value is the raw value. Subsequent
    processing steps update final_value.
    """

    return LineageRecord(
        field_name=field_name,
        source_url=source_url,
        raw_value=raw_value,
        final_value=raw_value,
        metadata=metadata or {},
    )


def record_lineage_step(
    lineage: LineageRecord,
    operation: str,
    input_value: Any,
    output_value: Any,
    *,
    metadata: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> LineageStep:
    """
    Record one processing operation against a lineage record.
    """

    return lineage.add_step(
        operation=operation,
        input_value=input_value,
        output_value=output_value,
        metadata=metadata,
        timestamp=timestamp,
    )


def build_lineage(
    field_name: str,
    source_url: str,
    raw_value: Any,
    steps: list[dict[str, Any]] | None = None,
    *,
    metadata: dict[str, Any] | None = None,
) -> LineageRecord:
    """
    Build a complete lineage record from a raw value and
    an optional sequence of transformation steps.
    """

    lineage = create_lineage(
        field_name=field_name,
        source_url=source_url,
        raw_value=raw_value,
        metadata=metadata,
    )

    for step in steps or []:
        record_lineage_step(
            lineage,
            operation=step["operation"],
            input_value=step["input_value"],
            output_value=step["output_value"],
            metadata=step.get("metadata"),
            timestamp=step.get("timestamp"),
        )

    return lineage