from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class SpatialPoint:
    """A geographic point represented by latitude and longitude."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")


@dataclass(frozen=True)
class BoundingBox:
    """Geographic bounding box."""

    min_latitude: float
    min_longitude: float
    max_latitude: float
    max_longitude: float

    def __post_init__(self) -> None:
        SpatialPoint(self.min_latitude, self.min_longitude)
        SpatialPoint(self.max_latitude, self.max_longitude)

        if self.min_latitude > self.max_latitude:
            raise ValueError(
                "min_latitude cannot exceed max_latitude"
            )

        if self.min_longitude > self.max_longitude:
            raise ValueError(
                "min_longitude cannot exceed max_longitude"
            )


def haversine_distance_km(
    first: SpatialPoint,
    second: SpatialPoint,
) -> float:
    """Return great-circle distance between two geographic points."""

    if not isinstance(first, SpatialPoint):
        raise ValueError("first must be a SpatialPoint")

    if not isinstance(second, SpatialPoint):
        raise ValueError("second must be a SpatialPoint")

    latitude_1 = radians(first.latitude)
    latitude_2 = radians(second.latitude)

    delta_latitude = radians(
        second.latitude - first.latitude
    )
    delta_longitude = radians(
        second.longitude - first.longitude
    )

    a = (
        sin(delta_latitude / 2) ** 2
        + cos(latitude_1)
        * cos(latitude_2)
        * sin(delta_longitude / 2) ** 2
    )

    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def point_within_bounds(
    point: SpatialPoint,
    bounds: BoundingBox,
) -> bool:
    """Return whether a point lies within a bounding box."""

    if not isinstance(point, SpatialPoint):
        raise ValueError("point must be a SpatialPoint")

    if not isinstance(bounds, BoundingBox):
        raise ValueError("bounds must be a BoundingBox")

    return (
        bounds.min_latitude
        <= point.latitude
        <= bounds.max_latitude
        and bounds.min_longitude
        <= point.longitude
        <= bounds.max_longitude
    )


def create_bounding_box(
    center: SpatialPoint,
    latitude_margin: float,
    longitude_margin: float,
) -> BoundingBox:
    """Create a bounding box around a geographic center."""

    if not isinstance(center, SpatialPoint):
        raise ValueError("center must be a SpatialPoint")

    if latitude_margin < 0:
        raise ValueError(
            "latitude_margin cannot be negative"
        )

    if longitude_margin < 0:
        raise ValueError(
            "longitude_margin cannot be negative"
        )

    if center.latitude - latitude_margin < -90:
        raise ValueError("latitude bounds exceed valid range")

    if center.latitude + latitude_margin > 90:
        raise ValueError("latitude bounds exceed valid range")

    if center.longitude - longitude_margin < -180:
        raise ValueError("longitude bounds exceed valid range")

    if center.longitude + longitude_margin > 180:
        raise ValueError("longitude bounds exceed valid range")

    return BoundingBox(
        min_latitude=center.latitude - latitude_margin,
        min_longitude=center.longitude - longitude_margin,
        max_latitude=center.latitude + latitude_margin,
        max_longitude=center.longitude + longitude_margin,
    )
