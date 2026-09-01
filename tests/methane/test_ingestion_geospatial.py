import pytest

from backend.app.services.intelligence.methane.ingestion.geospatial import (
    GeospatialError,
    NormalizedCoordinates,
    coordinates_equal,
    normalize_coordinates,
    normalize_reference,
    validate_coordinates,
    validate_geometry,
)


def test_validate_coordinates_accepts_valid_coordinates():
    assert validate_coordinates(9.0765, 7.3986) is True


def test_validate_coordinates_rejects_invalid_latitude():
    with pytest.raises(GeospatialError):
        validate_coordinates(91.0, 7.0)


def test_validate_coordinates_rejects_invalid_longitude():
    with pytest.raises(GeospatialError):
        validate_coordinates(9.0, 181.0)


def test_validate_coordinates_rejects_non_numeric_latitude():
    with pytest.raises(TypeError):
        validate_coordinates("9.0", 7.0)


def test_validate_coordinates_rejects_non_finite_values():
    with pytest.raises(GeospatialError):
        validate_coordinates(float("nan"), 7.0)


def test_normalize_coordinates_defaults_to_wgs84():
    result = normalize_coordinates(9.0765, 7.3986)

    assert isinstance(result, NormalizedCoordinates)
    assert result.latitude == 9.0765
    assert result.longitude == 7.3986
    assert result.crs == "EPSG:4326"


def test_normalize_coordinates_accepts_wgs84_alias():
    result = normalize_coordinates(
        9.0765,
        7.3986,
        "WGS84",
    )

    assert result.crs == "EPSG:4326"


def test_normalize_coordinates_rejects_unsupported_crs():
    with pytest.raises(GeospatialError):
        normalize_coordinates(
            9.0765,
            7.3986,
            "EPSG:3857",
        )


def test_validate_geometry_accepts_geojson_like_geometry():
    geometry = {
        "type": "Point",
        "coordinates": [7.3986, 9.0765],
    }

    assert validate_geometry(geometry) is True


def test_validate_geometry_rejects_missing_coordinates():
    geometry = {
        "type": "Point",
    }

    with pytest.raises(GeospatialError):
        validate_geometry(geometry)


def test_normalize_reference_with_coordinates():
    result = normalize_reference(
        latitude=9.0765,
        longitude=7.3986,
        crs="WGS84",
    )

    assert result["latitude"] == 9.0765
    assert result["longitude"] == 7.3986
    assert result["crs"] == "EPSG:4326"


def test_normalize_reference_with_geometry():
    geometry = {
        "type": "Point",
        "coordinates": [7.3986, 9.0765],
    }

    result = normalize_reference(geometry=geometry)

    assert result["latitude"] is None
    assert result["longitude"] is None
    assert result["geometry"] == geometry


def test_normalize_reference_requires_coordinate_pair():
    with pytest.raises(GeospatialError):
        normalize_reference(latitude=9.0765)


def test_coordinates_equal():
    first = normalize_coordinates(9.0765, 7.3986)
    second = normalize_coordinates(9.0765, 7.3986)

    assert coordinates_equal(first, second) is True


def test_coordinates_equal_detects_difference():
    first = normalize_coordinates(9.0765, 7.3986)
    second = normalize_coordinates(9.0766, 7.3986)

    assert coordinates_equal(first, second) is False
