from __future__ import annotations

from .models import InventoryEntity, InventoryEntityType


_PARENT_TYPES: dict[InventoryEntityType, InventoryEntityType | None] = {
    InventoryEntityType.OPERATOR: None,
    InventoryEntityType.ASSET: InventoryEntityType.OPERATOR,
    InventoryEntityType.FIELD: InventoryEntityType.ASSET,
    InventoryEntityType.FACILITY: InventoryEntityType.FIELD,
    InventoryEntityType.EQUIPMENT: InventoryEntityType.FACILITY,
    InventoryEntityType.COMPONENT: InventoryEntityType.EQUIPMENT,
}


def validate_parent(
    entity: InventoryEntity,
    parent: InventoryEntity | None,
) -> bool:
    expected = _PARENT_TYPES[entity.entity_type]

    if expected is None:
        return parent is None

    return parent is not None and parent.entity_type == expected


def validate_hierarchy(
    entities: list[InventoryEntity],
) -> list[str]:
    errors: list[str] = []
    by_id = {entity.id: entity for entity in entities}

    if len(by_id) != len(entities):
        errors.append("duplicate inventory entity IDs")

    for entity in entities:
        expected_parent = _PARENT_TYPES[entity.entity_type]

        if expected_parent is None:
            if entity.parent_id is not None:
                errors.append(
                    f"{entity.id}: operator cannot have a parent"
                )
            continue

        if entity.parent_id is None:
            errors.append(
                f"{entity.id}: missing parent"
            )
            continue

        parent = by_id.get(entity.parent_id)

        if parent is None:
            errors.append(
                f"{entity.id}: parent not found: {entity.parent_id}"
            )
            continue

        if parent.entity_type != expected_parent:
            errors.append(
                f"{entity.id}: invalid parent type"
            )

    return errors
