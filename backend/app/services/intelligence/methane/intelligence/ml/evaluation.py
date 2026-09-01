from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

from .models import (
    MLTaskType,
    ModelEvaluation,
    ModelMetric,
)


class ModelEvaluationEngine:
    """
    Deterministic model evaluation engine.

    Provides baseline evaluation for regression and binary
    classification models. The engine is intentionally framework
    independent so trained models can later plug into the same
    evaluation contract.
    """

    def evaluate(
        self,
        *,
        evaluation_id: str,
        model_id: str,
        model_version: str,
        task_type: MLTaskType,
        predictions: Sequence[float],
        targets: Sequence[float],
        dataset_split: str = "validation",
        metric_thresholds: dict[str, float] | None = None,
    ) -> ModelEvaluation:

        if not evaluation_id.strip():
            raise ValueError("evaluation_id is required")

        if not model_id.strip():
            raise ValueError("model_id is required")

        if not model_version.strip():
            raise ValueError("model_version is required")

        if not dataset_split.strip():
            raise ValueError("dataset_split is required")

        if len(predictions) != len(targets):
            raise ValueError(
                "predictions and targets must have equal length"
            )

        if not predictions:
            raise ValueError(
                "at least one prediction is required"
            )

        thresholds = metric_thresholds or {}

        if task_type == MLTaskType.REGRESSION:
            metrics = self._regression_metrics(
                predictions,
                targets,
                dataset_split,
            )
        elif task_type == MLTaskType.CLASSIFICATION:
            metrics = self._classification_metrics(
                predictions,
                targets,
                dataset_split,
            )
        else:
            raise ValueError(
                f"unsupported evaluation task type: {task_type}"
            )

        passed = self._evaluate_thresholds(
            metrics,
            thresholds,
        )

        return ModelEvaluation(
            evaluation_id=evaluation_id,
            model_id=model_id,
            model_version=model_version,
            metrics=tuple(metrics),
            passed=passed,
            metadata={
                "task_type": task_type.value,
                "dataset_split": dataset_split,
                "metric_thresholds": dict(thresholds),
            },
        )

    @staticmethod
    def _regression_metrics(
        predictions: Sequence[float],
        targets: Sequence[float],
        dataset_split: str,
    ) -> list[ModelMetric]:

        errors = [
            float(prediction) - float(target)
            for prediction, target in zip(
                predictions,
                targets,
            )
        ]

        absolute_errors = [
            abs(error)
            for error in errors
        ]

        squared_errors = [
            error ** 2
            for error in errors
        ]

        mae = sum(absolute_errors) / len(errors)
        mse = sum(squared_errors) / len(errors)
        rmse = sqrt(mse)

        target_mean = sum(
            float(target)
            for target in targets
        ) / len(targets)

        ss_total = sum(
            (float(target) - target_mean) ** 2
            for target in targets
        )

        ss_residual = sum(squared_errors)

        r2 = (
            1.0 - (ss_residual / ss_total)
            if ss_total > 0.0
            else 0.0
        )

        return [
            ModelMetric(
                name="mae",
                value=mae,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="mse",
                value=mse,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="rmse",
                value=rmse,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="r2",
                value=r2,
                dataset_split=dataset_split,
            ),
        ]

    @staticmethod
    def _classification_metrics(
        predictions: Sequence[float],
        targets: Sequence[float],
        dataset_split: str,
    ) -> list[ModelMetric]:

        predicted_labels = [
            1 if float(prediction) >= 0.5 else 0
            for prediction in predictions
        ]

        target_labels = [
            1 if float(target) >= 0.5 else 0
            for target in targets
        ]

        true_positive = sum(
            prediction == 1 and target == 1
            for prediction, target in zip(
                predicted_labels,
                target_labels,
            )
        )

        true_negative = sum(
            prediction == 0 and target == 0
            for prediction, target in zip(
                predicted_labels,
                target_labels,
            )
        )

        false_positive = sum(
            prediction == 1 and target == 0
            for prediction, target in zip(
                predicted_labels,
                target_labels,
            )
        )

        false_negative = sum(
            prediction == 0 and target == 1
            for prediction, target in zip(
                predicted_labels,
                target_labels,
            )
        )

        total = len(target_labels)

        accuracy = (
            (true_positive + true_negative) / total
        )

        precision = (
            true_positive
            / (true_positive + false_positive)
            if true_positive + false_positive > 0
            else 0.0
        )

        recall = (
            true_positive
            / (true_positive + false_negative)
            if true_positive + false_negative > 0
            else 0.0
        )

        f1 = (
            2.0 * precision * recall
            / (precision + recall)
            if precision + recall > 0.0
            else 0.0
        )

        return [
            ModelMetric(
                name="accuracy",
                value=accuracy,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="precision",
                value=precision,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="recall",
                value=recall,
                dataset_split=dataset_split,
            ),
            ModelMetric(
                name="f1",
                value=f1,
                dataset_split=dataset_split,
            ),
        ]

    @staticmethod
    def _evaluate_thresholds(
        metrics: Sequence[ModelMetric],
        thresholds: dict[str, float],
    ) -> bool:

        if not thresholds:
            return True

        values = {
            metric.name: metric.value
            for metric in metrics
        }

        for metric_name, threshold in thresholds.items():
            if metric_name not in values:
                return False

            if values[metric_name] < threshold:
                return False

        return True


def evaluate_model(
    *,
    evaluation_id: str,
    model_id: str,
    model_version: str,
    task_type: MLTaskType,
    predictions: Sequence[float],
    targets: Sequence[float],
    dataset_split: str = "validation",
    metric_thresholds: dict[str, float] | None = None,
) -> ModelEvaluation:

    return ModelEvaluationEngine().evaluate(
        evaluation_id=evaluation_id,
        model_id=model_id,
        model_version=model_version,
        task_type=task_type,
        predictions=predictions,
        targets=targets,
        dataset_split=dataset_split,
        metric_thresholds=metric_thresholds,
    )
