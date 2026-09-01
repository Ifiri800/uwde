import pytest

from backend.app.services.intelligence.methane.intelligence.ml.evaluation import (
    ModelEvaluationEngine,
    evaluate_model,
)
from backend.app.services.intelligence.methane.intelligence.ml.models import (
    MLTaskType,
)


def test_regression_evaluation():
    result = ModelEvaluationEngine().evaluate(
        evaluation_id="eval-1",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=[10.0, 20.0, 30.0],
        targets=[10.0, 20.0, 30.0],
    )

    assert result.passed
    assert result.metric_count == 4
    assert result.metrics[0].value == 0.0


def test_regression_metrics_are_computed():
    result = evaluate_model(
        evaluation_id="eval-2",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=[11.0, 19.0],
        targets=[10.0, 20.0],
    )

    metrics = {
        metric.name: metric.value
        for metric in result.metrics
    }

    assert metrics["mae"] == 1.0
    assert metrics["mse"] == 1.0
    assert metrics["rmse"] == 1.0


def test_classification_evaluation():
    result = ModelEvaluationEngine().evaluate(
        evaluation_id="eval-3",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.CLASSIFICATION,
        predictions=[0.9, 0.1, 0.8, 0.2],
        targets=[1.0, 0.0, 1.0, 0.0],
    )

    assert result.passed

    metrics = {
        metric.name: metric.value
        for metric in result.metrics
    }

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_thresholds_can_fail_evaluation():
    result = ModelEvaluationEngine().evaluate(
        evaluation_id="eval-4",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.CLASSIFICATION,
        predictions=[0.9, 0.1],
        targets=[1.0, 0.0],
        metric_thresholds={
            "accuracy": 1.1,
        },
    )

    assert not result.passed


def test_thresholds_can_pass_evaluation():
    result = ModelEvaluationEngine().evaluate(
        evaluation_id="eval-5",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.CLASSIFICATION,
        predictions=[0.9, 0.1],
        targets=[1.0, 0.0],
        metric_thresholds={
            "accuracy": 0.9,
        },
    )

    assert result.passed


def test_mismatched_lengths_fail():
    with pytest.raises(ValueError):
        evaluate_model(
            evaluation_id="eval-6",
            model_id="model-1",
            model_version="1.0.0",
            task_type=MLTaskType.REGRESSION,
            predictions=[1.0],
            targets=[1.0, 2.0],
        )


def test_empty_predictions_fail():
    with pytest.raises(ValueError):
        evaluate_model(
            evaluation_id="eval-7",
            model_id="model-1",
            model_version="1.0.0",
            task_type=MLTaskType.REGRESSION,
            predictions=[],
            targets=[],
        )


def test_unsupported_task_fails():
    with pytest.raises(ValueError):
        evaluate_model(
            evaluation_id="eval-8",
            model_id="model-1",
            model_version="1.0.0",
            task_type=MLTaskType.CLUSTERING,
            predictions=[1.0],
            targets=[1.0],
        )


def test_dataset_split_is_preserved():
    result = evaluate_model(
        evaluation_id="eval-9",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=[1.0],
        targets=[1.0],
        dataset_split="test",
    )

    assert all(
        metric.dataset_split == "test"
        for metric in result.metrics
    )


def test_evaluation_metadata_contains_task():
    result = evaluate_model(
        evaluation_id="eval-10",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=[1.0],
        targets=[1.0],
    )

    assert result.metadata["task_type"] == "regression"


def test_unknown_threshold_metric_fails():
    result = evaluate_model(
        evaluation_id="eval-11",
        model_id="model-1",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=[1.0],
        targets=[1.0],
        metric_thresholds={
            "unknown_metric": 0.5,
        },
    )

    assert not result.passed


def test_invalid_identifiers_fail():
    with pytest.raises(ValueError):
        evaluate_model(
            evaluation_id="",
            model_id="model-1",
            model_version="1.0.0",
            task_type=MLTaskType.REGRESSION,
            predictions=[1.0],
            targets=[1.0],
        )
