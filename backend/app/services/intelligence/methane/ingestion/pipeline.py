from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .metadata import create_metadata
from .models import (
    IngestionBatch,
    IngestionMetadata,
    IngestionRecord,
    IngestionSourceType,
    ObservationStatus,
)
from .normalization import normalize_record
from .registry import IngestionRegistry
from .validation import (
    ValidationResult,
    validate_ingestion_batch,
    validate_ingestion_record,
)
from .versioning import DataVersion, create_version


@dataclass(frozen=True)
class PipelineRecordResult:
    """
    Result of processing a single ingestion record.
    """

    record: IngestionRecord
    validation: ValidationResult

    @property
    def valid(self) -> bool:
        return self.validation.valid


@dataclass(frozen=True)
class IngestionPipelineResult:
    """
    Result produced by the ingestion pipeline.
    """

    batch: IngestionBatch
    records: tuple[PipelineRecordResult, ...]
    version: DataVersion | None = None
    validation: ValidationResult | None = None

    @property
    def record_count(self) -> int:
        return len(self.records)

    @property
    def valid_record_count(self) -> int:
        return sum(
            1
            for result in self.records
            if result.valid
        )

    @property
    def rejected_record_count(self) -> int:
        return sum(
            1
            for result in self.records
            if not result.valid
        )

    @property
    def valid(self) -> bool:
        if self.validation is None:
            return True

        return self.validation.valid


@dataclass
class IngestionPipeline:
    """
    Orchestrates the methane data ingestion workflow.

    Pipeline stages:

    1. Normalize source records
    2. Construct ingestion records
    3. Validate records
    4. Mark invalid records as rejected
    5. Build ingestion batch
    6. Validate batch
    7. Create immutable data version
    """

    registry: IngestionRegistry | None = None
    field_mapping: Mapping[str, str] = field(
        default_factory=dict
    )

    def process(
        self,
        records: tuple[Mapping[str, Any], ...],
        source_id: str,
        source_name: str,
        source_type: IngestionSourceType,
        dataset_id: str,
        batch_id: str,
        metadata: IngestionMetadata | None = None,
        created_at: datetime | None = None,
    ) -> IngestionPipelineResult:
        """
        Process raw source records through the ingestion workflow.
        """

        if not isinstance(records, tuple):
            raise TypeError(
                "records must be a tuple of mappings"
            )

        timestamp = created_at or datetime.now(
            timezone.utc
        )

        if timestamp.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        ingestion_metadata = metadata or create_metadata(
            source_id=source_id,
            source_name=source_name,
            source_type=source_type,
            acquired_at=timestamp,
        )

        processed_records: list[PipelineRecordResult] = []
        ingestion_records: list[IngestionRecord] = []

        for index, raw_record in enumerate(records):
            normalized = normalize_record(
                raw_record,
                field_mapping=self.field_mapping,
            )

            record = IngestionRecord(
                record_id=f"{batch_id}:{index}",
                data=normalized.standardized,
                metadata=ingestion_metadata,
                status=ObservationStatus.STANDARDIZED,
            )

            validation = validate_ingestion_record(
                record,
                registry=self.registry,
            )

            if not validation.valid:
                record = IngestionRecord(
                    record_id=record.record_id,
                    data=record.data,
                    metadata=record.metadata,
                    status=ObservationStatus.REJECTED,
                    temporal=record.temporal,
                    geospatial=record.geospatial,
                    schema_version=record.schema_version,
                    record_version=record.record_version,
                )

            ingestion_records.append(record)

            processed_records.append(
                PipelineRecordResult(
                    record=record,
                    validation=validation,
                )
            )

        batch = IngestionBatch(
            batch_id=batch_id,
            records=tuple(ingestion_records),
            created_at=timestamp,
            source_type=source_type,
        )

        batch_validation = validate_ingestion_batch(
            batch,
            registry=self.registry,
        )

        version = create_version(
            version_id=f"{dataset_id}:{batch_id}",
            dataset_id=dataset_id,
            value=tuple(
                record.data
                for record in ingestion_records
            ),
            metadata={
                "batch_id": batch_id,
                "source_id": source_id,
                "record_count": len(ingestion_records),
            },
            created_at=timestamp,
        )

        return IngestionPipelineResult(
            batch=batch,
            records=tuple(processed_records),
            version=version,
            validation=batch_validation,
        )
