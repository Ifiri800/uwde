from __future__ import annotations

import pytest

from backend.app.services.intelligence.methane.intelligence.ml.inference import (
    MLInferenceEngine,
    predict,
)
from backend.app.services.intelligence.methane.intelligence.ml.models import (
    MLTaskType,
    ModelStatus,
    ModelType,
    ModelVersion,
    PredictionRequest,
)
from backend.app.services.intelligence.methane.intelligence.ml.registry import (
    ModelRegistry,
)


def make_model(
    *,
    status: ModelStatus = ModelStatus.DEPLOYED,
    features: tuple[str, ...] = ("a", "b"),
) -> ModelVersion:
    return ModelVersion(
        model_id="model-1",
        version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.TREE,
        status=status,
        dataset_id="dataset-1",
        dataset_version="1.0.0",
        feature_version="2.0.0",
        training_run_id="run-1",
        feature_names=features,
    )


def make_request(
    *,
    features: dict[str, float] | None = None,
) -> PredictionRequest:
    return PredictionRequest(
        request_id="request-1",
        entity_id="entity-1",
        model_id="model-1",
        model_version="1.0.0",
        features=features or {"a": 2.0, "b": 3.0},
        signal_ids=("signal-1",),
        evidence_ids=("evidence-1",),
    )


def make_engine(
    *,
    status: ModelStatus = ModelStatus.DEPLOYED,
) -> MLInferenceEngine:
    registry = ModelRegistry([
        make_model(status=status),
    ])

    return MLInferenceEngine(
        registry,
        {
            ("model-1", "1.0.0"): (
                lambda features: features["a"] + features["b"]
            ),
        },
    )


def test_prediction():
    result = make_engine().predict(
        make_request()
    )

    assert result.value == 5.0


def test_prediction_contains_provenance():
    result = make_engine().predict(
        make_request()
    )

    assert result.feature_version == "2.0.0"
    assert result.dataset_version == "1.0.0"
    assert result.training_run_id == "run-1"


def test_prediction_contains_signal_and_evidence_ids():
    result = make_engine().predict(
        make_request()
    )

    assert result.signal_ids == ("signal-1",)
    assert result.evidence_ids == ("evidence-1",)


def test_prediction_contains_explanation():
    result = make_engine().predict(
        make_request()
    )

    assert "model-1:1.0.0" in result.explanation


def test_confidence_is_preserved():
    result = make_engine().predict(
        make_request(),
        confidence=0.75,
    )

    assert result.confidence == 0.75


def test_invalid_confidence_rejected():
    with pytest.raises(ValueError):
        make_engine().predict(
            make_request(),
            confidence=1.1,
        )


def test_non_request_rejected():
    with pytest.raises(TypeError):
        make_engine().predict("invalid")  # type: ignore[arg-type]


def test_non_deployed_model_rejected():
    engine = make_engine(
        status=ModelStatus.APPROVED
    )

    with pytest.raises(ValueError):
        engine.predict(make_request())


def test_missing_feature_rejected():
    engine = make_engine()

    with pytest.raises(ValueError, match="missing"):
        engine.predict(
            make_request(
                features={"a": 1.0}
            )
        )


def test_unexpected_feature_rejected():
    engine = make_engine()

    with pytest.raises(ValueError, match="unexpected"):
        engine.predict(
            make_request(
                features={
                    "a": 1.0,
                    "b": 2.0,
                    "c": 3.0,
                }
            )
        )


def test_missing_executor_rejected():
    registry = ModelRegistry([
        make_model()
    ])

    engine = MLInferenceEngine(registry)

    with pytest.raises(LookupError):
        engine.predict(make_request())


def test_executor_must_return_numeric_value():
    registry = ModelRegistry([
        make_model()
    ])

    engine = MLInferenceEngine(
        registry,
        {
            ("model-1", "1.0.0"): (
                lambda features: "invalid"
            ),
        },
    )

    with pytest.raises(TypeError):
        engine.predict(make_request())


def test_executor_result_must_be_finite():
    registry = ModelRegistry([
        make_model()
    ])

    engine = MLInferenceEngine(
        registry,
        {
            ("model-1", "1.0.0"): (
                lambda features: float("inf")
            ),
        },
    )

    with pytest.raises(ValueError):
        engine.predict(make_request())


def test_duplicate_executor_rejected():
    engine = make_engine()

    with pytest.raises(ValueError):
        engine.register_executor(
            "model-1",
            "1.0.0",
            lambda features: 1.0,
        )


def test_convenience_predict():
    registry = ModelRegistry([
        make_model()
    ])

    result = predict(
        registry,
        make_request(),
        lambda features: 42.0,
    )

    assert result.value == 42.0
