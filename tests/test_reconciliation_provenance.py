from datetime import datetime, timezone

import pytest

from backend.app.services.reconciliation.provenance import (
    Provenance,
    SourcedValue,
    attach_provenance,
    create_provenance,
)


def test_provenance_requires_source_url():
    with pytest.raises(ValueError):
        Provenance(source_url="")


def test_provenance_accepts_source_url():
    provenance = Provenance(
        source_url="https://example.com/data",
    )

    assert provenance.source_url == "https://example.com/data"


def test_provenance_default_timestamp_is_utc():
    provenance = Provenance(
        source_url="https://example.com/data",
    )

    assert provenance.extracted_at.tzinfo is not None
    assert provenance.extracted_at.utcoffset() == timezone.utc.utcoffset(
        provenance.extracted_at
    )


def test_provenance_stores_metadata():
    provenance = Provenance(
        source_url="https://example.com/data",
        source_id="source-001",
        field_name="title",
        extraction_method="css_selector",
        confidence=0.95,
        metadata={
            "selector": "h1.title",
            "page": 1,
        },
    )

    assert provenance.source_id == "source-001"
    assert provenance.field_name == "title"
    assert provenance.extraction_method == "css_selector"
    assert provenance.confidence == 0.95
    assert provenance.metadata["selector"] == "h1.title"
    assert provenance.metadata["page"] == 1


def test_provenance_accepts_zero_confidence():
    provenance = Provenance(
        source_url="https://example.com",
        confidence=0.0,
    )

    assert provenance.confidence == 0.0


def test_provenance_accepts_full_confidence():
    provenance = Provenance(
        source_url="https://example.com",
        confidence=1.0,
    )

    assert provenance.confidence == 1.0


def test_provenance_rejects_confidence_above_one():
    with pytest.raises(ValueError):
        Provenance(
            source_url="https://example.com",
            confidence=1.1,
        )


def test_provenance_rejects_confidence_below_zero():
    with pytest.raises(ValueError):
        Provenance(
            source_url="https://example.com",
            confidence=-0.1,
        )


def test_create_provenance():
    provenance = create_provenance(
        "https://example.com/jobs",
        source_id="jobs-page",
        field_name="title",
        extraction_method="css_selector",
        confidence=0.9,
        metadata={"selector": ".job-title"},
    )

    assert provenance.source_url == "https://example.com/jobs"
    assert provenance.source_id == "jobs-page"
    assert provenance.field_name == "title"
    assert provenance.extraction_method == "css_selector"
    assert provenance.confidence == 0.9
    assert provenance.metadata == {
        "selector": ".job-title",
    }


def test_create_provenance_uses_utc_timestamp():
    before = datetime.now(timezone.utc)

    provenance = create_provenance(
        "https://example.com",
    )

    after = datetime.now(timezone.utc)

    assert before <= provenance.extracted_at <= after


def test_attach_provenance():
    provenance = create_provenance(
        "https://example.com",
        field_name="title",
        confidence=0.85,
    )

    sourced = attach_provenance(
        "Environmental Consultant",
        provenance,
    )

    assert isinstance(sourced, SourcedValue)
    assert sourced.value == "Environmental Consultant"
    assert sourced.provenance is provenance


def test_sourced_value_exposes_confidence():
    provenance = create_provenance(
        "https://example.com",
        confidence=0.75,
    )

    sourced = SourcedValue(
        value="UWDE",
        provenance=provenance,
    )

    assert sourced.confidence == 0.75


def test_sourced_value_can_contain_complex_value():
    provenance = create_provenance(
        "https://example.com/data",
        field_name="coordinates",
    )

    value = {
        "latitude": 9.0765,
        "longitude": 7.3986,
    }

    sourced = attach_provenance(
        value,
        provenance,
    )

    assert sourced.value == value
    assert sourced.provenance.field_name == "coordinates"