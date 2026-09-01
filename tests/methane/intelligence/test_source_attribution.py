from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceType,
)
from backend.app.services.intelligence.methane.intelligence.source_attribution import (
    SourceAttributionEngine,
    attribute_sources,
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
        SourceAttributionEngine().predict("", [feature("compressor", 1)])
    except ValueError as exc:
        assert "entity_id" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_requires_features():
    try:
        SourceAttributionEngine().predict("asset-1", [])
    except ValueError as exc:
        assert "feature" in str(exc)
    else:
        raise AssertionError("ValueError expected")


def test_returns_source_attribution_type():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
    )

    assert result.intelligence_type == IntelligenceType.SOURCE_ATTRIBUTION


def test_prediction_is_created():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
    )

    assert result.prediction_count == 1
    assert result.predictions[0].value == 1.0


def test_multiple_sources_are_normalized():
    result = attribute_sources(
        "asset-1",
        [
            feature("compressor", 10),
            feature("valve", 20),
        ],
    )

    values = [prediction.value for prediction in result.predictions]

    assert sum(values) == 1.0


def test_stronger_source_gets_higher_score():
    result = attribute_sources(
        "asset-1",
        [
            feature("compressor", 10),
            feature("valve", 30),
        ],
    )

    predictions = {
        prediction.feature_names[0]: prediction.value
        for prediction in result.predictions
    }

    assert predictions["valve"] > predictions["compressor"]


def test_confidence_affects_attribution():
    result = attribute_sources(
        "asset-1",
        [
            feature("compressor", 10, 1.0),
            feature("valve", 10, 0.5),
        ],
    )

    predictions = {
        prediction.feature_names[0]: prediction.value
        for prediction in result.predictions
    }

    assert predictions["compressor"] > predictions["valve"]


def test_zero_values_are_supported():
    result = attribute_sources(
        "asset-1",
        [
            feature("compressor", 0),
            feature("valve", 0),
        ],
    )

    assert all(
        prediction.value == 0.0
        for prediction in result.predictions
    )


def test_negative_values_do_not_create_negative_scores():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", -10)],
    )

    assert result.predictions[0].value == 0.0


def test_signal_ids_are_preserved():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
        signal_ids=("signal-1",),
    )

    assert result.signal_ids == ("signal-1",)
    assert result.predictions[0].signal_ids == ("signal-1",)


def test_evidence_ids_are_preserved():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
        evidence_ids=("evidence-1",),
    )

    assert result.evidence_ids == ("evidence-1",)
    assert result.predictions[0].evidence_ids == ("evidence-1",)


def test_explanation_is_present():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
    )

    assert result.predictions[0].explanation


def test_feature_names_are_preserved():
    result = attribute_sources(
        "asset-1",
        [feature("compressor", 10)],
    )

    assert result.predictions[0].feature_names == ("compressor",)


def test_result_confidence_is_bounded():
    result = attribute_sources(
        "asset-1",
        [
            feature("compressor", 10, 1.0),
            feature("valve", 20, 0.5),
        ],
    )

    assert 0.0 <= result.confidence <= 1.0
