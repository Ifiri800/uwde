import pytest

from backend.app.services.intelligence.methane.intelligence.equipment_risk import (
    EquipmentRiskPredictionEngine,
    predict_equipment_risk,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligenceType,
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


def test_predicts_equipment_risk():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("leak_frequency", 0.8)],
    )

    assert result.intelligence_type == IntelligenceType.EQUIPMENT_RISK
    assert result.prediction_count == 1
    assert result.predictions[0].value == pytest.approx(0.8)


def test_prediction_uses_deterministic_method():
    result = EquipmentRiskPredictionEngine().predict(
        "equipment-001",
        [make_feature("failure_indicator", 0.7)],
    )

    prediction = result.predictions[0]

    assert prediction.method == IntelligenceMethod.DETERMINISTIC
    assert prediction.model_id == "deterministic-risk-baseline"


def test_confidence_weighted_risk():
    result = predict_equipment_risk(
        "equipment-001",
        [
            make_feature("indicator_a", 0.2, 1.0),
            make_feature("indicator_b", 0.8, 0.5),
        ],
    )

    assert result.predictions[0].value == pytest.approx(0.4)


def test_values_above_one_are_bounded():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("indicator", 5.0)],
    )

    assert result.predictions[0].value == 1.0


def test_negative_values_are_bounded():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("indicator", -5.0)],
    )

    assert result.predictions[0].value == 0.0


def test_confidence_is_average_feature_confidence():
    result = predict_equipment_risk(
        "equipment-001",
        [
            make_feature("a", 0.5, 0.8),
            make_feature("b", 0.9, 0.6),
        ],
    )

    assert result.confidence == pytest.approx(0.7)


def test_features_are_normalized():
    result = predict_equipment_risk(
        "equipment-001",
        [
            make_feature("z_feature", 0.8),
            make_feature("a_feature", 0.2),
        ],
    )

    assert tuple(
        feature.name
        for feature in result.features
    ) == ("a_feature", "z_feature")


def test_signal_and_evidence_ids_are_preserved():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("indicator", 0.7)],
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )

    assert result.signal_ids == ("signal-1",)
    assert result.evidence_ids == ("evidence-1",)

    prediction = result.predictions[0]

    assert prediction.signal_ids == ("signal-1",)
    assert prediction.evidence_ids == ("evidence-1",)


def test_empty_features_are_rejected():
    with pytest.raises(
        ValueError,
        match="at least one feature is required",
    ):
        predict_equipment_risk(
            "equipment-001",
            [],
        )


def test_empty_entity_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="entity_id is required",
    ):
        predict_equipment_risk(
            "",
            [make_feature("indicator", 0.5)],
        )


def test_non_string_entity_id_is_rejected():
    with pytest.raises(TypeError, match="entity_id must be a string"):
        predict_equipment_risk(
            123,
            [make_feature("indicator", 0.5)],
        )


def test_explanation_is_present():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("indicator", 0.6)],
    )

    assert result.predictions[0].explanation
    assert "Equipment risk prediction" in (
        result.predictions[0].explanation
    )


def test_custom_prediction_and_model_ids():
    result = predict_equipment_risk(
        "equipment-001",
        [make_feature("indicator", 0.6)],
        prediction_id="prediction-001",
        model_id="model-001",
    )

    prediction = result.predictions[0]

    assert prediction.prediction_id == "prediction-001"
    assert prediction.model_id == "model-001"


def test_deterministic_repeated_results():
    features = [
        make_feature("a", 0.3, 0.9),
        make_feature("b", 0.8, 0.7),
    ]

    first = predict_equipment_risk(
        "equipment-001",
        features,
    )

    second = predict_equipment_risk(
        "equipment-001",
        features,
    )

    assert first.predictions[0].value == second.predictions[0].value
    assert first.confidence == second.confidence
