from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .dataset import DatasetRecord, DatasetSplit
from .models import (
    ModelStatus,
    TrainingConfig,
)


@dataclass(frozen=True)
class TrainingResult:
    """Auditable result of an ML training operation."""

    run_id: str
    model_id: str
    status: ModelStatus

    task_type: str
    model_type: str

    train_count: int
    validation_count: int
    test_count: int

    feature_names: tuple[str, ...]
    target_name: str | None

    metrics: Mapping[str, float] = field(
        default_factory=dict
    )

    hyperparameters: Mapping[str, Any] = field(
        default_factory=dict
    )

    warnings: tuple[str, ...] = ()

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    @property
    def total_count(self) -> int:
        return (
            self.train_count
            + self.validation_count
            + self.test_count
        )

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


class TrainingEngine:
    """
    Deterministic ML training orchestration layer.

    This component establishes the training lifecycle and audit
    contract. Actual estimator implementations can be attached
    later without changing dataset, evaluation, registry,
    inference, or monitoring interfaces.
    """

    def train(
        self,
        *,
        run_id: str,
        model_id: str,
        config: TrainingConfig,
        dataset_split: DatasetSplit,
        feature_names: Sequence[str] | None = None,
    ) -> TrainingResult:

        if not isinstance(run_id, str):
            raise TypeError("run_id must be a string")

        if not run_id.strip():
            raise ValueError("run_id is required")

        if not isinstance(model_id, str):
            raise TypeError("model_id must be a string")

        if not model_id.strip():
            raise ValueError("model_id is required")

        features = tuple(
            feature_names
            if feature_names is not None
            else config.feature_names
        )

        if not features:
            raise ValueError(
                "at least one feature is required"
            )

        if any(
            not name.strip()
            for name in features
        ):
            raise ValueError(
                "feature names cannot be empty"
            )

        if (
            config.target_name is not None
            and config.target_name in features
        ):
            raise ValueError(
                "target cannot also be a training feature"
            )

        self._validate_split(
            dataset_split.train,
            features,
            "train",
        )

        self._validate_split(
            dataset_split.validation,
            features,
            "validation",
        )

        self._validate_split(
            dataset_split.test,
            features,
            "test",
        )

        warnings: list[str] = []

        if not dataset_split.train:
            raise ValueError(
                "training split cannot be empty"
            )

        if not dataset_split.validation:
            warnings.append(
                "validation split contains no records"
            )

        if not dataset_split.test:
            warnings.append(
                "test split contains no records"
            )

        metrics = self._training_metrics(
            dataset_split.train,
            config.target_name,
        )

        return TrainingResult(
            run_id=run_id,
            model_id=model_id,
            status=ModelStatus.TRAINING,
            task_type=config.task_type.value,
            model_type=config.model_type.value,
            train_count=dataset_split.train_count,
            validation_count=dataset_split.validation_count,
            test_count=dataset_split.test_count,
            feature_names=features,
            target_name=config.target_name,
            metrics=metrics,
            hyperparameters=dict(
                config.hyperparameters
            ),
            warnings=tuple(warnings),
            metadata={
                "random_seed": config.random_seed,
                "validation_fraction": (
                    config.validation_fraction
                ),
                "test_fraction": (
                    config.test_fraction
                ),
            },
        )

    @staticmethod
    def _validate_split(
        records: Sequence[DatasetRecord],
        feature_names: tuple[str, ...],
        split_name: str,
    ) -> None:

        for record in records:
            missing = tuple(
                name
                for name in feature_names
                if name not in record.features
            )

            if missing:
                raise ValueError(
                    f"{split_name} record "
                    f"'{record.record_id}' is missing "
                    f"features: {', '.join(missing)}"
                )

    @staticmethod
    def _training_metrics(
        records: Sequence[DatasetRecord],
        target_name: str | None,
    ) -> dict[str, float]:

        if target_name is None:
            return {
                "training_records": float(
                    len(records)
                )
            }

        targets = [
            record.target
            for record in records
            if isinstance(
                record.target,
                (int, float),
            )
        ]

        if not targets:
            return {
                "training_records": float(
                    len(records)
                )
            }

        mean_target = sum(
            float(value)
            for value in targets
        ) / len(targets)

        return {
            "training_records": float(
                len(records)
            ),
            "target_mean": mean_target,
            "target_count": float(
                len(targets)
            ),
        }


def train_model(
    *,
    run_id: str,
    model_id: str,
    config: TrainingConfig,
    dataset_split: DatasetSplit,
    feature_names: Sequence[str] | None = None,
) -> TrainingResult:

    return TrainingEngine().train(
        run_id=run_id,
        model_id=model_id,
        config=config,
        dataset_split=dataset_split,
        feature_names=feature_names,
    )
