from datetime import date
from decimal import Decimal

from backend.app.services.preprocessing.pipeline import (
    preprocess_record,
    preprocess_records,
)
from backend.app.services.preprocessing.validators import FieldRule


def test_preprocess_record_cleans_normalizes_and_validates():
    record = {
        "title": "  Environmental   Consultant ",
        "salary": "125000",
        "active": "yes",
        "published": "2026-08-24",
        "source_url": "HTTPS://Example.COM/jobs/1",
    }

    normalization_schema = {
        "title": "text",
        "salary": "number",
        "active": "boolean",
        "published": "date",
        "source_url": "url",
    }

    validation_schema = {
        "title": FieldRule(
            field_type="text",
            required=True,
            min_length=3,
        ),
        "salary": FieldRule(
            field_type="number",
            required=True,
            minimum=0,
        ),
        "active": FieldRule(
            field_type="boolean",
        ),
        "published": FieldRule(
            field_type="date",
        ),
        "source_url": FieldRule(
            field_type="url",
        ),
    }

    result = preprocess_record(
        record,
        schema=normalization_schema,
        validation_schema=validation_schema,
    )

    assert result.valid is True
    assert result.errors == []

    assert result.record["title"] == "Environmental Consultant"
    assert result.record["salary"] == 125000
    assert result.record["active"] is True
    assert result.record["published"] == date(2026, 8, 24)
    assert result.record["source_url"] == (
        "https://example.com/jobs/1"
    )


def test_preprocess_record_reports_validation_errors():
    record = {
        "title": "AB",
        "salary": "-100",
        "active": "yes",
    }

    normalization_schema = {
        "title": "text",
        "salary": "number",
        "active": "boolean",
    }

    validation_schema = {
        "title": FieldRule(
            field_type="text",
            required=True,
            min_length=3,
        ),
        "salary": FieldRule(
            field_type="number",
            minimum=0,
        ),
        "active": FieldRule(
            field_type="boolean",
        ),
    }

    result = preprocess_record(
        record,
        schema=normalization_schema,
        validation_schema=validation_schema,
    )

    assert result.valid is False
    assert result.error_count == 2
    assert any("title" in error for error in result.errors)
    assert any("salary" in error for error in result.errors)


def test_preprocess_record_can_remove_empty_values():
    record = {
        "title": "  UWDE  ",
        "description": "   ",
        "location": " Lagos ",
    }

    result = preprocess_record(
        record,
        schema={
            "title": "text",
            "description": "text",
            "location": "text",
        },
        remove_empty=True,
    )

    assert result.record == {
        "title": "UWDE",
        "location": "Lagos",
    }


def test_preprocess_records_processes_each_record_independently():
    records = [
        {
            "title": "  Record One ",
            "score": "90",
        },
        {
            "title": " Record Two ",
            "score": "75",
        },
    ]

    results = preprocess_records(
        records,
        schema={
            "title": "text",
            "score": "number",
        },
        validation_schema={
            "title": FieldRule(
                field_type="text",
                required=True,
            ),
            "score": FieldRule(
                field_type="number",
                minimum=0,
                maximum=100,
            ),
        },
    )

    assert len(results) == 2

    assert results[0].valid is True
    assert results[0].record["title"] == "Record One"
    assert results[0].record["score"] == 90

    assert results[1].valid is True
    assert results[1].record["title"] == "Record Two"
    assert results[1].record["score"] == 75


def test_preprocess_records_preserves_individual_failures():
    records = [
        {
            "title": "Valid Record",
            "score": "80",
        },
        {
            "title": "Invalid Record",
            "score": "150",
        },
    ]

    results = preprocess_records(
        records,
        schema={
            "title": "text",
            "score": "number",
        },
        validation_schema={
            "title": FieldRule(
                field_type="text",
                required=True,
            ),
            "score": FieldRule(
                field_type="number",
                minimum=0,
                maximum=100,
            ),
        },
    )

    assert len(results) == 2

    assert results[0].valid is True
    assert results[1].valid is False

    assert results[0].record["score"] == 80
    assert results[1].record["score"] == 150


def test_preprocess_record_preserves_decimal_numbers():
    record = {
        "value": "42.50",
    }

    result = preprocess_record(
        record,
        schema={
            "value": "number",
        },
        validation_schema={
            "value": FieldRule(
                field_type="number",
            ),
        },
    )

    assert result.valid is True
    assert result.record["value"] == Decimal("42.50")