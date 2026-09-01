from __future__ import annotations

from collections.abc import Iterable

from .models import (
    DatasetVersion,
    ModelStatus,
    ModelVersion,
)


class ModelRegistry:
    """
    Deterministic in-memory registry for Layer 10 ML model versions.

    The registry enforces unique model versions, dataset/feature
    compatibility, controlled lifecycle transitions, and deterministic
    lookup of active deployments.
    """

    _ALLOWED_TRANSITIONS: dict[ModelStatus, frozenset[ModelStatus]] = {
        ModelStatus.DRAFT: frozenset({
            ModelStatus.TRAINING,
            ModelStatus.RETIRED,
        }),
        ModelStatus.TRAINING: frozenset({
            ModelStatus.VALIDATED,
            ModelStatus.RETIRED,
        }),
        ModelStatus.VALIDATED: frozenset({
            ModelStatus.APPROVED,
            ModelStatus.TRAINING,
            ModelStatus.RETIRED,
        }),
        ModelStatus.APPROVED: frozenset({
            ModelStatus.DEPLOYED,
            ModelStatus.RETIRED,
        }),
        ModelStatus.DEPLOYED: frozenset({
            ModelStatus.RETIRED,
        }),
        ModelStatus.RETIRED: frozenset(),
    }

    def __init__(
        self,
        models: Iterable[ModelVersion] = (),
    ) -> None:
        self._models: dict[tuple[str, str], ModelVersion] = {}

        for model in models:
            self.register(model)

    @property
    def count(self) -> int:
        return len(self._models)

    def register(
        self,
        model: ModelVersion,
        *,
        dataset: DatasetVersion | None = None,
    ) -> ModelVersion:
        if not isinstance(model, ModelVersion):
            raise TypeError(
                "model must be a ModelVersion"
            )

        key = (model.model_id, model.version)

        if key in self._models:
            raise ValueError(
                f"model version already registered: "
                f"{model.model_id}:{model.version}"
            )

        if dataset is not None:
            self._validate_dataset_compatibility(
                model,
                dataset,
            )

        self._models[key] = model
        return model

    def get(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:
        if not model_id.strip():
            raise ValueError("model_id is required")

        if not version.strip():
            raise ValueError("model version is required")

        try:
            return self._models[(model_id, version)]
        except KeyError as exc:
            raise KeyError(
                f"model version not found: {model_id}:{version}"
            ) from exc

    def exists(
        self,
        model_id: str,
        version: str,
    ) -> bool:
        return (model_id, version) in self._models

    def list_versions(
        self,
        model_id: str,
    ) -> tuple[ModelVersion, ...]:
        if not model_id.strip():
            raise ValueError("model_id is required")

        return tuple(
            sorted(
                (
                    model
                    for model in self._models.values()
                    if model.model_id == model_id
                ),
                key=lambda model: model.version,
            )
        )

    def list_by_status(
        self,
        status: ModelStatus,
    ) -> tuple[ModelVersion, ...]:
        return tuple(
            sorted(
                (
                    model
                    for model in self._models.values()
                    if model.status == status
                ),
                key=lambda model: (
                    model.model_id,
                    model.version,
                ),
            )
        )

    def transition(
        self,
        model_id: str,
        version: str,
        status: ModelStatus,
    ) -> ModelVersion:
        current = self.get(model_id, version)

        if status == current.status:
            return current

        allowed = self._ALLOWED_TRANSITIONS[current.status]

        if status not in allowed:
            raise ValueError(
                f"invalid model status transition: "
                f"{current.status.value} -> {status.value}"
            )

        updated = ModelVersion(
            model_id=current.model_id,
            version=current.version,
            task_type=current.task_type,
            model_type=current.model_type,
            status=status,
            dataset_id=current.dataset_id,
            dataset_version=current.dataset_version,
            feature_version=current.feature_version,
            training_run_id=current.training_run_id,
            feature_names=current.feature_names,
            created_at=current.created_at,
            metadata=current.metadata,
        )

        self._models[(model_id, version)] = updated

        return updated

    def approve(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:
        return self.transition(
            model_id,
            version,
            ModelStatus.APPROVED,
        )

    def deploy(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:
        model = self.get(model_id, version)

        if model.status != ModelStatus.APPROVED:
            raise ValueError(
                "only approved models can be deployed"
            )

        deployed = self.list_deployed()

        for existing in deployed:
            if existing.model_id == model_id:
                self.transition(
                    existing.model_id,
                    existing.version,
                    ModelStatus.RETIRED,
                )

        return self.transition(
            model_id,
            version,
            ModelStatus.DEPLOYED,
        )

    def retire(
        self,
        model_id: str,
        version: str,
    ) -> ModelVersion:
        return self.transition(
            model_id,
            version,
            ModelStatus.RETIRED,
        )

    def list_deployed(self) -> tuple[ModelVersion, ...]:
        return self.list_by_status(ModelStatus.DEPLOYED)

    def resolve_deployed(
        self,
        model_id: str,
    ) -> ModelVersion:
        deployed = tuple(
            model
            for model in self.list_deployed()
            if model.model_id == model_id
        )

        if not deployed:
            raise LookupError(
                f"no deployed model found: {model_id}"
            )

        if len(deployed) > 1:
            raise RuntimeError(
                f"multiple deployed versions found: {model_id}"
            )

        return deployed[0]

    def validate_compatibility(
        self,
        model: ModelVersion,
        dataset: DatasetVersion,
    ) -> bool:
        self._validate_dataset_compatibility(
            model,
            dataset,
        )
        return True

    @staticmethod
    def _validate_dataset_compatibility(
        model: ModelVersion,
        dataset: DatasetVersion,
    ) -> None:
        if model.dataset_id != dataset.dataset_id:
            raise ValueError(
                "model dataset_id does not match dataset"
            )

        if model.dataset_version != dataset.version:
            raise ValueError(
                "model dataset_version does not match dataset"
            )

        if model.feature_version != dataset.feature_version:
            raise ValueError(
                "model feature_version does not match dataset"
            )


__all__ = [
    "ModelRegistry",
]
