from __future__ import annotations

from .models import EmissionSource, InventoryEntity


def validate_entities(
    entities: list[InventoryEntity],
) -> list[str]:
    errors: list[str] = []

    ids = [entity.id for entity in entities]

    if len(ids) != len(set(ids)):
        errors.append("duplicate inventory entity IDs")

    return errors


def validate_sources(
    sources: list[EmissionSource],
    component_ids: set[str],
) -> list[str]:
    errors: list[str] = []

    ids = [source.id for source in sources]

    if len(ids) != len(set(ids)):
        errors.append("duplicate emission source IDs")

    for source in sources:
        if source.component_id not in component_ids:
            errors.append(
                f"{source.id}: component not found"
            )

    return errors


def validate_inventory(
    entities: list[InventoryEntity],
    sources: list[EmissionSource],
) -> list[str]:
    from .hierarchy import validate_hierarchy

    errors = validate_entities(entities)
    errors.extend(validate_hierarchy(entities))
    errors.extend(
        validate_sources(
            sources,
            {entity.id for entity in entities},
        )
    )

    return errors
