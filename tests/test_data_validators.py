from datetime import date, datetime

from backend.app.services.preprocessing.validators import (
    FieldRule,
    validate_record,
    validate_value,
)


def test_valid_text_value():
    rule = FieldRule(
        field_type="text",
        required=True,
    )

    assert validate_value(
        "title",
        "Environmental Consultant",
        rule,
    ) == []


def test_invalid_text_type():
    rule = FieldRule(field_type="text")

    errors = validate_value(
        "title",
        123,
        rule,
    )

    assert len(errors) == 1
    assert "expected type text" in errors[0]


def test_text_minimum_length():
    rule = FieldRule(
        field_type="text",
        min_length=5,
    )

    errors = validate_value(
        "name",
        "ABC",
        rule,
    )

    assert len(errors) == 1


def test_text_maximum_length():
    rule = FieldRule(
        field_type="text",
        max_length=5,
    )

    errors = validate_value(
        "name",
        "ABCDEFG",
        rule,
    )

    assert len(errors) == 1


def test_valid_number():
    rule = FieldRule(
        field_type="number",
        minimum=0,
        maximum=100,
    )

    assert validate_value(
        "score",
        75,
        rule,
    ) == []


def test_number_below_minimum():
    rule = FieldRule(
        field_type="number",
        minimum=0,
    )

    errors = validate_value(
        "score",
        -1,
        rule,
    )

    assert len(errors) == 1


def test_number_above_maximum():
    rule = FieldRule(
        field_type="number",
        maximum=100,
    )

    errors = validate_value(
        "score",
        101,
        rule,
    )

    assert len(errors) == 1


def test_boolean_validation():
    rule = FieldRule(field_type="boolean")

    assert validate_value(
        "active",
        True,
        rule,
    ) == []


def test_date_validation():
    rule = FieldRule(field_type="date")

    assert validate_value(
        "published",
        date(2026, 8, 24),
        rule,
    ) == []


def test_datetime_validation():
    rule = FieldRule(field_type="datetime")

    assert validate_value(
        "created_at",
        datetime(2026, 8, 24, 10, 30),
        rule,
    ) == []


def test_url_validation():
    rule = FieldRule(field_type="url")

    assert validate_value(
        "source_url",
        "https://example.com/page",
        rule,
    ) == []


def test_invalid_url():
    rule = FieldRule(field_type="url")

    errors = validate_value(
        "source_url",
        "not-a-url",
        rule,
    )

    assert len(errors) == 1


def test_null_value_allowed():
    rule = FieldRule(
        field_type="text",
        nullable=True,
    )

    assert validate_value(
        "description",
        None,
        rule,
    ) == []


def test_null_value_rejected():
    rule = FieldRule(
        field_type="text",
        nullable=False,
    )

    errors = validate_value(
        "description",
        None,
        rule,
    )

    assert len(errors) == 1
    assert "cannot be null" in errors[0]


def test_allowed_values():
    rule = FieldRule(
        field_type="text",
        allowed_values=("active", "inactive"),
    )

    assert validate_value(
        "status",
        "active",
        rule,
    ) == []


def test_disallowed_value():
    rule = FieldRule(
        field_type="text",
        allowed_values=("active", "inactive"),
    )

    errors = validate_value(
        "status",
        "unknown",
        rule,
    )

    assert len(errors) == 1


def test_required_field_missing():
    schema = {
        "title": FieldRule(
            field_type="text",
            required=True,
        )
    }

    result = validate_record({}, schema)

    assert result.valid is False
    assert result.error_count == 1


def test_optional_field_missing():
    schema = {
        "description": FieldRule(
            field_type="text",
            required=False,
        )
    }

    result = validate_record({}, schema)

    assert result.valid is True
    assert result.error_count == 0


def test_valid_record():
    schema = {
        "title": FieldRule(
            field_type="text",
            required=True,
        ),
        "score": FieldRule(
            field_type="number",
            minimum=0,
            maximum=100,
        ),
        "active": FieldRule(
            field_type="boolean",
        ),
    }

    record = {
        "title": "Environmental Consultant",
        "score": 95,
        "active": True,
    }

    result = validate_record(record, schema)

    assert result.valid is True
    assert result.errors == []


def test_invalid_record_collects_multiple_errors():
    schema = {
        "title": FieldRule(
            field_type="text",
            required=True,
        ),
        "score": FieldRule(
            field_type="number",
            minimum=0,
            maximum=100,
        ),
    }

    record = {
        "title": 123,
        "score": 150,
    }

    result = validate_record(record, schema)

    assert result.valid is False
    assert result.error_count == 2