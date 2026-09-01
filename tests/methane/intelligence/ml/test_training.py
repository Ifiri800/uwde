from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
    DatasetBuilder,
    DatasetRecord,
)
from backend.app.services.intelligence.methane.intelligence.ml.models import (
    MLTaskType,
    ModelStatus,
    ModelType,
    TrainingConfig,
)
from backend.app.services.intelligence.methane.intelligence.ml.training import (
    TrainingEngine,
    TrainingResult,
    train_model,
)


def make_config():
    return TrainingConfig(
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.LINEAR,
        feature_names=("emission", "temperature"),
        target_name="target",
        random_seed=42,
    )


def make_split():
    records = tuple(
        DatasetRecord(
            record_id=f"r{i}",
            features={
                "emission": float(i),
                "temperature": float(i + 10),
            },
            target=float(i * 2),
        )
        for i in range(10)
    )

    return DatasetBuilder(
        feature_names=("emission", "temperature"),
        target_name="target",
    ).split(
        records,
        validation_fraction=0.2,
        test_fraction=0.2,
        random_seed=42,
    )


def test_training_returns_result():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
    )

    assert isinstance(result, TrainingResult)


def test_training_status_is_training():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
    )

    assert result.status == ModelStatus.TRAINING


def test_training_counts_are_preserved():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
    )

    assert result.total_count == 10
    assert result.train_count == 6
    assert result.validation_count == 2
    assert result.test_count == 2


def test_training_preserves_model_configuration():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
    )

    assert result.task_type == "regression"
    assert result.model_type == "linear"
    assert result.feature_names == (
        "emission",
        "temperature",
    )
    assert result.target_name == "target"


def test_training_is_reproducible():
    config = make_config()
    split = make_split()

    first = train_model(
        run_id="run-1",
        model_id="model-1",
        config=config,
        dataset_split=split,
    )

    second = train_model(
        run_id="run-1",
        model_id="model-1",
        config=config,
        dataset_split=split,
    )

    assert first == second


def test_training_rejects_empty_run_id():
    import pytest

    with pytest.raises(ValueError):
        TrainingEngine().train(
            run_id="",
            model_id="model-1",
            config=make_config(),
            dataset_split=make_split(),
        )


def test_training_rejects_empty_model_id():
    import pytest

    with pytest.raises(ValueError):
        TrainingEngine().train(
            run_id="run-1",
            model_id="",
            config=make_config(),
            dataset_split=make_split(),
        )


def test_training_rejects_empty_training_split():
    import pytest

    from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
        DatasetSplit,
    )

    split = DatasetSplit(
        train=(),
        validation=(),
        test=(),
    )

    with pytest.raises(ValueError):
        TrainingEngine().train(
            run_id="run-1",
            model_id="model-1",
            config=make_config(),
            dataset_split=split,
        )


def test_training_rejects_missing_feature():
    import pytest

    from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
        DatasetSplit,
    )

    record = DatasetRecord(
        record_id="bad",
        features={"emission": 10.0},
        target=20.0,
    )

    split = DatasetSplit(
        train=(record,),
        validation=(),
        test=(),
    )

    with pytest.raises(ValueError):
        TrainingEngine().train(
            run_id="run-1",
            model_id="model-1",
            config=make_config(),
            dataset_split=split,
        )


def test_training_rejects_target_as_feature():
    import pytest

    config = TrainingConfig(
        task_type=MLTaskType.REGRESSION,
        model_type=ModelType.LINEAR,
        feature_names=("target",),
        target_name="target",
    )

    with pytest.raises(ValueError):
        TrainingEngine().train(
            run_id="run-1",
            model_id="model-1",
            config=config,
            dataset_split=make_split(),
        )


def test_training_records_target_metrics():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
    )

    assert "target_mean" in result.metrics
    assert "target_count" in result.metrics


def test_empty_validation_and_test_generate_warnings():
    from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
        DatasetSplit,
    )

    record = DatasetRecord(
        record_id="r1",
        features={
            "emission": 1.0,
            "temperature": 20.0,
        },
        target=2.0,
    )

    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=DatasetSplit(
            train=(record,),
            validation=(),
            test=(),
        ),
    )

    assert result.has_warnings
    assert len(result.warnings) == 2


def test_feature_names_can_be_explicitly_supplied():
    result = TrainingEngine().train(
        run_id="run-1",
        model_id="model-1",
        config=make_config(),
        dataset_split=make_split(),
        feature_names=(
            "emission",
            "temperature",
        ),
    )

    assert result.feature_names == (
        "emission",
        "temperature",
    )
