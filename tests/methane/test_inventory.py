from backend.app.services.intelligence.methane.inventory.models import (
    InventoryEntity,
    InventoryEntityType,
)
from backend.app.services.intelligence.methane.inventory.hierarchy import (
    validate_hierarchy,
)


def test_operator_has_no_parent():
    entity = InventoryEntity(
        id="op-1",
        name="Operator",
        entity_type=InventoryEntityType.OPERATOR,
    )

    assert validate_hierarchy([entity]) == []


def test_asset_requires_operator():
    operator = InventoryEntity(
        id="op-1",
        name="Operator",
        entity_type=InventoryEntityType.OPERATOR,
    )
    asset = InventoryEntity(
        id="asset-1",
        name="Asset",
        entity_type=InventoryEntityType.ASSET,
        parent_id="op-1",
    )

    assert validate_hierarchy([operator, asset]) == []


def test_invalid_parent_type_is_detected():
    operator = InventoryEntity(
        id="op-1",
        name="Operator",
        entity_type=InventoryEntityType.OPERATOR,
    )
    facility = InventoryEntity(
        id="fac-1",
        name="Facility",
        entity_type=InventoryEntityType.FACILITY,
        parent_id="op-1",
    )

    errors = validate_hierarchy([operator, facility])

    assert errors


def test_missing_parent_is_detected():
    asset = InventoryEntity(
        id="asset-1",
        name="Asset",
        entity_type=InventoryEntityType.ASSET,
    )

    errors = validate_hierarchy([asset])

    assert errors
