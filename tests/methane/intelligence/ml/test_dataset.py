import pytest

from backend.app.services.intelligence.methane.intelligence.ml.dataset import (
    DatasetBuilder,
    DatasetRecord,
)


def record(
    record_id: str,
    value: float,
) -> DatasetRecord:
    return DatasetRecord(
        record_id=record_id,
        features={
            "emission_rate": value,
            "pressure": value / 100,
        },
        target=value,
    )


def test_dataset_record():
    item = record("r1", 100.0)

    assert item.record_id == "r1"
    assert item.features["emission_rate"] == 100.0


def test_dataset_record_requires_id():
    with pytest.raises(ValueError):
        DatasetRecord(
            record_id="",
            features={"x": 1.0},
        )


def test_dataset_record_rejects_non_numeric_feature():
    with pytest.raises(TypeError):
        DatasetRecord(
            record_id="r1",
            features={"x": "bad"},
        )


def test_validation_success():
    builder = DatasetBuilder(
        feature_names=(
            "emission_rate",
            "pressure",
        ),
        target_name="target",
    )

    result = builder.validate(
        [
            record("r1", 100.0),
            record("r2", 200.0),
        ]
    )

    assert result.valid is True
    assert result.record_count == 2


def test_validation_detects_missing_feature():
    builder = DatasetBuilder(
        feature_names=("emission_rate", "pressure")
    )

    result = builder.validate(
        [
            DatasetRecord(
                record_id="r1",
                features={
                    "emission_rate": 100.0,
                },
            )
        ]
    )

    assert result.valid is False
    assert "r1" in result.missing_feature_records


def test_validation_detects_duplicates():
    builder = DatasetBuilder(
        feature_names=("emission_rate",)
    )

    records = (
        DatasetRecord(
            record_id="r1",
            features={"emission_rate": 1.0},
        ),
        DatasetRecord(
            record_id="r1",
            features={"emission_rate": 2.0},
        ),
    )

    result = builder.validate(records)

    assert result.valid is False
    assert "r1" in result.duplicate_record_ids


def test_validation_detects_feature_target_leakage():
    builder = DatasetBuilder(
        feature_names=("target", "pressure"),
        target_name="target",
    )

    result = builder.validate(
        [
            DatasetRecord(
                record_id="r1",
                features={
                    "target": 10.0,
                    "pressure": 0.5,
                },
            )
        ]
    )

    assert result.valid is False
    assert "target" in result.leakage_features


def test_build_creates_dataset_version():
    builder = DatasetBuilder(
        feature_names=("emission_rate",)
    )

    dataset = builder.build(
        "methane",
        "1.0.0",
        [
            DatasetRecord(
                record_id="r1",
                features={"emission_rate": 10.0},
            )
        ],
        feature_version="features-1",
    )

    assert dataset.dataset_id == "methane"
    assert dataset.version == "1.0.0"
    assert dataset.record_count == 1


def test_build_rejects_invalid_dataset():
    builder = DatasetBuilder(
        feature_names=("emission_rate", "pressure")
    )

    with pytest.raises(ValueError):
        builder.build(
            "methane",
            "1",
            [
                DatasetRecord(
                    record_id="r1",
                    features={"emission_rate": 10.0},
                )
            ],
        )


def test_split_preserves_total_records():
    builder = DatasetBuilder(
        feature_names=("emission_rate",)
    )

    records = tuple(
        DatasetRecord(
            record_id=f"r{i}",
            features={"emission_rate": float(i)},
        )
        for i in range(100)
    )

    split = builder.split(
        records,
        random_seed=42,
    )

    assert split.total_count == 100
    assert split.train_count == 60
    assert split.validation_count == 20
    assert split.test_count == 20


def test_split_is_reproducible():
    builder = DatasetBuilder(
        feature_names=("emission_rate",)
    )

    records = tuple(
        DatasetRecord(
            record_id=f"r{i}",
            features={"emission_rate": float(i)},
        )
        for i in range(20)
    )

    first = builder.split(
        records,
        random_seed=42,
    )

    second = builder.split(
        records,
        random_seed=42,
    )

    assert first == second
