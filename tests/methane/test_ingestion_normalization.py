import pytest

from backend.app.services.intelligence.methane.ingestion.normalization import (
    normalize_field_name,
    normalize_record,
    normalize_records,
)


def test_normalize_field_name():
    assert normalize_field_name("Methane Emissions") == "methane_emissions"


def test_normalize_field_name_handles_hyphens():
    assert normalize_field_name("facility-id") == "facility_id"


def test_normalize_field_name_handles_slashes():
    assert normalize_field_name("kg CH4/hour") == "kg_ch4_hour"


def test_normalize_field_name_strips_whitespace():
    assert normalize_field_name("  Facility ID  ") == "facility_id"


def test_normalize_field_name_rejects_non_string():
    with pytest.raises(TypeError):
        normalize_field_name(123)


def test_normalize_record():
    result = normalize_record(
        {
            "Facility ID": "FAC-001",
            "Methane Emissions": 12.5,
        }
    )

    assert result.standardized == {
        "facility_id": "FAC-001",
        "methane_emissions": 12.5,
    }


def test_normalize_record_preserves_original():
    original = {
        "Facility ID": "FAC-001",
    }

    result = normalize_record(original)

    assert result.original == original


def test_normalize_record_reports_changes():
    result = normalize_record(
        {
            "Facility ID": "FAC-001",
            "status": "raw",
        }
    )

    assert result.changed is True
    assert "Facility ID" in result.changed_fields
    assert "status" not in result.changed_fields


def test_explicit_field_mapping():
    result = normalize_record(
        {
            "CH4": 15.2,
            "Facility ID": "FAC-001",
        },
        {
            "CH4": "methane_kg",
            "Facility ID": "facility_id",
        },
    )

    assert result.standardized == {
        "methane_kg": 15.2,
        "facility_id": "FAC-001",
    }


def test_normalize_multiple_records():
    results = normalize_records(
        [
            {"Facility ID": "FAC-001"},
            {"Facility ID": "FAC-002"},
        ]
    )

    assert len(results) == 2
    assert results[0].standardized["facility_id"] == "FAC-001"
    assert results[1].standardized["facility_id"] == "FAC-002"
