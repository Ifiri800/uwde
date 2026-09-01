from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class ActivityData:
    """
    Activity data used by bottom-up methane emissions quantification.

    Examples include production, throughput, fuel use, operating hours,
    gas processed, vented volumes, or other activity measurements.
    """

    activity_id: str
    source_id: str
    quantity: float
    unit: str
    period_start: datetime
    period_end: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_activity_data(activity: ActivityData) -> ActivityData:
    """
    Validate a bottom-up activity-data record.

    Returns the original immutable record when valid.
    Raises ValueError when the record violates the Layer 7 contract.
    """

    if not isinstance(activity, ActivityData):
        raise ValueError("activity must be an ActivityData instance")

    if not activity.activity_id.strip():
        raise ValueError("activity_id is required")

    if not activity.source_id.strip():
        raise ValueError("source_id is required")

    if activity.quantity < 0:
        raise ValueError("quantity cannot be negative")

    if not activity.unit.strip():
        raise ValueError("unit is required")

    if activity.period_start.tzinfo is None:
        raise ValueError("period_start must be timezone-aware")

    if activity.period_end.tzinfo is None:
        raise ValueError("period_end must be timezone-aware")

    if activity.period_end <= activity.period_start:
        raise ValueError("period_end must be after period_start")

    return activity
