import pytest

from backend.app.services.intelligence.methane.intelligence.leak_probability import (
    LeakProbabilityEngine,
    predict_leak_probability,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
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


def test_predicts_leak_probability():
    result = LeakProbabilityEngine().predict(
        "facility-001",
        [feature("leak_indicator", 0.8)],
    )

    assert result.intelligence_type == (
        IntelligenceType.LEAK_PROBABILITY
    )
    assert result.prediction_count == 1

    prediction = result.predictions[0]

    assert prediction.value == 0.8
    assert prediction.method == IntelligenceMethod.DETERMINISTIC
    assert prediction.confidence == 1.0


def test_probability_is_confidence_weighted():
    result = predict_leak_probability(
        "facility-001",
        [
            feature("indicator_a", 0.2, 1.0),
            feature("indicator_b", 0.8, 0.5),
        ],
    )

    assert result.predictions[0].value == pytest.approx(0.4)


def test_low_classification():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.2)],
    )

    assert result.metadata["classification"] == "low"
    assert result.predictions[0].metadata["classification"] == "low"


def test_medium_classification():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.5)],
    )

    assert result.metadata["classification"] == "medium"


def test_high_classification():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.9)],
    )

    assert result.metadata["classification"] == "high"


def test_boundary_values():
    low = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.0)],
    )

    high = predict_leak_probability(
        "facility-001",
        [feature("indicator", 1.0)],
    )

    assert low.predictions[0].value == 0.0
    assert low.metadata["classification"] == "low"

    assert high.predictions[0].value == 1.0
    assert high.metadata["classification"] == "high"


def test_features_are_normalized():
    result = predict_leak_probability(
        "facility-001",
        [
            feature("z_indicator", 0.8),
            feature("a_indicator", 0.2),
        ],
    )

    assert tuple(
        item.name for item in result.features
    ) == (
        "a_indicator",
        "z_indicator",
    )


def test_signal_and_evidence_ids_are_preserved():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.7)],
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )

    prediction = result.predictions[0]

    assert prediction.signal_ids == ("signal-1",)
    assert prediction.evidence_ids == ("evidence-1",)
    assert result.signal_ids == ("signal-1",)
    assert result.evidence_ids == ("evidence-1",)


def test_confidence_is_average_feature_confidence():
    result = predict_leak_probability(
        "facility-001",
        [
            feature("a", 0.7, 0.8),
            feature("b", 0.9, 0.6),
        ],
    )

    assert result.confidence == pytest.approx(0.7)


def test_values_above_one_are_rejected():
    with pytest.raises(
        ValueError,
        match="leak probability features must be between 0 and 1",
    ):
        predict_leak_probability(
            "facility-001",
            [feature("indicator", 1.1)],
        )


def test_negative_values_are_rejected():
    with pytest.raises(
        ValueError,
        match="leak probability features must be between 0 and 1",
    ):
        predict_leak_probability(
            "facility-001",
            [feature("indicator", -0.1)],
        )


def test_empty_features_are_rejected():
    with pytest.raises(
        ValueError,
        match="at least one feature is required",
    ):
        predict_leak_probability(
            "facility-001",
            [],
        )


def test_explanation_is_present():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.7)],
    )

    assert result.predictions[0].explanation
    assert "Leak probability" in result.predictions[0].explanation


def test_custom_identifiers_are_preserved():
    result = predict_leak_probability(
        "facility-001",
        [feature("indicator", 0.7)],
        prediction_id="prediction-123",
        model_id="model-456",
    )

    prediction = result.predictions[0]

    assert prediction.prediction_id == "prediction-123"
    assert prediction.model_id == "model-456"
