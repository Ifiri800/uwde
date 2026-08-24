from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from .conflicts import Conflict
from .models import ReconciliationResolution


class ResolutionStrategy(str, Enum):
    """
    Supported reconciliation strategies.
    """

    MAJORITY = "majority"
    HIGHEST_CONFIDENCE = "highest_confidence"
    LATEST = "latest"
    WEIGHTED = "weighted"
    MANUAL = "manual"
    NONE = "none"


# Backwards-compatible name used by older UWDE code.
Resolution = ReconciliationResolution


def _observation_value(observation: Any) -> Any:
    """
    Extract the value from an observation.
    """

    if isinstance(observation, dict):
        if "value" in observation:
            return observation["value"]

    if hasattr(observation, "value"):
        return observation.value

    return observation


def _observation_confidence(observation: Any) -> float:
    """
    Extract observation confidence.

    Missing confidence is treated as zero.
    """

    if isinstance(observation, dict):
        value = observation.get("confidence", 0.0)
        return float(value or 0.0)

    if hasattr(observation, "confidence"):
        value = getattr(observation, "confidence")
        return float(value or 0.0)

    provenance = getattr(
        observation,
        "provenance",
        None,
    )

    if provenance is not None:
        value = getattr(
            provenance,
            "confidence",
            0.0,
        )
        return float(value or 0.0)

    return 0.0


def _observation_timestamp(
    observation: Any,
) -> datetime | None:
    """
    Extract the observation timestamp.

    Supports timestamp/extracted_at on both the observation
    and its provenance.
    """

    if isinstance(observation, dict):
        timestamp = observation.get("timestamp")

        if isinstance(timestamp, datetime):
            return timestamp

        extracted_at = observation.get("extracted_at")

        if isinstance(extracted_at, datetime):
            return extracted_at

    timestamp = getattr(
        observation,
        "timestamp",
        None,
    )

    if isinstance(timestamp, datetime):
        return timestamp

    extracted_at = getattr(
        observation,
        "extracted_at",
        None,
    )

    if isinstance(extracted_at, datetime):
        return extracted_at

    provenance = getattr(
        observation,
        "provenance",
        None,
    )

    if provenance is not None:
        timestamp = getattr(
            provenance,
            "timestamp",
            None,
        )

        if isinstance(timestamp, datetime):
            return timestamp

        extracted_at = getattr(
            provenance,
            "extracted_at",
            None,
        )

        if isinstance(extracted_at, datetime):
            return extracted_at

    return None


def _values_equal(
    left: Any,
    right: Any,
) -> bool:
    """
    Safely compare values, including unhashable values.
    """

    try:
        return left == right
    except Exception:
        return repr(left) == repr(right)


def _group_observations(
    observations: list[Any],
) -> list[tuple[Any, list[Any]]]:
    """
    Group observations by their value.
    """

    groups: list[
        tuple[Any, list[Any]]
    ] = []

    for observation in observations:
        value = _observation_value(observation)

        found = False

        for existing_value, members in groups:
            if _values_equal(
                existing_value,
                value,
            ):
                members.append(observation)
                found = True
                break

        if not found:
            groups.append(
                (
                    value,
                    [observation],
                )
            )

    return groups


def _latest_observation(
    observations: list[Any],
) -> Any:
    """
    Return the latest observation.

    If no timestamps are available, preserve original
    observation order and return the final observation.
    """

    if not observations:
        return None

    timestamped = [
        (
            observation,
            _observation_timestamp(observation),
        )
        for observation in observations
    ]

    available = [
        item
        for item in timestamped
        if item[1] is not None
    ]

    if not available:
        return observations[-1]

    return max(
        available,
        key=lambda item: item[1],
    )[0]


def _representative_observation(
    observations: list[Any],
) -> Any:
    """
    Select the best representative observation from a group.

    Highest confidence wins. If confidence ties, latest
    observation wins.
    """

    if not observations:
        return None

    return max(
        observations,
        key=lambda item: (
            _observation_confidence(item),
            _observation_timestamp(item)
            or datetime.min,
        ),
    )


