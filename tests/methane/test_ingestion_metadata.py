from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.metadata import (
    enrich_metadata,
    metadata_age_seconds,
    validate_metadata,
    with_quality_note,
)
from backend.app.services.intelligence.methane.ingestion.models import (
    IngestionMetadata,
    IngestionSourceType,
)


def make_metadata():
    return IngestionMetadata(
        source_id="SRC-001",
        source_type=IngestionSourceType.API,
        source_name="Test API",
        acquired_at=datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
    )


def test_validate_metadata_accepts_valid_metadata():
    validate_metadata(make_metadata())


def test_validate_metadata_rejects_invalid_type():
    with pytest.raises(TypeError):
        validate_metadata("invalid")


def test_enrich_metadata_adds_attribute():
    result = enrich_metadata(make_metadata(), facility_id="FAC-001")

    assert result.attributes["facility_id"] == "FAC-001"


def test_enrich_metadata_preserves_existing_attributes():
    metadata = enrich_metadata(make_metadata(), operator="Operator A")

    result = enrich_metadata(metadata, facility_id="FAC-001")

    assert result.attributes["operator"] == "Operator A"
    assert result.attributes["facility_id"] == "FAC-001"


def test_enrich_metadata_overwrites_existing_attribute():
    metadata = enrich_metadata(make_metadata(), status="raw")

    result = enrich_metadata(metadata, status="validated")

    assert result.attributes["status"] == "validated"


def test_with_quality_note():
    result = with_quality_note(make_metadata(), "Calibration verified")

    assert result.quality_notes == "Calibration verified"


def test_with_quality_note_rejects_empty_note():
    with pytest.raises(ValueError):
        with_quality_note(make_metadata(), "   ")


def test_metadata_age_seconds():
    metadata = make_metadata()

    now = datetime(2026, 8, 31, 10, 5, tzinfo=timezone.utc)

    assert metadata_age_seconds(metadata, now=now) == 300


def test_metadata_age_rejects_invalid_now():
    with pytest.raises(TypeError):
        metadata_age_seconds(make_metadata(), now="invalid")
