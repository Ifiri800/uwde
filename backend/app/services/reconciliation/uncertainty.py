from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .conflicts import Conflict
from .provenance import SourcedValue


ConfidenceLevel = Literal[
    "very_low",
    "low",
    "medium",
    "high",
    "very_high",
]


@dataclass(frozen=True)
class Uncertainty:
    """
    Represents the uncertainty associated with a reconciled value.
    """

    confidence: float
    uncertainty: float
    supporting_sources: int
    conflicting_sources: int
    level: ConfidenceLevel
    requires_review: bool

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError(
                "uncertainty must be between 0 and 1"
            )

        if self.supporting_sources < 0:
            raise ValueError(
                "supporting_sources cannot be negative"
            )

        if self.conflicting_sources < 0:
            raise ValueError(
                "conflicting_sources cannot be negative"
            )


def _confidence_level(
    confidence: float,
) -> ConfidenceLevel:
    """
    Convert a numeric confidence score into a qualitative level.
    """

    if confidence < 0.20:
        return "very_low"

    if confidence < 0.40:
        return "low"

    if confidence < 0.70:
        return "medium"

    if confidence < 0.90:
        return "high"

    return "very_high"


def calculate_uncertainty(
    confidence: float,
    *,
    supporting_sources: int = 0,
    conflicting_sources: int = 0,
    review_threshold: float = 0.50,
) -> Uncertainty:
    """
    Calculate uncertainty from a confidence score and source evidence.

    Uncertainty is represented as the complement of confidence:

        uncertainty = 1 - confidence

    A result requires review when confidence is below the configured
    review threshold or when conflicting sources are present.
    """

    if not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    if supporting_sources < 0:
        raise ValueError(
            "supporting_sources cannot be negative"
        )

    if conflicting_sources < 0:
        raise ValueError(
            "conflicting_sources cannot be negative"
        )

    if not 0.0 <= review_threshold <= 1.0:
        raise ValueError(
            "review_threshold must be between 0 and 1"
        )

    uncertainty = 1.0 - confidence

    requires_review = (
        confidence < review_threshold
        or conflicting_sources > 0
    )

    return Uncertainty(
        confidence=confidence,
        uncertainty=uncertainty,
        supporting_sources=supporting_sources,
        conflicting_sources=conflicting_sources,
        level=_confidence_level(confidence),
        requires_review=requires_review,
    )


def calculate_source_confidence(
    observations: list[SourcedValue],
) -> float:
    """
    Calculate the average confidence across observations.

    Missing confidence values are treated as zero.
    """

    if not observations:
        return 0.0

    total = sum(
        observation.provenance.confidence or 0.0
        for observation in observations
    )

    return total / len(observations)


def calculate_conflict_uncertainty(
    conflict: Conflict,
) -> Uncertainty:
    """
    Calculate uncertainty for a detected conflict.

    The confidence is based on the strongest observation while the
    existence of competing values forces review.
    """

    observations = list(conflict.observations)

    if not observations:
        return calculate_uncertainty(
            0.0,
            supporting_sources=0,
            conflicting_sources=0,
        )

    strongest_confidence = max(
        observation.provenance.confidence or 0.0
        for observation in observations
    )

    value_groups: dict[str, int] = {}

    for observation in observations:
        key = repr(observation.value)
        value_groups[key] = (
            value_groups.get(key, 0) + 1
        )

    largest_group = max(
        value_groups.values()
    )

    conflicting_sources = (
        len(observations) - largest_group
    )

    return calculate_uncertainty(
        strongest_confidence,
        supporting_sources=largest_group,
        conflicting_sources=conflicting_sources,
    )