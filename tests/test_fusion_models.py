from datetime import datetime, timezone

import pytest

from backend.app.services.fusion.models import (
    FusionField,
    FusionObservation,
    FusionRecord,
    FusionResult,
    FusionSource,
)


def test_fusion_source_requires_source_id():
    with pytest.raises(ValueError):
        FusionSource(source_id="")


def test_fusion_source_can_store_metadata():
    source = FusionSource(
        source_id="source-1",
        source_url="https://example.com",
        source_name="Example",
        metadata={"type": "web"},
    )

    assert source.source_id == "source-1"
    assert source.source_url == "https://example.com"
    assert source.metadata["type"] == "web"


def test_fusion_observation_requires_field_name():
    source = FusionSource(source_id="source-1")

    with pytest.raises(ValueError):
        FusionObservation(
            field_name="",
            value="test",
            source=source,
        )


def test_fusion_observation_validates_confidence():
    source = FusionSource(source_id="source-1")

    with pytest.raises(ValueError):
        FusionObservation(
            field_name="name",
            value="Test",
            source=source,
            confidence=1.1,
        )


def test_fusion_observation_accepts_valid_confidence():
    source = FusionSource(source_id="source-1")

    observation = FusionObservation(
        field_name="name",
        value="Test",
        source=source,
        confidence=0.85,
    )

    assert observation.confidence == 0.85


def test_fusion_field_validates_confidence():
    with pytest.raises(ValueError):
        FusionField(
            field_name="name",
            confidence=-0.1,
        )


def test_fusion_record_requires_record_id():
    with pytest.raises(ValueError):
        FusionRecord(record_id="")


def test_fusion_record_validates_confidence():
    with pytest.raises(ValueError):
        FusionRecord(
            record_id="record-1",
            confidence=1.5,
        )


def test_fusion_record_stores_fields_and_sources():
    source = FusionSource(source_id="source-1")

    observation = FusionObservation(
        field_name="name",
        value="Environmental Consultant",
        source=source,
        confidence=0.9,
    )

    field = FusionField(
        field_name="name",
        value="Environmental Consultant",
        observations=[observation],
        confidence=0.9,
    )

    record = FusionRecord(
        record_id="record-1",
        fields={"name": field},
        sources=[source],
        confidence=0.9,
    )

    assert record.fields["name"].value == "Environmental Consultant"
    assert record.sources[0].source_id == "source-1"
    assert record.confidence == 0.9


def test_fusion_result_defaults_are_safe():
    result = FusionResult()

    assert result.records == []
    assert result.observations_processed == 0
    assert result.sources_processed == 0
    assert result.conflicts_detected == 0
    assert result.duplicates_detected == 0
    assert result.requires_review is False


def test_fusion_result_rejects_negative_counters():
    with pytest.raises(ValueError):
        FusionResult(observations_processed=-1)

    with pytest.raises(ValueError):
        FusionResult(sources_processed=-1)

    with pytest.raises(ValueError):
        FusionResult(conflicts_detected=-1)

    with pytest.raises(ValueError):
        FusionResult(duplicates_detected=-1)


def test_fusion_timestamps_are_timezone_aware():
    source = FusionSource(source_id="source-1")

    observation = FusionObservation(
        field_name="name",
        value="Test",
        source=source,
    )

    record = FusionRecord(record_id="record-1")

    assert observation.extracted_at.tzinfo == timezone.utc
    assert record.created_at.tzinfo == timezone.utc


def test_fusion_observation_supports_metadata():
    source = FusionSource(source_id="source-1")

    observation = FusionObservation(
        field_name="name",
        value="Test",
        source=source,
        metadata={"method": "css_selector"},
    )

    assert observation.metadata["method"] == "css_selector"
