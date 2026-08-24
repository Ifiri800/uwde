from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ReconciliationConflict:
    """
    Represents a disagreement between source values during reconciliation.

    This model is retained for backwards compatibility with older UWDE
    callers. The active reconciliation pipeline uses Conflict from
    conflicts.py.
    """

    field_name: str
    values: list[Any] = field(default_factory=list)
    sources: list[Any] = field(default_factory=list)
    message: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name is required")


@dataclass
class ReconciliationResolution:
    """
    Represents the result of resolving a reconciliation conflict.

    The model retains compatibility with both the current
    reconciliation pipeline and older UWDE callers.
    """

    field_name: str
    value: Any = None
    strategy: str = "default"
    confidence: Optional[float] = None
    reason: Optional[str] = None
    requires_review: bool = False

    # Compatibility fields used by the active resolver.
    conflict: Any = None
    selected_observation: Any = None

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name is required")

        self.requires_review = bool(
            self.requires_review
        )

    @property
    def selected_value(self) -> Any:
        """
        Backwards-compatible alias for value.
        """
        return self.value

    @property
    def resolved(self) -> bool:
        """
        Return True when a concrete observation was selected
        and manual review is not required.
        """
        return (
            self.selected_observation is not None
            and not self.requires_review
        )


@dataclass
class ReconciliationUncertainty:
    """
    Represents uncertainty associated with a reconciled value.
    """

    field_name: str
    confidence: Optional[float] = None
    reason: Optional[str] = None
    sources: list[Any] = field(default_factory=list)
    uncertainty: Optional[float] = None
    supporting_sources: int = 0
    conflicting_sources: int = 0
    level: Optional[str] = None
    requires_review: bool = False

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError("field_name is required")

        self.supporting_sources = max(
            0,
            int(self.supporting_sources),
        )

        self.conflicting_sources = max(
            0,
            int(self.conflicting_sources),
        )

        self.requires_review = bool(
            self.requires_review
        )


@dataclass
class ReconciliationResult:
    """
    Canonical result of the UWDE reconciliation process.

    This is the single ReconciliationResult model used by the
    reconciliation pipeline and lineage subsystem.
    """

    values: dict[str, Any]
    conflicts: list[Any] = field(default_factory=list)
    resolutions: list[Any] = field(default_factory=list)
    requires_review: bool = False
    uncertainties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.values is None:
            self.values = {}

        if self.conflicts is None:
            self.conflicts = []

        if self.resolutions is None:
            self.resolutions = []

        if self.uncertainties is None:
            self.uncertainties = {}

        self.requires_review = bool(
            self.requires_review
        )

    @property
    def conflict_count(self) -> int:
        """
        Return the number of detected conflicts.
        """
        return len(self.conflicts)

    @property
    def resolved_count(self) -> int:
        """
        Return the number of successfully resolved conflicts.
        """
        return sum(
            bool(
                getattr(
                    resolution,
                    "resolved",
                    False,
                )
            )
            for resolution in self.resolutions
        )

    @property
    def unresolved_count(self) -> int:
        """
        Return the number of resolutions requiring review.
        """
        return sum(
            bool(
                getattr(
                    resolution,
                    "requires_review",
                    False,
                )
            )
            for resolution in self.resolutions
        )


@dataclass
class ReconciliationSource:
    """
    A source participating in reconciliation.
    """

    source_id: Optional[str] = None
    url: Optional[str] = None
    field_name: Optional[str] = None
    value: Any = None
    extracted_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ReconciliationStep:
    """
    Records a step in the reconciliation process.
    """

    step: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    input_value: Any = None
    output_value: Any = None


@dataclass
class ReconciliationLineage:
    """
    Complete lineage for a reconciled field.
    """

    field_name: str
    sources: list[Any] = field(
        default_factory=list
    )
    final_value: Any = None
    steps: list[Any] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.field_name:
            raise ValueError(
                "field_name is required"
            )

        if self.sources is None:
            self.sources = []

        if self.steps is None:
            self.steps = []

        if self.metadata is None:
            self.metadata = {}