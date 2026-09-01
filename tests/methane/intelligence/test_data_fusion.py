from backend.app.services.intelligence.methane.intelligence.data_fusion import (
    DataFusionEngine,
    fuse_intelligence,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceType,
)


def feature(
    name: str,
    value: float,
    confidence: float = 1.0,
) -> IntelligenceFeature:
    return IntelligenceFeature(
        name=name,
        value=value,
        source="test",
        confidence=confidence,
    )


def test_requires_entity_id():
    try:
        DataFusionEngine().predict("", [feature("signal", 1.0)])
    except ValueError as exc:
        assert "entity_id" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_requires_features():
    try:
        DataFusionEngine().predict("asset-1", [])
    except ValueError as exc:
        assert "feature" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_returns_data_fusion_type():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
    )

    assert result.intelligence_type == IntelligenceType.DATA_FUSION


def test_single_feature_is_preserved():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
    )

    assert result.prediction_count == 1
    assert result.predictions[0].value == 10.0


def test_equal_confidence_produces_mean():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("a", 10.0),
            feature("b", 20.0),
        ],
    )

    assert result.predictions[0].value == 15.0


def test_confidence_weights_fusion():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("high", 10.0, 1.0),
            feature("low", 30.0, 0.5),
        ],
    )

    assert result.predictions[0].value == 16.666666666666668


def test_zero_confidence_is_supported():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("ignored", 100.0, 0.0),
            feature("valid", 20.0, 1.0),
        ],
    )

    assert result.predictions[0].value == 20.0


def test_all_zero_confidence_returns_zero():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("a", 100.0, 0.0),
            feature("b", 200.0, 0.0),
        ],
    )

    assert result.predictions[0].value == 0.0


def test_negative_values_are_bounded():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", -10.0)],
    )

    assert result.predictions[0].value == 0.0


def test_signal_ids_are_preserved():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
        signal_ids=("signal-1", "signal-2"),
    )

    assert result.signal_ids == ("signal-1", "signal-2")
    assert result.predictions[0].signal_ids == (
        "signal-1",
        "signal-2",
    )


def test_evidence_ids_are_preserved():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
        evidence_ids=("evidence-1",),
    )

    assert result.evidence_ids == ("evidence-1",)
    assert result.predictions[0].evidence_ids == (
        "evidence-1",
    )


def test_feature_names_are_preserved():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("z", 10.0),
            feature("a", 20.0),
        ],
    )

    assert result.predictions[0].feature_names == ("a", "z")


def test_confidence_is_bounded():
    result = fuse_intelligence(
        "asset-1",
        [
            feature("a", 10.0, 1.0),
            feature("b", 20.0, 0.5),
        ],
    )

    assert 0.0 <= result.confidence <= 1.0


def test_explanation_is_present():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
    )

    assert result.predictions[0].explanation


def test_metadata_identifies_fusion_method():
    result = fuse_intelligence(
        "asset-1",
        [feature("signal", 10.0)],
    )

    assert (
        result.metadata["fusion_method"]
        == "confidence_weighted_mean"
    )