def resolve_conflict(
    conflict: Conflict,
    strategy: ResolutionStrategy | str = (
        ResolutionStrategy.MAJORITY
    ),
) -> ReconciliationResolution | None:
    """
    Resolve one reconciliation conflict.
    """

    # Normalize strategy
    if isinstance(strategy, str):
        try:
            strategy = ResolutionStrategy(strategy)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported resolution strategy: {strategy}"
            ) from exc

    observations = list(
        conflict.observations
    )

    # ---------------------------------------------------------------
    # No observations
    # ---------------------------------------------------------------

    if not observations:

        if strategy == ResolutionStrategy.NONE:
            return None

        return ReconciliationResolution(
            field_name=conflict.field_name,
            value=None,
            strategy=strategy.value,
            confidence=0.0,
            requires_review=True,
            conflict=conflict,
            selected_observation=None,
        )

    groups = _group_observations(
        observations
    )

    selected_value: Any = None
    selected_observations: list[Any] = []

    # ---------------------------------------------------------------
    # MAJORITY
    # ---------------------------------------------------------------

    if strategy == ResolutionStrategy.MAJORITY:

        best_count = -1
        best_confidence = -1.0

        for value, members in groups:

            count = len(members)

            confidence = sum(
                _observation_confidence(item)
                for item in members
            )

            if (
                count > best_count
                or (
                    count == best_count
                    and confidence > best_confidence
                )
            ):
                selected_value = value
                selected_observations = members
                best_count = count
                best_confidence = confidence

    # ---------------------------------------------------------------
    # HIGHEST CONFIDENCE
    # ---------------------------------------------------------------

    elif (
        strategy
        == ResolutionStrategy.HIGHEST_CONFIDENCE
    ):

        selected_observation = max(
            observations,
            key=lambda item: (
                _observation_confidence(item),
                _observation_timestamp(item)
                or datetime.min,
            ),
        )

        selected_value = _observation_value(
            selected_observation
        )

        selected_observations = [
            selected_observation
        ]

    # ---------------------------------------------------------------
    # LATEST
    # ---------------------------------------------------------------

    elif strategy == ResolutionStrategy.LATEST:

        selected_observation = _latest_observation(
            observations
        )

        selected_value = _observation_value(
            selected_observation
        )

        selected_observations = [
            selected_observation
        ]

    # ---------------------------------------------------------------
    # WEIGHTED
    # ---------------------------------------------------------------

    elif strategy == ResolutionStrategy.WEIGHTED:

        best_score = -1.0

        for value, members in groups:

            score = sum(
                _observation_confidence(item)
                for item in members
            )

            if score > best_score:
                selected_value = value
                selected_observations = members
                best_score = score

    # ---------------------------------------------------------------
    # MANUAL
    # ---------------------------------------------------------------

    elif strategy == ResolutionStrategy.MANUAL:

        return ReconciliationResolution(
            field_name=conflict.field_name,
            value=None,
            strategy=strategy.value,
            confidence=0.0,
            requires_review=True,
            conflict=conflict,
            selected_observation=None,
        )

    # ---------------------------------------------------------------
    # NONE
    # ---------------------------------------------------------------

    elif strategy == ResolutionStrategy.NONE:

        return ReconciliationResolution(
            field_name=conflict.field_name,
            value=None,
            strategy=strategy.value,
            confidence=0.0,
            requires_review=False,
            conflict=conflict,
            selected_observation=None,
        )

    # ---------------------------------------------------------------
    # Calculate resolution confidence
    # ---------------------------------------------------------------

    confidence_values = [
        _observation_confidence(item)
        for item in selected_observations
    ]

    confidence = (
        sum(confidence_values)
        / len(confidence_values)
        if confidence_values
        else 0.0
    )

    # Select a representative observation.
    #
    # For majority/weighted, there can be several observations
    # supporting the selected value. We expose the strongest one.
    selected_observation = _representative_observation(
        selected_observations
    )

    return ReconciliationResolution(
        field_name=conflict.field_name,
        value=selected_value,
        strategy=strategy.value,
        confidence=confidence,
        requires_review=False,
        conflict=conflict,
        selected_observation=selected_observation,
    )


def resolve_conflicts(
    conflicts: list[Conflict],
    strategy: ResolutionStrategy | str = (
        ResolutionStrategy.MAJORITY
    ),
) -> list[ReconciliationResolution]:
    """
    Resolve multiple conflicts independently.
    """

    resolutions: list[
        ReconciliationResolution
    ] = []

    for conflict in conflicts:

        resolution = resolve_conflict(
            conflict,
            strategy=strategy,
        )

        if resolution is not None:
            resolutions.append(
                resolution
            )

    return resolutions


def resolve(
    conflict: Conflict,
    strategy: ResolutionStrategy | str = (
        ResolutionStrategy.MAJORITY
    ),
) -> ReconciliationResolution | None:
    """
    Backwards-compatible wrapper.
    """

    return resolve_conflict(
        conflict,
        strategy=strategy,
    )