from __future__ import annotations

from dataclasses import dataclass


class UnitConversionError(ValueError):
    """Raised when a unit conversion is unsupported or invalid."""


@dataclass(frozen=True)
class UnitValue:
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError("value must be numeric")

        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("unit is required")


# Canonical mass units are kilograms.
_MASS_TO_KG: dict[str, float] = {
    "kg": 1.0,
    "g": 0.001,
    "mg": 0.000001,
    "t": 1000.0,
    "tonne": 1000.0,
    "tonnes": 1000.0,
}


# Canonical volume units are cubic metres.
_VOLUME_TO_M3: dict[str, float] = {
    "m3": 1.0,
    "m³": 1.0,
    "l": 0.001,
    "L": 0.001,
}


# Canonical time units are seconds.
_TIME_TO_SECONDS: dict[str, float] = {
    "s": 1.0,
    "sec": 1.0,
    "min": 60.0,
    "h": 3600.0,
    "hr": 3600.0,
    "day": 86400.0,
}


def _clean_unit(unit: str) -> str:
    return unit.strip()


def convert_mass(value: float, from_unit: str, to_unit: str) -> float:
    source = _clean_unit(from_unit)
    target = _clean_unit(to_unit)

    if source not in _MASS_TO_KG:
        raise UnitConversionError(f"unsupported mass unit: {from_unit}")

    if target not in _MASS_TO_KG:
        raise UnitConversionError(f"unsupported mass unit: {to_unit}")

    return value * _MASS_TO_KG[source] / _MASS_TO_KG[target]


def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    source = _clean_unit(from_unit)
    target = _clean_unit(to_unit)

    if source not in _VOLUME_TO_M3:
        raise UnitConversionError(f"unsupported volume unit: {from_unit}")

    if target not in _VOLUME_TO_M3:
        raise UnitConversionError(f"unsupported volume unit: {to_unit}")

    return value * _VOLUME_TO_M3[source] / _VOLUME_TO_M3[target]


def convert_time(value: float, from_unit: str, to_unit: str) -> float:
    source = _clean_unit(from_unit)
    target = _clean_unit(to_unit)

    if source not in _TIME_TO_SECONDS:
        raise UnitConversionError(f"unsupported time unit: {from_unit}")

    if target not in _TIME_TO_SECONDS:
        raise UnitConversionError(f"unsupported time unit: {to_unit}")

    return value * _TIME_TO_SECONDS[source] / _TIME_TO_SECONDS[target]


def convert(
    value: float,
    from_unit: str,
    to_unit: str,
) -> float:
    if from_unit in _MASS_TO_KG and to_unit in _MASS_TO_KG:
        return convert_mass(value, from_unit, to_unit)

    if from_unit in _VOLUME_TO_M3 and to_unit in _VOLUME_TO_M3:
        return convert_volume(value, from_unit, to_unit)

    if from_unit in _TIME_TO_SECONDS and to_unit in _TIME_TO_SECONDS:
        return convert_time(value, from_unit, to_unit)

    raise UnitConversionError(
        f"incompatible or unsupported conversion: "
        f"{from_unit} -> {to_unit}"
    )


def convert_unit_value(
    measurement: UnitValue,
    to_unit: str,
) -> UnitValue:
    converted = convert(
        measurement.value,
        measurement.unit,
        to_unit,
    )

    return UnitValue(
        value=converted,
        unit=to_unit,
    )
