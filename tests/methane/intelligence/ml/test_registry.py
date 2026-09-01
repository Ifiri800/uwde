from __future__ import annotations

import pytest

from backend.app.services.intelligence.methane.intelligence.ml.models import (
    DatasetStatus,
    DatasetVersion,
    MLTaskType,
    ModelStatus,
    ModelType,
    ModelVersion,
)
from backend.app.services.intelligence.methane.intelligence.ml.registry import (
    ModelRegistry,
)


def make_dataset(
    *,
    dataset_id: str = "methane",
    version: str = "1.0.0",
    feature_version: str = "1.0.0",
) -> DatasetVersion:
    return DatasetVersion(
        dataset_id=dataset_id,
        version=version,
        status=DatasetStatus.VALIDATED,
        feature_version=feature_version,
        record_count=100,
    )


def make_model(
    *,
    model_id: str = "emission-model",
    version: str = "1.0.0",
    status: ModelStatus = ModelStatus.DRAFT,
    dataset_id: str = "methane",
    dataset_version: str = "1.0.0",
    feature_version: str = "1.0.0",
) -> ModelVersion:
    return ModelVersion(
        model_id=model_id,
        version=version,
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.TREE,
        status=status,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        feature_version=feature_version,
        training_run_id="run-001",
        feature_names=("emission", "temperature"),
    )


def test_empty_registry():
    registry = ModelRegistry()

    assert registry.count == 0
    assert registry.list_deployed() == ()


def test_register_model():
    registry = ModelRegistry()
    model = make_model()

    result = registry.register(model)

    assert result == model
    assert registry.count == 1
    assert registry.get("emission-model", "1.0.0") == model


def test_duplicate_model_version_rejected():
    registry = ModelRegistry()
    model = make_model()

    registry.register(model)

    with pytest.raises(ValueError):
        registry.register(model)


def test_exists():
    registry = ModelRegistry([make_model()])

    assert registry.exists("emission-model", "1.0.0")
    assert not registry.exists("emission-model", "2.0.0")


def test_missing_model_rejected():
    registry = ModelRegistry()

    with pytest.raises(KeyError):
        registry.get("missing", "1.0.0")


def test_versions_are_deterministically_sorted():
    registry = ModelRegistry([
        make_model(version="2.0.0"),
        make_model(version="1.0.0"),
    ])

    versions = registry.list_versions("emission-model")

    assert tuple(model.version for model in versions) == (
        "1.0.0",
        "2.0.0",
    )


def test_valid_status_transition():
    registry = ModelRegistry([make_model()])

    result = registry.transition(
        "emission-model",
        "1.0.0",
        ModelStatus.TRAINING,
    )

    assert result.status == ModelStatus.TRAINING


def test_invalid_status_transition_rejected():
    registry = ModelRegistry([make_model()])

    with pytest.raises(ValueError):
        registry.transition(
            "emission-model",
            "1.0.0",
            ModelStatus.DEPLOYED,
        )


def test_full_lifecycle():
    registry = ModelRegistry([make_model()])

    registry.transition(
        "emission-model",
        "1.0.0",
        ModelStatus.TRAINING,
    )

    registry.transition(
        "emission-model",
        "1.0.0",
        ModelStatus.VALIDATED,
    )

    registry.approve(
        "emission-model",
        "1.0.0",
    )

    deployed = registry.deploy(
        "emission-model",
        "1.0.0",
    )

    assert deployed.status == ModelStatus.DEPLOYED
    assert registry.resolve_deployed(
        "emission-model"
    ).version == "1.0.0"


def test_only_approved_models_can_deploy():
    registry = ModelRegistry([make_model()])

    with pytest.raises(ValueError):
        registry.deploy(
            "emission-model",
            "1.0.0",
        )


def test_new_deployment_retires_previous_deployment():
    registry = ModelRegistry([
        make_model(
            version="1.0.0",
            status=ModelStatus.APPROVED,
        ),
        make_model(
            version="2.0.0",
            status=ModelStatus.APPROVED,
        ),
    ])

    registry.deploy("emission-model", "1.0.0")
    registry.deploy("emission-model", "2.0.0")

    assert registry.get(
        "emission-model",
        "1.0.0",
    ).status == ModelStatus.RETIRED

    assert registry.get(
        "emission-model",
        "2.0.0",
    ).status == ModelStatus.DEPLOYED


def test_retire_model():
    registry = ModelRegistry([
        make_model(
            status=ModelStatus.APPROVED,
        )
    ])

    result = registry.retire(
        "emission-model",
        "1.0.0",
    )

    assert result.status == ModelStatus.RETIRED


def test_dataset_compatibility():
    registry = ModelRegistry()
    model = make_model()
    dataset = make_dataset()

    registry.register(
        model,
        dataset=dataset,
    )

    assert registry.validate_compatibility(
        model,
        dataset,
    )


def test_dataset_mismatch_rejected():
    registry = ModelRegistry()
    model = make_model()
    dataset = make_dataset(dataset_id="different")

    with pytest.raises(ValueError):
        registry.register(
            model,
            dataset=dataset,
        )


def test_feature_version_mismatch_rejected():
    registry = ModelRegistry()
    model = make_model()
    dataset = make_dataset(feature_version="2.0.0")

    with pytest.raises(ValueError):
        registry.register(
            model,
            dataset=dataset,
        )


def test_list_by_status_is_deterministic():
    registry = ModelRegistry([
        make_model(
            model_id="z-model",
            version="1.0.0",
            status=ModelStatus.APPROVED,
        ),
        make_model(
            model_id="a-model",
            version="1.0.0",
            status=ModelStatus.APPROVED,
        ),
    ])

    models = registry.list_by_status(
        ModelStatus.APPROVED
    )

    assert tuple(model.model_id for model in models) == (
        "a-model",
        "z-model",
    )
