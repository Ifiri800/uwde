import pytest

from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceMethod,
    IntelligencePrediction,
    IntelligenceResult,
    IntelligenceType,
)


def test_intelligence_feature_accepts_valid_values():
    feature = IntelligenceFeature(
        name="emission_rate",
        value=0.75,
        source="reconciled_estimate",
        unit="kg/h",
        confidence=0.9,
    )

    assert feature.name == "emission_rate"
    assert feature.value == 0.75
    assert feature.confidence == 0.9


def test_intelligence_feature_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        IntelligenceFeature(
            name="emission_rate",
            value=0.75,
            source="test",
            confidence=1.1,
        )


def test_intelligence_prediction_serializes():
    prediction = IntelligencePrediction(
        prediction_id="pred-001",
        entity_id="facility-001",
        intelligence_type=(
            IntelligenceType.EMISSION_PREDICTION
        ),
        method=IntelligenceMethod.DETERMINISTIC,
        value=0.82,
        confidence=0.91,
        feature_names=("emission_rate",),
        signal_ids=("signal-001",),
        evidence_ids=("evidence-001",),
        explanation="Prediction is supported by the observed emission trend.",
    )

    data = prediction.to_dict()

    assert data["prediction_id"] == "pred-001"
    assert data["entity_id"] == "facility-001"
    assert data["intelligence_type"] == "emission_prediction"
    assert data["method"] == "deterministic"
    assert data["feature_names"] == ["emission_rate"]
    assert data["signal_ids"] == ["signal-001"]
    assert data["evidence_ids"] == ["evidence-001"]


def test_intelligence_prediction_rejects_negative_value():
    with pytest.raises(ValueError):
        IntelligencePrediction(
            prediction_id="pred-001",
            entity_id="facility-001",
            intelligence_type=IntelligenceType.ANOMALY,
            method=IntelligenceMethod.STATISTICAL,
            value=-1.0,
            confidence=0.8,
            explanation="Invalid negative prediction.",
        )


def test_intelligence_result_counts_predictions_and_features():
    feature = IntelligenceFeature(
        name="emission_rate",
        value=0.75,
        source="reconciled_estimate",
    )

    prediction = IntelligencePrediction(
        prediction_id="pred-001",
        entity_id="facility-001",
        intelligence_type=IntelligenceType.ANOMALY,
        method=IntelligenceMethod.STATISTICAL,
        value=0.8,
        confidence=0.9,
        explanation="Anomalous emission behavior detected.",
    )

    result = IntelligenceResult(
        entity_id="facility-001",
        intelligence_type=IntelligenceType.ANOMALY,
        predictions=(prediction,),
        features=(feature,),
        confidence=0.9,
        warnings=("Limited historical observations.",),
    )

    assert result.prediction_count == 1
    assert result.feature_count == 1
    assert result.has_warnings is True


def test_intelligence_result_serializes():
    result = IntelligenceResult(
        entity_id="facility-001",
        intelligence_type=IntelligenceType.ANOMALY,
        confidence=0.85,
        reasons=("Observed deviation from baseline.",),
    )

    data = result.to_dict()

    assert data["entity_id"] == "facility-001"
    assert data["intelligence_type"] == "anomaly"
    assert data["confidence"] == 0.85
    assert data["reasons"] == [
        "Observed deviation from baseline."
    ]
