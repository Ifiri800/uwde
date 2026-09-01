from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .models import DatasetStatus, DatasetVersion


@dataclass(frozen=True)
class DatasetRecord:
    """One immutable ML training record."""

    record_id: str
    features: Mapping[str, float]
    target: float | int | str | None = None
    entity_id: str | None = None
    timestamp: Any | None = None
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id is required")

        for name, value in self.features.items():
            if not name.strip():
                raise ValueError(
                    "feature names cannot be empty"
                )

            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"feature '{name}' must be numeric"
                )

            if not float("-inf") < float(value) < float("inf"):
                raise ValueError(
                    f"feature '{name}' must be finite"
                )


@dataclass(frozen=True)
class DatasetSplit:
    """Deterministic train/validation/test dataset split."""

    train: tuple[DatasetRecord, ...]
    validation: tuple[DatasetRecord, ...]
    test: tuple[DatasetRecord, ...]

    @property
    def train_count(self) -> int:
        return len(self.train)

    @property
    def validation_count(self) -> int:
        return len(self.validation)

    @property
    def test_count(self) -> int:
        return len(self.test)

    @property
    def total_count(self) -> int:
        return (
            self.train_count
            + self.validation_count
            + self.test_count
        )


@dataclass(frozen=True)
class DatasetValidation:
    """Validation result for an ML dataset."""

    valid: bool
    record_count: int

    feature_names: tuple[str, ...]

    missing_feature_records: tuple[str, ...] = ()
    duplicate_record_ids: tuple[str, ...] = ()
    invalid_record_ids: tuple[str, ...] = ()
    leakage_features: tuple[str, ...] = ()

    warnings: tuple[str, ...] = ()

    @property
    def has_errors(self) -> bool:
        return not self.valid


class DatasetBuilder:
    """Build and validate deterministic ML datasets."""

    def __init__(
        self,
        *,
        feature_names: Sequence[str],
        target_name: str | None = None,
    ) -> None:
        self.feature_names = tuple(feature_names)
        self.target_name = target_name

        if not self.feature_names:
            raise ValueError(
                "at least one feature is required"
            )

        if any(
            not name.strip()
            for name in self.feature_names
        ):
            raise ValueError(
                "feature names cannot be empty"
            )

    def validate(
        self,
        records: Sequence[DatasetRecord],
    ) -> DatasetValidation:
        values = tuple(records)

        seen: set[str] = set()
        duplicates: list[str] = []
        missing: list[str] = []
        invalid: list[str] = []

        for record in values:
            if record.record_id in seen:
                duplicates.append(record.record_id)

            seen.add(record.record_id)

            if any(
                feature not in record.features
                for feature in self.feature_names
            ):
                missing.append(record.record_id)

            try:
                for name in self.feature_names:
                    value = record.features[name]

                    if not float("-inf") < float(value) < float("inf"):
                        invalid.append(record.record_id)

            except (KeyError, TypeError, ValueError):
                invalid.append(record.record_id)

        leakage = self._detect_leakage()

        valid = not (
            duplicates
            or missing
            or invalid
            or leakage
        )

        warnings: list[str] = []

        if not values:
            warnings.append(
                "dataset contains no records"
            )

        if self.target_name in self.feature_names:
            warnings.append(
                "target name is also present as a feature"
            )

        return DatasetValidation(
            valid=valid,
            record_count=len(values),
            feature_names=self.feature_names,
            missing_feature_records=tuple(
                sorted(set(missing))
            ),
            duplicate_record_ids=tuple(
                sorted(set(duplicates))
            ),
            invalid_record_ids=tuple(
                sorted(set(invalid))
            ),
            leakage_features=leakage,
            warnings=tuple(warnings),
        )

    def build(
        self,
        dataset_id: str,
        version: str,
        records: Sequence[DatasetRecord],
        *,
        source_ids: tuple[str, ...] = (),
        feature_version: str = "1.0.0",
    ) -> DatasetVersion:
        validation = self.validate(records)

        if not validation.valid:
            raise ValueError(
                "dataset validation failed"
            )

        return DatasetVersion(
            dataset_id=dataset_id,
            version=version,
            status=DatasetStatus.VALIDATED,
            feature_version=feature_version,
            record_count=len(records),
            source_ids=source_ids,
        )

    def split(
        self,
        records: Sequence[DatasetRecord],
        *,
        validation_fraction: float = 0.2,
        test_fraction: float = 0.2,
        random_seed: int | None = None,
    ) -> DatasetSplit:
        if not 0.0 < validation_fraction < 1.0:
            raise ValueError(
                "validation_fraction must be between 0 and 1"
            )

        if not 0.0 < test_fraction < 1.0:
            raise ValueError(
                "test_fraction must be between 0 and 1"
            )

        if validation_fraction + test_fraction >= 1.0:
            raise ValueError(
                "validation_fraction + test_fraction "
                "must be less than 1"
            )

        values = list(records)

        if random_seed is not None:
            import random

            random.Random(random_seed).shuffle(values)

        total = len(values)

        test_count = int(total * test_fraction)
        validation_count = int(
            total * validation_fraction
        )

        test_start = total - test_count
        validation_start = (
            test_start - validation_count
        )

        return DatasetSplit(
            train=tuple(values[:validation_start]),
            validation=tuple(
                values[validation_start:test_start]
            ),
            test=tuple(values[test_start:]),
        )

    def _detect_leakage(self) -> tuple[str, ...]:
        leakage: list[str] = []

        if self.target_name is not None:
            for feature in self.feature_names:
                if feature == self.target_name:
                    leakage.append(feature)

        return tuple(sorted(leakage))
