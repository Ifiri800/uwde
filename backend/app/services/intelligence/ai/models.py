from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIObservation:
    """A structured intelligence observation supplied to the AI layer."""

    source: str
    category: str
    statement: str
    confidence: float = 1.0
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("source is required")

        if not self.category.strip():
            raise ValueError("category is required")

        if not self.statement.strip():
            raise ValueError("statement is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class AIContext:
    """Normalized intelligence context presented to the AI layer."""

    observations: tuple[AIObservation, ...] = ()
    entities: tuple[dict[str, Any], ...] = ()
    signals: tuple[dict[str, Any], ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def observation_count(self) -> int:
        return len(self.observations)


@dataclass(frozen=True)
class AIReasoning:
    """Reasoning result produced from an AI context."""

    conclusion: str
    rationale: tuple[str, ...] = ()
    confidence: float = 0.0
    supporting_observations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.conclusion.strip():
            raise ValueError("conclusion is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class AISynthesis:
    """Human-readable synthesis of multiple intelligence outputs."""

    summary: str
    key_findings: tuple[str, ...] = ()
    implications: tuple[str, ...] = ()
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("summary is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class AIRecommendation:
    """Decision-support recommendation produced by the AI layer."""

    recommendation: str
    rationale: tuple[str, ...] = ()
    priority: str = "medium"
    confidence: float = 0.0
    actions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.recommendation.strip():
            raise ValueError("recommendation is required")

        if self.priority not in {"low", "medium", "high", "critical"}:
            raise ValueError(
                "priority must be one of: low, medium, high, critical"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
