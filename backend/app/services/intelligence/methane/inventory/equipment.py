from __future__ import annotations

from .models import InventoryEntity, InventoryEntityType


def create_equipment(
    equipment_id: str,
    name: str,
    facility_id: str,
    *,
    metadata: dict[str, object] | None = None,
) -> InventoryEntity:
    return InventoryEntity(
        id=equipment_id,
        name=name,
        entity_type=InventoryEntityType.EQUIPMENT,
        parent_id=facility_id,
        metadata=metadata or {},
    )


def create_component(
    component_id: str,
    name: str,
    equipment_id: str,
    *,
    metadata: dict[str, object] | None = None,
) -> InventoryEntity:
    return InventoryEntity(
        id=component_id,
        name=name,
        entity_type=InventoryEntityType.COMPONENT,
        parent_id=equipment_id,
        metadata=metadata or {},
    )
