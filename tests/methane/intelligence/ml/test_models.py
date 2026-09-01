import pytest

from backend.app.services.intelligence.methane.intelligence.ml.models import (
    DatasetStatus,
    DatasetVersion,
    DriftAssessment,
    MLTaskType,
    ModelEvaluation,
    ModelMetric,
    ModelStatus,
    ModelType,
    ModelVersion,
    PredictionRequest,
    PredictionResponse,
    TrainingConfig,
)


def test_training_config_defaults():
    config = TrainingConfig(
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.TREE,
    )

    assert config.validation_fraction == 0.2
    assert config.test_fraction == 0.2


def test_training_config_rejects_invalid_split():
    with pytest.raises(ValueError):
        TrainingConfig(
            task_type=MLTaskType.REGRESSION,
            model_type=ModelType.TREE,
            validation_fraction=0.6,
            test_fraction=0.5,
        )


def test_dataset_version():
    dataset = DatasetVersion(
        dataset_id="methane-dataset",
        version="1.0.0",
        status=DatasetStatus.VALIDATED,
        feature_version="features-1",
        record_count=100,
    )

    assert dataset.record_count == 100


def test_dataset_rejects_negative_records():
    with pytest.raises(ValueError):
        DatasetVersion(
            dataset_id="dataset",
            version="1",
            status=DatasetStatus.CREATED,
            feature_version="features-1",
            record_count=-1,
        )


def test_model_metric():
    metric = ModelMetric(
        name="rmse",
        value=1.25,
    )

    assert metric.name == "rmse"


def test_model_evaluation_metric_count():
    evaluation = ModelEvaluation(
        evaluation_id="eval-1",
        model_id="model-1",
        model_version="1.0.0",
        metrics=(
            ModelMetric("rmse", 1.0),
            ModelMetric("mae", 0.5),
        ),
        passed=True,
    )

    assert evaluation.metric_count == 2


def test_model_version_lineage():
    model = ModelVersion(
        model_id="methane-model",
        version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.ENSEMBLE,
        status=ModelStatus.VALIDATED,
        dataset_id="dataset-1",
        dataset_version="1.0.0",
        feature_version="features-1",
        training_run_id="run-1",
    )

    assert model.dataset_version == "1.0.0"
    assert model.feature_version == "features-1"


def test_model_version_requires_lineage():
    with pytest.raises(ValueError):
        ModelVersion(
            model_id="model",
            version="1",
            task_type=MLTaskType.REGRESSION,
            model_type=ModelType.TREE,
            status=ModelStatus.DRAFT,
            dataset_id="",
            dataset_version="1",
            feature_version="features",
            training_run_id="run",
        )


def test_prediction_request():
    request = PredictionRequest(
        request_id="request-1",
        entity_id="facility-1",
        model_id="model-1",
        model_version="1.0.0",
        features={
            "emission_rate": 120.0,
            "pressure": 0.8,
        },
    )

    assert request.features["emission_rate"] == 120.0


def test_prediction_request_rejects_nonfinite_feature():
    with pytest.raises(ValueError):
        PredictionRequest(
            request_id="request-1",
            entity_id="facility-1",
            model_id="model-1",
            model_version="1.0.0",
            features={"emission_rate": float("inf")},
        )


def test_prediction_response():
    response = PredictionResponse(
        request_id="request-1",
        entity_id="facility-1",
        model_id="model-1",
        model_version="1.0.0",
        value=0.82,
        confidence=0.91,
        feature_version="features-1",
        dataset_version="dataset-1",
        training_run_id="run-1",
        explanation="High-risk equipment pattern detected.",
    )

    assert response.confidence == 0.91


def test_prediction_response_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        PredictionResponse(
            request_id="request",
            entity_id="facility",
            model_id="model",
            model_version="1",
            value=0.5,
            confidence=1.5,
        )


def test_drift_assessment():
    assessment = DriftAssessment(
        assessment_id="drift-1",
        drift_type="feature",
        score=0.31,
        threshold=0.20,
        detected=True,
        feature_name="pressure",
    )

    assert assessment.detected is True


def test_drift_rejects_negative_score():
    with pytest.raises(ValueError):
        DriftAssessment(
            assessment_id="drift",
            drift_type="feature",
            score=-1,
            threshold=0.2,
            detected=False,
        )
