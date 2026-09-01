import pytest

from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligenceType,
)
from backend.app.services.intelligence.methane.intelligence.prediction import (
    EmissionPredictionEngine,
    predict_emissions,
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


def test_prediction_returns_emission_prediction():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [
            feature("emission_rate", 100.0),
        ],
    )

    assert result.entity_id == "facility-001"
    assert (
        result.intelligence_type
        == IntelligenceType.EMISSION_PREDICTION
    )
    assert result.prediction_count == 1

    prediction = result.predictions[0]

    assert prediction.method == IntelligenceMethod.DETERMINISTIC
    assert prediction.value == 100.0
    assert prediction.confidence == 1.0


def test_prediction_uses_confidence_weighted_features():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [
            feature("a", 100.0, 1.0),
            feature("b", 200.0, 0.5),
        ],
    )

    prediction = result.predictions[0]

    assert prediction.value == pytest.approx(
        (100.0 + 100.0) / 1.5
    )


def test_prediction_confidence_is_average_feature_confidence():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [
            feature("a", 100.0, 1.0),
            feature("b", 200.0, 0.6),
            feature("c", 300.0, 0.8),
        ],
    )

    assert result.confidence == pytest.approx(
        (1.0 + 0.6 + 0.8) / 3.0
    )

    assert (
        result.predictions[0].confidence
        == result.confidence
    )


def test_prediction_features_are_deterministically_sorted():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [
            feature("z_feature", 30.0),
            feature("a_feature", 10.0),
            feature("m_feature", 20.0),
        ],
    )

    assert [
        item.name
        for item in result.features
    ] == [
        "a_feature",
        "m_feature",
        "z_feature",
    ]

    assert result.predictions[0].feature_names == (
        "a_feature",
        "m_feature",
        "z_feature",
    )


def test_prediction_preserves_signal_and_evidence_ids():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [feature("emission_rate", 50.0)],
        signal_ids=("signal-1", "signal-2"),
        evidence_ids=("evidence-1", "evidence-2"),
    )

    prediction = result.predictions[0]

    assert prediction.signal_ids == (
        "signal-1",
        "signal-2",
    )

    assert prediction.evidence_ids == (
        "evidence-1",
        "evidence-2",
    )

    assert result.signal_ids == (
        "signal-1",
        "signal-2",
    )

    assert result.evidence_ids == (
        "evidence-1",
        "evidence-2",
    )


def test_prediction_preserves_prediction_and_model_ids():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [feature("emission_rate", 50.0)],
        prediction_id="prediction-123",
        model_id="model-456",
    )

    prediction = result.predictions[0]

    assert prediction.prediction_id == "prediction-123"
    assert prediction.model_id == "model-456"


def test_prediction_requires_entity_id():
    with pytest.raises(ValueError, match="entity_id is required"):
        EmissionPredictionEngine().predict(
            "",
            [feature("emission_rate", 50.0)],
        )


def test_prediction_requires_features():
    with pytest.raises(
        ValueError,
        match="at least one feature is required",
    ):
        EmissionPredictionEngine().predict(
            "facility-001",
            [],
        )


def test_prediction_requires_string_entity_id():
    with pytest.raises(
        TypeError,
        match="entity_id must be a string",
    ):
        EmissionPredictionEngine().predict(
            123,  # type: ignore[arg-type]
            [feature("emission_rate", 50.0)],
        )


def test_prediction_explanation_is_present():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [feature("emission_rate", 75.0)],
    )

    prediction = result.predictions[0]

    assert prediction.explanation
    assert "deterministic" in prediction.explanation.lower()


def test_prediction_to_dict_is_serializable():
    result = EmissionPredictionEngine().predict(
        "facility-001",
        [feature("emission_rate", 75.0)],
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )

    data = result.predictions[0].to_dict()

    assert data["entity_id"] == "facility-001"
    assert data["intelligence_type"] == "emission_prediction"
    assert data["method"] == "deterministic"
    assert data["value"] == 75.0
    assert data["confidence"] == 1.0
    assert data["signal_ids"] == ["signal-1"]
    assert data["evidence_ids"] == ["evidence-1"]


def test_predict_emissions_convenience_function():
    result = predict_emissions(
        "facility-001",
        [feature("emission_rate", 125.0)],
    )

    assert result.entity_id == "facility-001"
    assert result.value if hasattr(result, "value") else True
    assert result.predictions[0].value == 125.0
