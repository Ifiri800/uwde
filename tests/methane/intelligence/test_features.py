import pytest

from backend.app.services.intelligence.methane.intelligence.features import (
    feature_map,
    normalize_features,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
)


def make_feature(name, value):
    return IntelligenceFeature(
        name=name,
        value=value,
        source="test",
    )


def test_normalize_features_sorts_by_name():
    features = (
        make_feature("z_feature", 3.0),
        make_feature("a_feature", 1.0),
        make_feature("m_feature", 2.0),
    )

    normalized = normalize_features(features)

    assert tuple(
        feature.name
        for feature in normalized
    ) == (
        "a_feature",
        "m_feature",
        "z_feature",
    )


def test_normalize_features_rejects_invalid_objects():
    with pytest.raises(TypeError):
        normalize_features(
            [
                make_feature("valid", 1.0),
                "invalid",
            ]
        )


def test_feature_map_returns_name_value_mapping():
    features = (
        make_feature("emission_rate", 4.5),
        make_feature("pressure", 2.0),
    )

    result = feature_map(features)

    assert result == {
        "emission_rate": 4.5,
        "pressure": 2.0,
    }


def test_feature_map_is_deterministic():
    features = (
        make_feature("z_feature", 3.0),
        make_feature("a_feature", 1.0),
    )

    result = feature_map(features)

    assert list(result.keys()) == [
        "a_feature",
        "z_feature",
    ]
