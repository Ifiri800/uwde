from __future__ import annotations

from collections.abc import Sequence

from .dataset import (
    DatasetBuilder,
    DatasetRecord,
    DatasetSplit,
)
from .evaluation import (
    ModelEvaluationEngine,
)
from .inference import (
    MLInferenceEngine,
    ModelExecutor,
)
from .models import (
    DatasetVersion,
    MLTaskType,
    ModelEvaluation,
    ModelVersion,
    PredictionRequest,
    PredictionResponse,
    TrainingConfig,
)
from .registry import ModelRegistry
from .training import (
    TrainingResult,
    train_model,
)


class MLOrchestrator:
    """
    End-to-end Layer 10 machine-learning workflow coordinator.

    Coordinates dataset preparation, deterministic splitting,
    training, evaluation, model registration, deployment,
    inference, and lifecycle operations without coupling the
    intelligence layer to a specific ML framework.
    """

    def __init__(
        self,
        *,
        registry: ModelRegistry | None = None,
    ) -> None:
        self.registry = registry or ModelRegistry()
        self.inference = MLInferenceEngine(
            self.registry,
        )
        self.evaluation = ModelEvaluationEngine()

    def prepare_dataset(
        self,
        *,
        dataset_id: str,
        version: str,
        records: Sequence[DatasetRecord],
        feature_names: Sequence[str],
        target_name: str | None = None,
        source_ids: tuple[str, ...] = (),
        feature_version: str = "1.0.0",
    ) -> DatasetVersion:

        builder = DatasetBuilder(
            feature_names=feature_names,
            target_name=target_name,
        )

        return builder.build(
            dataset_id=dataset_id,
            version=version,
            records=records,
            source_ids=source_ids,
            feature_version=feature_version,
        )

    def split_dataset(
        self,
        *,
        records: Sequence[DatasetRecord],
        validation_fraction: float = 0.2,
        test_fraction: float = 0.2,
        random_seed: int | None = None,
    ) -> DatasetSplit:

        if not records:
            raise ValueError(
                "at least one record is required"
            )

        builder = DatasetBuilder(
            feature_names=tuple(
                records[0].features.keys()
            ),
        )

        return builder.split(
            records,
            validation_fraction=validation_fraction,
            test_fraction=test_fraction,
            random_seed=random_seed,
        )

    def train(
        self,
        *,
        run_id: str,
        model_id: str,
        config: TrainingConfig,
        dataset_split: DatasetSplit,
        feature_names: Sequence[str] | None = None,
    ) -> TrainingResult:

        return train_model(
            run_id=run_id,
            model_id=model_id,
            config=config,
            dataset_split=dataset_split,
            feature_names=feature_names,
        )

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

        return self.evaluation.evaluate(
            evaluation_id=evaluation_id,
            model_id=model_id,
            model_version=model_version,
            task_type=task_type,
            predictions=predictions,
            targets=targets,
            dataset_split=dataset_split,
            metric_thresholds=metric_thresholds,
        )

    def register(
        self,
        model: ModelVersion,
        *,
        dataset: DatasetVersion | None = None,
    ) -> ModelVersion:

        return self.registry.register(
            model,
            dataset=dataset,
        )

    def approve(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:

        return self.registry.approve(
            model_id,
            version,
        )

    def deploy(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:

        return self.registry.deploy(
            model_id,
            version,
        )

    def register_executor(
        self,
        model_id: str,
        model_version: str,
        executor: ModelExecutor,
    ) -> None:

        self.inference.register_executor(
            model_id,
            model_version,
            executor,
        )

    def predict(
        self,
        request: PredictionRequest,
        *,
        confidence: float = 1.0,
    ) -> PredictionResponse:

        return self.inference.predict(
            request,
            confidence=confidence,
        )


__all__ = [
    "MLOrchestrator",
]
