from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


class TemporalNormalizationError(ValueError):
    """Raised when temporal data cannot be normalized safely."""


@dataclass(frozen=True)
class NormalizedTimestamp:
    value: datetime
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise TypeError("value must be a datetime")

        if self.value.tzinfo is None:
            raise TemporalNormalizationError(
                "timestamp must be timezone-aware"
            )


def ensure_aware(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")

    if value.tzinfo is None:
        raise TemporalNormalizationError(
            "timestamp must be timezone-aware"
        )

    return value


def to_utc(value: datetime) -> datetime:
    """Normalize a timezone-aware timestamp to UTC."""
    value = ensure_aware(value)
    return value.astimezone(timezone.utc)


def normalize_timestamp(value: datetime) -> NormalizedTimestamp:
    """Convert a timestamp to the canonical UTC representation."""
    return NormalizedTimestamp(
        value=to_utc(value),
        timezone="UTC",
    )


def synchronize_timestamps(
    values: Iterable[datetime],
) -> tuple[NormalizedTimestamp, ...]:
    """Normalize a collection of timestamps to UTC."""
    return tuple(normalize_timestamp(value) for value in values)


def duration_seconds(
    start: datetime,
    end: datetime,
) -> float:
    """Return elapsed seconds between two timezone-aware timestamps."""
    start_utc = to_utc(start)
    end_utc = to_utc(end)

    duration = (end_utc - start_utc).total_seconds()

    if duration < 0:
        raise TemporalNormalizationError(
            "end timestamp cannot precede start timestamp"
        )

    return duration


def validate_temporal_order(
    values: Iterable[datetime],
) -> bool:
    """Validate that timestamps are in non-decreasing chronological order."""
    timestamps = tuple(to_utc(value) for value in values)

    return all(
        timestamps[index] <= timestamps[index + 1]
        for index in range(len(timestamps) - 1)
    )
