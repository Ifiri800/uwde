from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class MLTaskType(StrEnum):
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    ANOMALY_DETECTION = "anomaly_detection"
    PROBABILITY_ESTIMATION = "probability_estimation"
    MULTI_OUTPUT = "multi_output"
    CLUSTERING = "clustering"
    DATA_FUSION = "data_fusion"


class ModelType(StrEnum):
    LINEAR = "linear"
    TREE = "tree"
    ENSEMBLE = "ensemble"
    NEURAL_NETWORK = "neural_network"
    STATISTICAL = "statistical"
    ANOMALY = "anomaly"
    HYBRID = "hybrid"


class ModelStatus(StrEnum):
    DRAFT = "draft"
    TRAINING = "training"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    RETIRED = "retired"


class DatasetStatus(StrEnum):
    CREATED = "created"
    VALIDATED = "validated"
    TRAINING = "training"
    LOCKED = "locked"
    RETIRED = "retired"


@dataclass(frozen=True)
class TrainingConfig:
    task_type: MLTaskType
    model_type: ModelType
    feature_names: tuple[str, ...] = ()
    target_name: str | None = None
    validation_fraction: float = 0.2
    test_fraction: float = 0.2
    random_seed: int | None = None
    hyperparameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 < self.validation_fraction < 1.0:
            raise ValueError(
                "validation_fraction must be between 0 and 1"
            )

        if not 0.0 < self.test_fraction < 1.0:
            raise ValueError(
                "test_fraction must be between 0 and 1"
            )

        if (
            self.validation_fraction
            + self.test_fraction
            >= 1.0
        ):
            raise ValueError(
                "validation_fraction + test_fraction "
                "must be less than 1"
            )

        if any(
            not name.strip()
            for name in self.feature_names
        ):
            raise ValueError(
                "feature_names cannot contain empty names"
            )

        if self.target_name is not None:
            if not self.target_name.strip():
                raise ValueError(
                    "target_name cannot be empty"
                )


@dataclass(frozen=True)
class DatasetVersion:
    dataset_id: str
    version: str
    status: DatasetStatus
    feature_version: str
    record_count: int
    source_ids: tuple[str, ...] = ()
    created_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")

        if not self.version.strip():
            raise ValueError("dataset version is required")

        if not self.feature_version.strip():
            raise ValueError(
                "feature_version is required"
            )

        if self.record_count < 0:
            raise ValueError(
                "record_count cannot be negative"
            )


@dataclass(frozen=True)
class ModelMetric:
    name: str
    value: float
    dataset_split: str = "validation"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("metric name is required")

        if not float("-inf") < self.value < float("inf"):
            raise ValueError(
                "metric value must be finite"
            )


@dataclass(frozen=True)
class ModelEvaluation:
    evaluation_id: str
    model_id: str
    model_version: str
    metrics: tuple[ModelMetric, ...] = ()
    passed: bool = False
    evaluated_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def metric_count(self) -> int:
        return len(self.metrics)


@dataclass(frozen=True)
class ModelVersion:
    model_id: str
    version: str
    task_type: MLTaskType
    model_type: ModelType
    status: ModelStatus
    dataset_id: str
    dataset_version: str
    feature_version: str
    training_run_id: str
    feature_names: tuple[str, ...] = ()
    created_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        required = {
            "model_id": self.model_id,
            "version": self.version,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "feature_version": self.feature_version,
            "training_run_id": self.training_run_id,
        }

        for name, value in required.items():
            if not value.strip():
                raise ValueError(
                    f"{name} is required"
                )


@dataclass(frozen=True)
class PredictionRequest:
    request_id: str
    entity_id: str
    model_id: str
    model_version: str
    features: Mapping[str, float]
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    requested_at: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in {
            "request_id": self.request_id,
            "entity_id": self.entity_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
        }.items():
            if not value.strip():
                raise ValueError(
                    f"{name} is required"
                )

        for name, value in self.features.items():
            if not name.strip():
                raise ValueError(
                    "feature names cannot be empty"
                )

            if not float("-inf") < value < float("inf"):
                raise ValueError(
                    f"feature '{name}' must be finite"
                )


@dataclass(frozen=True)
class PredictionResponse:
    request_id: str
    entity_id: str
    model_id: str
    model_version: str
    value: float
    confidence: float
    feature_version: str | None = None
    dataset_version: str | None = None
    training_run_id: str | None = None
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    explanation: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")

        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if not self.model_id.strip():
            raise ValueError("model_id is required")

        if not self.model_version.strip():
            raise ValueError(
                "model_version is required"
            )

        if not float("-inf") < self.value < float("inf"):
            raise ValueError(
                "prediction value must be finite"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )


@dataclass(frozen=True)
class DriftAssessment:
    assessment_id: str
    drift_type: str
    score: float
    threshold: float
    detected: bool
    feature_name: str | None = None
    reference_version: str | None = None
    current_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.assessment_id.strip():
            raise ValueError(
                "assessment_id is required"
            )

        if not self.drift_type.strip():
            raise ValueError(
                "drift_type is required"
            )

        if self.score < 0.0:
            raise ValueError(
                "drift score cannot be negative"
            )

        if self.threshold < 0.0:
            raise ValueError(
                "drift threshold cannot be negative"
            )
