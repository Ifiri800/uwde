from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.connectors import (
    create_connector,
)
from backend.app.services.intelligence.methane.ingestion.models import (
    GeospatialReference,
    IngestionBatch,
    IngestionMetadata,
    IngestionRecord,
    IngestionSourceType,
    ObservationStatus,
    TemporalReference,
    UnitValue,
)
from backend.app.services.intelligence.methane.ingestion.registry import (
    IngestionRegistry,
    RegisteredSource,
)
from backend.app.services.intelligence.methane.ingestion.validation import (
    IngestionValidationError,
    require_valid,
    validate_batch,
    validate_geospatial,
    validate_ingestion_batch,
    validate_ingestion_record,
    validate_metadata,
    validate_record,
    validate_temporal,
    validate_unit_value,
)


NOW = datetime.now(timezone.utc)


def make_metadata(
    source_id: str = "source-1",
    source_type: IngestionSourceType = IngestionSourceType.API,
) -> IngestionMetadata:
    return IngestionMetadata(
        source_id=source_id,
        source_type=source_type,
        source_name="Test Source",
        acquired_at=NOW,
    )


def make_record(
    record_id: str = "record-1",
    source_type: IngestionSourceType = IngestionSourceType.API,
) -> IngestionRecord:
    return IngestionRecord(
        record_id=record_id,
        data={"methane_kg": 10.0},
        metadata=make_metadata(
            source_type=source_type,
        ),
        status=ObservationStatus.RAW,
        temporal=TemporalReference(
            observed_at=NOW,
        ),
        geospatial=GeospatialReference(
            latitude=9.0,
            longitude=7.0,
        ),
    )


def make_registry() -> IngestionRegistry:
    metadata = make_metadata()

    connector = create_connector(
        source_id="source-1",
        source_type=IngestionSourceType.API,
    )

    return IngestionRegistry(
        [
            RegisteredSource(
                metadata=metadata,
                connector=connector,
            )
        ]
    )


def test_valid_metadata():
    assert validate_metadata(make_metadata()).valid


def test_invalid_metadata_type():
    result = validate_metadata("invalid")
    assert not result.valid


def test_valid_temporal():
    result = validate_temporal(
        TemporalReference(observed_at=NOW)
    )
    assert result.valid


def test_none_temporal_is_valid():
    assert validate_temporal(None).valid


def test_valid_geospatial():
    result = validate_geospatial(
        GeospatialReference(
            latitude=10.0,
            longitude=8.0,
        )
    )
    assert result.valid


def test_none_geospatial_is_valid():
    assert validate_geospatial(None).valid


def test_valid_unit_value():
    result = validate_unit_value(
        UnitValue(
            value=10.0,
            unit="kg",
        )
    )
    assert result.valid


def test_invalid_unit_value_type():
    result = validate_unit_value("invalid")
    assert not result.valid


def test_valid_record():
    result = validate_record(make_record())
    assert result.valid
    assert result.issue_count == 0


def test_record_requires_registered_source():
    result = validate_record(
        make_record(),
        registry=IngestionRegistry(),
    )

    assert not result.valid
    assert any(
        issue.field == "metadata.source_id"
        for issue in result.issues
    )


def test_record_with_registered_source():
    result = validate_record(
        make_record(),
        registry=make_registry(),
    )

    assert result.valid


def test_valid_batch():
    batch = IngestionBatch(
        batch_id="batch-1",
        records=(
            make_record("record-1"),
            make_record("record-2"),
        ),
        created_at=NOW,
        source_type=IngestionSourceType.API,
    )

    result = validate_batch(batch)

    assert result.valid


def test_duplicate_record_ids_rejected():
    batch = IngestionBatch(
        batch_id="batch-1",
        records=(
            make_record("same"),
            make_record("same"),
        ),
        created_at=NOW,
        source_type=IngestionSourceType.API,
    )

    result = validate_batch(batch)

    assert not result.valid
    assert any(
        "duplicate" in issue.message
        for issue in result.issues
    )


def test_batch_source_type_mismatch():
    batch = IngestionBatch(
        batch_id="batch-1",
        records=(
            make_record(
                "record-1",
                IngestionSourceType.SENSOR,
            ),
        ),
        created_at=NOW,
        source_type=IngestionSourceType.API,
    )

    result = validate_batch(batch)

    assert not result.valid


def test_boolean_record_validation():
    assert validate_ingestion_record(
        make_record()
    )


def test_boolean_batch_validation():
    batch = IngestionBatch(
        batch_id="batch-1",
        records=(make_record(),),
        created_at=NOW,
        source_type=IngestionSourceType.API,
    )

    assert validate_ingestion_batch(batch)


def test_require_valid_accepts_valid_result():
    require_valid(
        validate_record(make_record())
    )


def test_require_valid_raises():
    result = validate_record(
        make_record(),
        registry=IngestionRegistry(),
    )

    with pytest.raises(IngestionValidationError):
        require_valid(result)
