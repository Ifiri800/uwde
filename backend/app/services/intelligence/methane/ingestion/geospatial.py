from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Mapping


class GeospatialError(ValueError):
    """Raised when geospatial data is invalid or cannot be normalized."""


@dataclass(frozen=True)
class NormalizedCoordinates:
    latitude: float
    longitude: float
    crs: str = "EPSG:4326"

    def __post_init__(self) -> None:
        if not isfinite(self.latitude):
            raise GeospatialError("latitude must be finite")

        if not isfinite(self.longitude):
            raise GeospatialError("longitude must be finite")

        if not -90.0 <= self.latitude <= 90.0:
            raise GeospatialError("latitude must be between -90 and 90")

        if not -180.0 <= self.longitude <= 180.0:
            raise GeospatialError("longitude must be between -180 and 180")

        if not self.crs.strip():
            raise GeospatialError("crs is required")


def validate_coordinates(
    latitude: float,
    longitude: float,
) -> bool:
    """Validate geographic coordinates in decimal degrees."""
    if not isinstance(latitude, (int, float)):
        raise TypeError("latitude must be numeric")

    if not isinstance(longitude, (int, float)):
        raise TypeError("longitude must be numeric")

    if not isfinite(latitude):
        raise GeospatialError("latitude must be finite")

    if not isfinite(longitude):
        raise GeospatialError("longitude must be finite")

    if not -90.0 <= latitude <= 90.0:
        raise GeospatialError("latitude must be between -90 and 90")

    if not -180.0 <= longitude <= 180.0:
        raise GeospatialError("longitude must be between -180 and 180")

    return True


def normalize_coordinates(
    latitude: float,
    longitude: float,
    crs: str = "EPSG:4326",
) -> NormalizedCoordinates:
    """Create canonical WGS84 geographic coordinates."""
    validate_coordinates(latitude, longitude)

    if not isinstance(crs, str) or not crs.strip():
        raise GeospatialError("crs is required")

    normalized_crs = crs.strip().upper()

    aliases = {
        "WGS84": "EPSG:4326",
        "WGS 84": "EPSG:4326",
        "EPSG:4326": "EPSG:4326",
    }

    normalized_crs = aliases.get(normalized_crs, normalized_crs)

    if normalized_crs != "EPSG:4326":
        raise GeospatialError(
            "only EPSG:4326/WGS84 coordinates are currently supported"
        )

    return NormalizedCoordinates(
        latitude=float(latitude),
        longitude=float(longitude),
        crs=normalized_crs,
    )


def validate_geometry(
    geometry: Mapping[str, Any] | None,
) -> bool:
    """Validate a GeoJSON-like geometry structure."""
    if geometry is None:
        return True

    if not isinstance(geometry, Mapping):
        raise TypeError("geometry must be a mapping")

    geometry_type = geometry.get("type")

    if not isinstance(geometry_type, str) or not geometry_type.strip():
        raise GeospatialError("geometry type is required")

    if "coordinates" not in geometry:
        raise GeospatialError("geometry coordinates are required")

    return True


def normalize_reference(
    latitude: float | None = None,
    longitude: float | None = None,
    crs: str | None = None,
    geometry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Normalize a complete geospatial reference.

    A reference may contain point coordinates, geometry, or both.
    """
    if latitude is None and longitude is None:
        normalized_coordinates = None

    elif latitude is None or longitude is None:
        raise GeospatialError(
            "latitude and longitude must be provided together"
        )

    else:
        normalized_coordinates = normalize_coordinates(
            latitude,
            longitude,
            crs or "EPSG:4326",
        )

    validate_geometry(geometry)

    result: dict[str, Any] = {
        "latitude": (
            normalized_coordinates.latitude
            if normalized_coordinates is not None
            else None
        ),
        "longitude": (
            normalized_coordinates.longitude
            if normalized_coordinates is not None
            else None
        ),
        "crs": (
            normalized_coordinates.crs
            if normalized_coordinates is not None
            else (crs.strip().upper() if crs else None)
        ),
        "geometry": geometry,
    }

    return result


def coordinates_equal(
    first: NormalizedCoordinates,
    second: NormalizedCoordinates,
) -> bool:
    """Compare two normalized coordinate references."""
    if not isinstance(first, NormalizedCoordinates):
        raise TypeError("first must be NormalizedCoordinates")

    if not isinstance(second, NormalizedCoordinates):
        raise TypeError("second must be NormalizedCoordinates")

    return (
        first.latitude == second.latitude
        and first.longitude == second.longitude
        and first.crs == second.crs
    )
