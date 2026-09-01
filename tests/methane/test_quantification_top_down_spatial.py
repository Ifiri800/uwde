import pytest

from backend.app.services.intelligence.methane.quantification.top_down.spatial import (
    BoundingBox,
    SpatialPoint,
    create_bounding_box,
    haversine_distance_km,
    point_within_bounds,
)


def test_spatial_point_accepts_valid_coordinates():
    point = SpatialPoint(
        latitude=4.8156,
        longitude=7.0498,
    )

    assert point.latitude == 4.8156
    assert point.longitude == 7.0498


@pytest.mark.parametrize(
    "latitude",
    [-91.0, 91.0],
)
def test_spatial_point_rejects_invalid_latitude(latitude):
    with pytest.raises(ValueError):
        SpatialPoint(latitude=latitude, longitude=0.0)


@pytest.mark.parametrize(
    "longitude",
    [-181.0, 181.0],
)
def test_spatial_point_rejects_invalid_longitude(longitude):
    with pytest.raises(ValueError):
        SpatialPoint(latitude=0.0, longitude=longitude)


def test_bounding_box_accepts_valid_coordinates():
    bounds = BoundingBox(
        min_latitude=4.0,
        min_longitude=7.0,
        max_latitude=5.0,
        max_longitude=8.0,
    )

    assert bounds.min_latitude == 4.0
    assert bounds.max_longitude == 8.0


def test_bounding_box_rejects_reversed_latitude():
    with pytest.raises(ValueError):
        BoundingBox(
            min_latitude=5.0,
            min_longitude=7.0,
            max_latitude=4.0,
            max_longitude=8.0,
        )


def test_bounding_box_rejects_reversed_longitude():
    with pytest.raises(ValueError):
        BoundingBox(
            min_latitude=4.0,
            min_longitude=8.0,
            max_latitude=5.0,
            max_longitude=7.0,
        )


def test_haversine_distance_same_point_is_zero():
    point = SpatialPoint(4.8156, 7.0498)

    assert haversine_distance_km(point, point) == pytest.approx(0.0)


def test_haversine_distance_is_symmetric():
    first = SpatialPoint(4.8156, 7.0498)
    second = SpatialPoint(5.0, 7.2)

    assert haversine_distance_km(first, second) == pytest.approx(
        haversine_distance_km(second, first)
    )


def test_point_within_bounds():
    point = SpatialPoint(4.5, 7.5)

    bounds = BoundingBox(
        min_latitude=4.0,
        min_longitude=7.0,
        max_latitude=5.0,
        max_longitude=8.0,
    )

    assert point_within_bounds(point, bounds)


def test_point_outside_bounds():
    point = SpatialPoint(6.0, 7.5)

    bounds = BoundingBox(
        min_latitude=4.0,
        min_longitude=7.0,
        max_latitude=5.0,
        max_longitude=8.0,
    )

    assert not point_within_bounds(point, bounds)


def test_create_bounding_box():
    center = SpatialPoint(4.8156, 7.0498)

    bounds = create_bounding_box(
        center,
        latitude_margin=0.1,
        longitude_margin=0.2,
    )

    assert bounds.min_latitude == pytest.approx(4.7156)
    assert bounds.max_latitude == pytest.approx(4.9156)
    assert bounds.min_longitude == pytest.approx(6.8498)
    assert bounds.max_longitude == pytest.approx(7.2498)


def test_create_bounding_box_rejects_negative_margins():
    center = SpatialPoint(4.8156, 7.0498)

    with pytest.raises(ValueError):
        create_bounding_box(
            center,
            latitude_margin=-0.1,
            longitude_margin=0.1,
        )
