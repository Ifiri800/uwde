from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceType,
)
from backend.app.services.intelligence.methane.intelligence.super_emitter import (
    SuperEmitterDetectionEngine,
    detect_super_emitters,
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
        unit="kg/h",
        confidence=confidence,
    )


def test_detects_feature_at_threshold():
    result = SuperEmitterDetectionEngine().detect(
        "facility-1",
        [feature("emission_rate", 100.0)],
    )

    assert result.intelligence_type == IntelligenceType.SUPER_EMITTER
    assert result.prediction_count == 1
    assert result.predictions[0].value == 100.0


def test_detects_feature_above_threshold():
    result = detect_super_emitters(
        "facility-1",
        [feature("emission_rate", 250.0)],
    )

    assert result.prediction_count == 1
    assert result.predictions[0].value == 250.0


def test_does_not_detect_feature_below_threshold():
    result = detect_super_emitters(
        "facility-1",
        [feature("emission_rate", 99.9)],
    )

    assert result.prediction_count == 0
    assert result.confidence == 0.0


def test_custom_threshold():
    result = detect_super_emitters(
        "facility-1",
        [feature("emission_rate", 50.0)],
        threshold=50.0,
    )

    assert result.prediction_count == 1


def test_multiple_candidates_are_detected():
    result = detect_super_emitters(
        "facility-1",
        [
            feature("source_a", 150.0),
            feature("source_b", 250.0),
            feature("source_c", 20.0),
        ],
    )

    assert result.prediction_count == 2
    assert result.metadata["candidate_count"] == 2


def test_features_are_normalized():
    result = detect_super_emitters(
        "facility-1",
        [
            feature("z_feature", 150.0),
            feature("a_feature", 200.0),
        ],
    )

    assert tuple(
        f.name for f in result.features
    ) == ("a_feature", "z_feature")


def test_prediction_contains_feature_metadata():
    result = detect_super_emitters(
        "facility-1",
        [feature("emission_rate", 200.0)],
    )

    prediction = result.predictions[0]

    assert prediction.feature_names == ("emission_rate",)
    assert prediction.model_id == "deterministic-threshold"
    assert prediction.metadata["threshold"] == 100.0
    assert prediction.metadata["threshold_ratio"] == 2.0


def test_signal_and_evidence_ids_are_preserved():
    result = detect_super_emitters(
        "facility-1",
        [feature("emission_rate", 150.0)],
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )

    prediction = result.predictions[0]

    assert result.signal_ids == ("signal-1",)
    assert result.evidence_ids == ("evidence-1",)
    assert prediction.signal_ids == ("signal-1",)
    assert prediction.evidence_ids == ("evidence-1",)


def test_confidence_is_derived_from_candidates():
    result = detect_super_emitters(
        "facility-1",
        [
            feature("source_a", 150.0, confidence=0.8),
            feature("source_b", 200.0, confidence=0.6),
        ],
    )

    assert result.confidence == 0.7


def test_negative_threshold_is_rejected():
    try:
        detect_super_emitters(
            "facility-1",
            [feature("emission_rate", 100.0)],
            threshold=-1.0,
        )
    except ValueError as exc:
        assert "threshold cannot be negative" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_empty_features_are_rejected():
    try:
        detect_super_emitters(
            "facility-1",
            [],
        )
    except ValueError as exc:
        assert "at least one feature is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_empty_entity_id_is_rejected():
    try:
        detect_super_emitters(
            "",
            [feature("emission_rate", 100.0)],
        )
    except ValueError as exc:
        assert "entity_id is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
