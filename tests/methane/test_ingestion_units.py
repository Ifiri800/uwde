import pytest

from backend.app.services.intelligence.methane.ingestion.units import (
    UnitConversionError,
    UnitValue,
    convert,
    convert_mass,
    convert_time,
    convert_unit_value,
    convert_volume,
)


def test_kg_to_tonne():
    assert convert_mass(1000, "kg", "t") == 1


def test_tonne_to_kg():
    assert convert_mass(2, "t", "kg") == 2000


def test_grams_to_kg():
    assert convert_mass(5000, "g", "kg") == 5


def test_volume_conversion():
    assert convert_volume(1000, "L", "m3") == 1


def test_time_conversion():
    assert convert_time(2, "h", "s") == 7200


def test_generic_conversion():
    assert convert(1000, "kg", "t") == 1


def test_unit_value_conversion():
    measurement = UnitValue(2500, "kg")

    result = convert_unit_value(measurement, "t")

    assert result.value == 2.5
    assert result.unit == "t"


def test_unsupported_mass_unit():
    with pytest.raises(UnitConversionError):
        convert_mass(1, "lb", "kg")


def test_incompatible_units():
    with pytest.raises(UnitConversionError):
        convert(1, "kg", "m3")


def test_empty_unit_rejected():
    with pytest.raises(ValueError):
        UnitValue(1, "")
