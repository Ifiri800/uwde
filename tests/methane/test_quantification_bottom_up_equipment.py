import pytest

from backend.app.services.intelligence.methane.quantification.bottom_up.equipment import (
    EquipmentActivity,
    validate_equipment_activity,
)


def test_valid_equipment_activity():
    activity = EquipmentActivity(
        equipment_id="EQ-001",
        equipment_type="compressor",
        quantity=10.0,
        unit="operating_hours",
        emission_factor_id="EF-001",
    )

    assert validate_equipment_activity(activity) == activity


def test_inactive_equipment_is_supported():
    activity = EquipmentActivity(
        equipment_id="EQ-002",
        equipment_type="compressor",
        quantity=5.0,
        unit="operating_hours",
        emission_factor_id="EF-001",
        operating=False,
    )

    assert validate_equipment_activity(activity).operating is False


def test_zero_quantity_is_valid():
    activity = EquipmentActivity(
        equipment_id="EQ-003",
        equipment_type="valve",
        quantity=0.0,
        unit="count",
        emission_factor_id="EF-002",
    )

    assert validate_equipment_activity(activity) == activity


def test_negative_quantity_is_rejected():
    activity = EquipmentActivity(
        equipment_id="EQ-004",
        equipment_type="valve",
        quantity=-1.0,
        unit="count",
        emission_factor_id="EF-002",
    )

    with pytest.raises(ValueError):
        validate_equipment_activity(activity)


def test_missing_equipment_id_is_rejected():
    activity = EquipmentActivity(
        equipment_id="",
        equipment_type="valve",
        quantity=1.0,
        unit="count",
        emission_factor_id="EF-002",
    )

    with pytest.raises(ValueError):
        validate_equipment_activity(activity)


def test_missing_equipment_type_is_rejected():
    activity = EquipmentActivity(
        equipment_id="EQ-005",
        equipment_type="",
        quantity=1.0,
        unit="count",
        emission_factor_id="EF-002",
    )

    with pytest.raises(ValueError):
        validate_equipment_activity(activity)


def test_missing_unit_is_rejected():
    activity = EquipmentActivity(
        equipment_id="EQ-006",
        equipment_type="valve",
        quantity=1.0,
        unit="",
        emission_factor_id="EF-002",
    )

    with pytest.raises(ValueError):
        validate_equipment_activity(activity)


def test_missing_emission_factor_is_rejected():
    activity = EquipmentActivity(
        equipment_id="EQ-007",
        equipment_type="valve",
        quantity=1.0,
        unit="count",
        emission_factor_id="",
    )

    with pytest.raises(ValueError):
        validate_equipment_activity(activity)
