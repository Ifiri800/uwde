from backend.app.services.pipeline_validator import (
    validate_pipeline_input,
    validate_pipeline_output,
)


def test_valid_pipeline_input():
    result = validate_pipeline_input(
        "https://example.com",
        "Extract title",
    )

    assert result.valid is True
    assert result.issues == []


def test_empty_url_is_rejected():
    result = validate_pipeline_input(
        "",
        "Extract title",
    )

    assert result.valid is False
    assert result.errors[0].code == "EMPTY_URL"


def test_empty_instruction_is_rejected():
    result = validate_pipeline_input(
        "https://example.com",
        "",
    )

    assert result.valid is False
    assert result.errors[0].code == (
        "EMPTY_INSTRUCTION"
    )


def test_valid_records():
    records = [
        {
            "title": "Environmental Consultant",
            "location": "Abuja",
        },
        {
            "title": "WASH Specialist",
            "location": "Kaduna",
        },
    ]

    result = validate_pipeline_output(
        records,
        required_fields={
            "title",
            "location",
        },
    )

    assert result.valid is True
    assert result.record_count == 2
    assert result.errors == []


def test_missing_required_field():
    records = [
        {
            "title": "Environmental Consultant",
        }
    ]

    result = validate_pipeline_output(
        records,
        required_fields={
            "title",
            "location",
        },
    )

    assert result.valid is False
    assert len(result.errors) == 1
    assert result.errors[0].code == (
        "MISSING_REQUIRED_FIELD"
    )
    assert result.errors[0].field == "location"


def test_empty_required_field():
    records = [
        {
            "title": "",
            "location": "Abuja",
        }
    ]

    result = validate_pipeline_output(
        records,
        required_fields={"title"},
    )

    assert result.valid is False
    assert result.errors[0].code == (
        "EMPTY_REQUIRED_FIELD"
    )


def test_invalid_record_is_rejected():
    records = [
        "not-a-record",
    ]

    result = validate_pipeline_output(
        records,
    )

    assert result.valid is False
    assert result.errors[0].code == (
        "INVALID_RECORD"
    )


def test_empty_records_generate_warning():
    result = validate_pipeline_output([])

    assert result.valid is True
    assert result.record_count == 0
    assert len(result.warnings) == 1
    assert result.warnings[0].code == "NO_RECORDS"


def test_validation_result_is_serializable():
    records = [
        {
            "title": "Environmental Consultant",
        }
    ]

    result = validate_pipeline_output(
        records,
        required_fields={"title"},
    )

    data = result.to_dict()

    assert data["valid"] is True
    assert data["record_count"] == 1
    assert data["error_count"] == 0
    assert data["warning_count"] == 0