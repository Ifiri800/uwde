from backend.app.services.intelligence.methane.inventory.models import (
    EmissionSource,
    EmissionSourceType,
    InventoryEntity,
    InventoryEntityType,
)
from backend.app.services.intelligence.methane.inventory.validation import (
    validate_inventory,
)


def test_valid_complete_inventory():
    operator = InventoryEntity(
        id="op",
        name="Operator",
        entity_type=InventoryEntityType.OPERATOR,
    )
    asset = InventoryEntity(
        id="asset",
        name="Asset",
        entity_type=InventoryEntityType.ASSET,
        parent_id="op",
    )
    field = InventoryEntity(
        id="field",
        name="Field",
        entity_type=InventoryEntityType.FIELD,
        parent_id="asset",
    )
    facility = InventoryEntity(
        id="facility",
        name="Facility",
        entity_type=InventoryEntityType.FACILITY,
        parent_id="field",
    )
    equipment = InventoryEntity(
        id="equipment",
        name="Compressor",
        entity_type=InventoryEntityType.EQUIPMENT,
        parent_id="facility",
    )
    component = InventoryEntity(
        id="component",
        name="Valve",
        entity_type=InventoryEntityType.COMPONENT,
        parent_id="equipment",
    )

    source = EmissionSource(
        id="source",
        name="Valve fugitive emission",
        source_type=EmissionSourceType.FUGITIVE,
        component_id="component",
    )

    errors = validate_inventory(
        [
            operator,
            asset,
            field,
            facility,
            equipment,
            component,
        ],
        [source],
    )

    assert errors == []


def test_orphan_source_is_detected():
    source = EmissionSource(
        id="source",
        name="Orphan source",
        source_type=EmissionSourceType.VENTING,
        component_id="missing",
    )

    errors = validate_inventory([], [source])

    assert errors
