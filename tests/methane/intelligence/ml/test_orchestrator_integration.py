from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
    DatasetRecord,
)
from backend.app.services.intelligence.methane.intelligence.ml.models import (
    MLTaskType,
    ModelStatus,
    ModelType,
    ModelVersion,
    PredictionRequest,
    TrainingConfig,
)
from backend.app.services.intelligence.methane.intelligence.ml.orchestrator import (
    MLOrchestrator,
)


def test_ml_orchestrator_end_to_end_lifecycle():
    orchestrator = MLOrchestrator()

    records = tuple(
        DatasetRecord(
            record_id=f"record-{index}",
            entity_id=f"facility-{index}",
            features={
                "emission_rate": float(index * 10),
                "wind_speed": float(2 + index),
            },
            target=float(index * 5),
            source_ids=(f"source-{index}",),
        )
        for index in range(1, 11)
    )

    feature_names = (
        "emission_rate",
        "wind_speed",
    )

    dataset = orchestrator.prepare_dataset(
        dataset_id="methane-training",
        version="1.0.0",
        records=records,
        feature_names=feature_names,
        target_name="methane_target",
        source_ids=("sentinel-5p",),
        feature_version="1.0.0",
    )

    assert dataset.dataset_id == "methane-training"
    assert dataset.version == "1.0.0"
    assert dataset.record_count == 10

    dataset_split = orchestrator.split_dataset(
        records=records,
        validation_fraction=0.2,
        test_fraction=0.2,
        random_seed=42,
    )

    assert dataset_split.total_count == 10
    assert dataset_split.train_count == 6
    assert dataset_split.validation_count == 2
    assert dataset_split.test_count == 2

    config = TrainingConfig(
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.LINEAR,
        feature_names=feature_names,
        target_name="methane_target",
        validation_fraction=0.2,
        test_fraction=0.2,
        random_seed=42,
        hyperparameters={
            "learning_rate": 0.01,
        },
    )

    training = orchestrator.train(
        run_id="training-run-001",
        model_id="methane-model",
        config=config,
        dataset_split=dataset_split,
    )

    assert training.run_id == "training-run-001"
    assert training.model_id == "methane-model"
    assert training.train_count == 6
    assert training.validation_count == 2
    assert training.test_count == 2
    assert training.status == ModelStatus.TRAINING

    evaluation = orchestrator.evaluate(
        evaluation_id="evaluation-001",
        model_id="methane-model",
        model_version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        predictions=(10.0, 20.0),
        targets=(11.0, 19.0),
        dataset_split="validation",
        metric_thresholds={
            "r2": -1.0,
        },
    )

    assert evaluation.evaluation_id == "evaluation-001"
    assert evaluation.model_id == "methane-model"
    assert evaluation.model_version == "1.0.0"
    assert evaluation.passed is True
    assert evaluation.metric_count == 4

    model = ModelVersion(
        model_id="methane-model",
        version="1.0.0",
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.LINEAR,
        status=ModelStatus.TRAINING,
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        feature_version=dataset.feature_version,
        training_run_id=training.run_id,
        feature_names=feature_names,
    )

    registered = orchestrator.register(
        model,
        dataset=dataset,
    )

    assert registered.status == ModelStatus.TRAINING

    validated = orchestrator.registry.transition(
        "methane-model",
        "1.0.0",
        ModelStatus.VALIDATED,
    )

    assert validated.status == ModelStatus.VALIDATED

    approved = orchestrator.approve(
        "methane-model",
        "1.0.0",
    )

    assert approved.status == ModelStatus.APPROVED

    deployed = orchestrator.deploy(
        "methane-model",
        "1.0.0",
    )

    assert deployed.status == ModelStatus.DEPLOYED

    orchestrator.register_executor(
        "methane-model",
        "1.0.0",
        lambda features: (
            features["emission_rate"] * 0.5
            + features["wind_speed"]
        ),
    )

    request = PredictionRequest(
        request_id="prediction-001",
        entity_id="facility-001",
        model_id="methane-model",
        model_version="1.0.0",
        features={
            "emission_rate": 20.0,
            "wind_speed": 4.0,
        },
        signal_ids=("signal-001",),
        evidence_ids=("evidence-001",),
    )

    prediction = orchestrator.predict(
        request,
        confidence=0.95,
    )

    assert prediction.request_id == "prediction-001"
    assert prediction.entity_id == "facility-001"
    assert prediction.model_id == "methane-model"
    assert prediction.model_version == "1.0.0"
    assert prediction.value == 14.0
    assert prediction.confidence == 0.95
    assert prediction.feature_version == "1.0.0"
    assert prediction.dataset_version == "1.0.0"
    assert prediction.training_run_id == "training-run-001"
    assert prediction.signal_ids == ("signal-001",)
    assert prediction.evidence_ids == ("evidence-001",)
