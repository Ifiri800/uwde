from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .provenance import SourcedValue


@dataclass(frozen=True)
class Conflict:
    """
    Represents a disagreement between sourced values for one field.
    """

    field_name: str
    values: tuple[Any, ...]
    observations: tuple[SourcedValue, ...]

    @property
    def source_count(self) -> int:
        """Return the number of observations involved in the conflict."""
        return len(self.observations)

    @property
    def value_count(self) -> int:
        """Return the number of distinct values involved."""
        return len(self.values)

    @property
    def is_conflict(self) -> bool:
        """Return True when more than one distinct value exists."""
        return self.value_count > 1


def _value_key(value: Any) -> Any:
    """
    Create a stable comparison key for common Python values.
    """

    try:
        hash(value)
        return value
    except TypeError:
        return repr(value)


def detect_conflict(
    field_name: str,
    observations: list[SourcedValue],
) -> Conflict | None:
    """
    Detect whether observations for a field contain conflicting values.

    Returns None when all observations contain the same value or when
    there are fewer than two observations.
    """

    if len(observations) < 2:
        return None

    distinct_values: list[Any] = []
    seen: set[Any] = set()

    for observation in observations:
        key = _value_key(observation.value)

        if key not in seen:
            seen.add(key)
            distinct_values.append(observation.value)

    if len(distinct_values) <= 1:
        return None

    return Conflict(
        field_name=field_name,
        values=tuple(distinct_values),
        observations=tuple(observations),
    )


def detect_conflicts(
    observations_by_field: dict[str, list[SourcedValue]],
) -> list[Conflict]:
    """
    Detect conflicts across multiple fields.

    Each field is evaluated independently.
    """

    conflicts: list[Conflict] = []

    for field_name, observations in observations_by_field.items():
        conflict = detect_conflict(
            field_name,
            observations,
        )

        if conflict is not None:
            conflicts.append(conflict)

    return conflicts