import pytest

from backend.app.services.intelligence.methane.intelligence.anomaly import (
    MethaneAnomalyDetector,
    detect_methane_anomaly,
)
from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
    IntelligenceType,
)


def make_feature(
    name: str,
    value: float,
) -> IntelligenceFeature:
    return IntelligenceFeature(
        name=name,
        value=value,
        source="test",
        confidence=0.9,
    )


def test_anomaly_detector_returns_layer_10_result():
    features = [
        make_feature(
            "mean_relative_discrepancy",
            0.30,
        ),
        make_feature(
            "maximum_relative_discrepancy",
            0.40,
        ),
        make_feature(
            "reconciled_uncertainty",
            0.10,
        ),
        make_feature(
            "quantification_method_diversity",
            1.0,
        ),
    ]

    result = detect_methane_anomaly(
        "facility-001",
        features,
    )

    assert result.entity_id == "facility-001"
    assert result.intelligence_type == IntelligenceType.ANOMALY
    assert result.prediction_count == 1
    assert result.feature_count == 4


def test_anomaly_score_is_bounded():
    features = [
        make_feature(
            "mean_relative_discrepancy",
            10.0,
        ),
        make_feature(
            "maximum_relative_discrepancy",
            10.0,
        ),
        make_feature(
            "reconciled_uncertainty",
            10.0,
        ),
    ]

    result = detect_methane_anomaly(
        "facility-001",
        features,
    )

    assert 0.0 <= result.predictions[0].value <= 1.0


def test_high_discrepancy_produces_anomaly_signal():
    features = [
        make_feature(
            "mean_relative_discrepancy",
            0.80,
        ),
        make_feature(
            "maximum_relative_discrepancy",
            0.90,
        ),
        make_feature(
            "reconciled_uncertainty",
            0.50,
        ),
        make_feature(
            "quantification_method_diversity",
            1.0,
        ),
    ]

    result = MethaneAnomalyDetector(
        threshold=0.50,
    ).detect(
        "facility-001",
        features,
    )

    assert result.predictions[0].value >= 0.50
    assert any(
        "discrepancy" in reason
        for reason in result.reasons
    )


def test_low_discrepancy_can_remain_below_threshold():
    features = [
        make_feature(
            "mean_relative_discrepancy",
            0.01,
        ),
        make_feature(
            "maximum_relative_discrepancy",
            0.02,
        ),
        make_feature(
            "reconciled_uncertainty",
            0.01,
        ),
        make_feature(
            "quantification_method_diversity",
            1.0,
        ),
    ]

    result = detect_methane_anomaly(
        "facility-001",
        features,
    )

    assert result.predictions[0].value < 0.50


def test_signal_and_evidence_traceability_is_preserved():
    result = detect_methane_anomaly(
        "facility-001",
        [
            make_feature(
                "mean_relative_discrepancy",
                0.10,
            ),
        ],
        signal_ids=("signal-001",),
        evidence_ids=("evidence-001",),
    )

    prediction = result.predictions[0]

    assert prediction.signal_ids == (
        "signal-001",
    )
    assert prediction.evidence_ids == (
        "evidence-001",
    )


def test_invalid_threshold_is_rejected():
    with pytest.raises(ValueError):
        MethaneAnomalyDetector(
            threshold=1.5,
        )


def test_invalid_entity_id_is_rejected():
    with pytest.raises(ValueError):
        detect_methane_anomaly(
            "",
            [],
        )
