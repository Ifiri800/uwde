from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.models import (
    GeospatialReference,
    IngestionMetadata,
    IngestionRecord,
    IngestionSourceType,
    ObservationStatus,
    TemporalReference,
    UnitValue,
)


def metadata():
    return IngestionMetadata(
        source_id="src-001",
        source_type=IngestionSourceType.FILE,
        source_name="test.csv",
        acquired_at=datetime.now(timezone.utc),
    )


def test_ingestion_metadata():
    value = metadata()

    assert value.source_id == "src-001"
    assert value.source_type == IngestionSourceType.FILE


def test_ingestion_record_defaults():
    record = IngestionRecord(
        record_id="rec-001",
        data={"methane_rate": 10.5},
        metadata=metadata(),
    )

    assert record.status == ObservationStatus.RAW
    assert record.record_version == 1
    assert record.schema_version == "1.0"


def test_geospatial_reference():
    value = GeospatialReference(
        latitude=5.5,
        longitude=6.5,
        crs="EPSG:4326",
    )

    assert value.latitude == 5.5
    assert value.longitude == 6.5


def test_invalid_latitude():
    with pytest.raises(ValueError):
        GeospatialReference(latitude=91)


def test_invalid_longitude():
    with pytest.raises(ValueError):
        GeospatialReference(longitude=181)


def test_temporal_reference():
    observed = datetime.now(timezone.utc)

    value = TemporalReference(
        observed_at=observed,
        timezone="UTC",
        duration_seconds=60,
    )

    assert value.observed_at == observed
    assert value.duration_seconds == 60


def test_negative_duration_rejected():
    with pytest.raises(ValueError):
        TemporalReference(
            observed_at=datetime.now(timezone.utc),
            duration_seconds=-1,
        )


def test_unit_value():
    value = UnitValue(
        value=25.0,
        unit="kg/h",
    )

    assert value.value == 25.0
    assert value.unit == "kg/h"


def test_empty_source_id_rejected():
    with pytest.raises(ValueError):
        IngestionMetadata(
            source_id="",
            source_type=IngestionSourceType.FILE,
            source_name="test.csv",
            acquired_at=datetime.now(timezone.utc),
        )
