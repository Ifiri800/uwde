import pytest

from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligenceType,
)
from backend.app.services.intelligence.methane.intelligence.pattern import (
    PatternRecognitionEngine,
    recognize_patterns,
)


def make_feature(
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


def test_detects_increasing_pattern():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("t1", 0.1),
            make_feature("t2", 0.3),
            make_feature("t3", 0.6),
        ],
    )

    assert result.metadata["pattern"] == "increasing"
    assert result.predictions[0].value == pytest.approx(0.25)


def test_detects_decreasing_pattern():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("t1", 0.9),
            make_feature("t2", 0.6),
            make_feature("t3", 0.2),
        ],
    )

    assert result.metadata["pattern"] == "decreasing"
    assert result.predictions[0].value == pytest.approx(0.35)


def test_detects_stable_pattern():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("t1", 0.50),
            make_feature("t2", 0.52),
            make_feature("t3", 0.49),
        ],
    )

    assert result.metadata["pattern"] == "stable"


def test_single_feature_is_stable():
    result = recognize_patterns(
        "facility-001",
        [make_feature("t1", 0.5)],
    )

    assert result.metadata["pattern"] == "stable"
    assert result.predictions[0].value == 0.0


def test_custom_tolerance():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("t1", 0.50),
            make_feature("t2", 0.60),
        ],
        tolerance=0.15,
    )

    assert result.metadata["pattern"] == "stable"


def test_confidence_is_average_feature_confidence():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("a", 0.2, 0.8),
            make_feature("b", 0.4, 0.6),
        ],
    )

    assert result.confidence == pytest.approx(0.7)


def test_features_are_normalized():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("z", 0.8),
            make_feature("a", 0.2),
        ],
    )

    assert tuple(
        feature.name
        for feature in result.features
    ) == ("a", "z")


def test_signal_and_evidence_ids_are_preserved():
    result = recognize_patterns(
        "facility-001",
        [make_feature("indicator", 0.5)],
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )

    assert result.signal_ids == ("signal-1",)
    assert result.evidence_ids == ("evidence-1",)
    assert result.predictions[0].signal_ids == ("signal-1",)
    assert result.predictions[0].evidence_ids == ("evidence-1",)


def test_prediction_contract():
    result = recognize_patterns(
        "facility-001",
        [
            make_feature("a", 0.2),
            make_feature("b", 0.4),
        ],
    )

    prediction = result.predictions[0]

    assert prediction.intelligence_type == IntelligenceType.PATTERN
    assert prediction.method == IntelligenceMethod.DETERMINISTIC
    assert prediction.model_id == "deterministic-pattern-baseline"
    assert prediction.explanation


def test_empty_features_are_rejected():
    with pytest.raises(
        ValueError,
        match="at least one feature is required",
    ):
        recognize_patterns(
            "facility-001",
            [],
        )


def test_empty_entity_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="entity_id is required",
    ):
        recognize_patterns(
            "",
            [make_feature("a", 0.5)],
        )


def test_invalid_entity_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="entity_id must be a string",
    ):
        recognize_patterns(
            123,
            [make_feature("a", 0.5)],
        )


def test_negative_tolerance_is_rejected():
    with pytest.raises(
        ValueError,
        match="tolerance cannot be negative",
    ):
        recognize_patterns(
            "facility-001",
            [make_feature("a", 0.5)],
            tolerance=-0.1,
        )


def test_custom_identifiers():
    result = recognize_patterns(
        "facility-001",
        [make_feature("a", 0.5)],
        prediction_id="prediction-001",
        model_id="model-001",
    )

    prediction = result.predictions[0]

    assert prediction.prediction_id == "prediction-001"
    assert prediction.model_id == "model-001"


def test_deterministic_results():
    features = [
        make_feature("a", 0.2, 0.9),
        make_feature("b", 0.5, 0.8),
        make_feature("c", 0.7, 0.7),
    ]

    first = recognize_patterns(
        "facility-001",
        features,
    )

    second = recognize_patterns(
        "facility-001",
        features,
    )

    assert first.to_dict() == second.to_dict()
