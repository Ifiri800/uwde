from __future__ import annotations

import pytest

from backend.app.services.intelligence.methane.intelligence.ml.models import (
    ModelMetric,
)
from backend.app.services.intelligence.methane.intelligence.ml.monitoring import (
    MLMonitoringEngine,
    PerformanceAssessment,
    PredictionMonitoring,
)


def test_prediction_monitoring():
    result = MLMonitoringEngine().monitor_predictions(
        [1.0, 2.0, 3.0],
        [0.8, 0.9, 1.0],
    )

    assert isinstance(result, PredictionMonitoring)
    assert result.prediction_count == 3
    assert result.mean_prediction == 2.0
    assert result.mean_confidence == pytest.approx(0.9)
    assert result.minimum_confidence == 0.8
    assert result.maximum_confidence == 1.0


def test_empty_prediction_batch():
    result = MLMonitoringEngine().monitor_predictions(
        [],
        [],
    )

    assert result.prediction_count == 0
    assert result.mean_prediction == 0.0


def test_prediction_length_mismatch_rejected():
    with pytest.raises(ValueError):
        MLMonitoringEngine().monitor_predictions(
            [1.0],
            [0.5, 0.6],
        )


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        MLMonitoringEngine().monitor_predictions(
            [1.0],
            [1.5],
        )


def test_non_finite_prediction_rejected():
    with pytest.raises(ValueError):
        MLMonitoringEngine().monitor_predictions(
            [float("inf")],
            [0.5],
        )


def test_no_feature_drift():
    result = MLMonitoringEngine().assess_feature_drift(
        "temperature",
        [1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0],
        threshold=0.1,
    )

    assert result.detected is False
    assert result.score == 0.0


def test_feature_drift_detected():
    result = MLMonitoringEngine().assess_feature_drift(
        "temperature",
        [1.0, 1.0, 1.0],
        [2.0, 2.0, 2.0],
        threshold=0.1,
    )

    assert result.detected is True
    assert result.score >= 0.1


def test_feature_drift_contains_versions():
    result = MLMonitoringEngine().assess_feature_drift(
        "temperature",
        [1.0, 2.0],
        [1.0, 2.0],
        reference_version="feature-1",
        current_version="feature-2",
    )

    assert result.reference_version == "feature-1"
    assert result.current_version == "feature-2"


def test_empty_reference_rejected():
    with pytest.raises(ValueError):
        MLMonitoringEngine().assess_feature_drift(
            "temperature",
            [],
            [1.0],
        )


def test_empty_current_rejected():
    with pytest.raises(ValueError):
        MLMonitoringEngine().assess_feature_drift(
            "temperature",
            [1.0],
            [],
        )


def test_performance_not_degraded():
    metric = ModelMetric(
        name="mae",
        value=0.05,
    )

    result = MLMonitoringEngine().assess_performance(
        metric,
        baseline_value=0.10,
        threshold=0.1,
    )

    assert isinstance(result, PerformanceAssessment)
    assert result.degraded is False


def test_performance_degraded():
    metric = ModelMetric(
        name="mae",
        value=0.15,
    )

    result = MLMonitoringEngine().assess_performance(
        metric,
        baseline_value=0.10,
        threshold=0.1,
    )

    assert result.degraded is True
    assert result.degradation == pytest.approx(0.5)


def test_invalid_performance_threshold():
    metric = ModelMetric(
        name="mae",
        value=0.1,
    )

    with pytest.raises(ValueError):
        MLMonitoringEngine().assess_performance(
            metric,
            baseline_value=0.1,
            threshold=-0.1,
        )


def test_invalid_baseline():
    metric = ModelMetric(
        name="mae",
        value=0.1,
    )

    with pytest.raises(ValueError):
        MLMonitoringEngine().assess_performance(
            metric,
            baseline_value=-1.0,
        )
