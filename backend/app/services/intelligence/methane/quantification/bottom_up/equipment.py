from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EquipmentActivity:
    """
    Equipment-level activity input for bottom-up methane quantification.
    """

    equipment_id: str
    equipment_type: str
    quantity: float
    unit: str
    emission_factor_id: str
    operating: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)


def validate_equipment_activity(
    activity: EquipmentActivity,
) -> EquipmentActivity:
    """
    Validate equipment-level activity data.
    """

    if not isinstance(activity, EquipmentActivity):
        raise ValueError(
            "activity must be an EquipmentActivity instance"
        )

    if not activity.equipment_id.strip():
        raise ValueError("equipment_id is required")

    if not activity.equipment_type.strip():
        raise ValueError("equipment_type is required")

    if activity.quantity < 0:
        raise ValueError("quantity cannot be negative")

    if not activity.unit.strip():
        raise ValueError("unit is required")

    if not activity.emission_factor_id.strip():
        raise ValueError("emission_factor_id is required")

    return activity
