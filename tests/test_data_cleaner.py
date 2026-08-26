from backend.app.services.preprocessing.cleaner import (
    clean_record,
    clean_text,
    clean_value,
)


def test_clean_text_removes_leading_and_trailing_whitespace():
    assert clean_text("  Environmental Consultant  ") == "Environmental Consultant"


def test_clean_text_collapses_repeated_whitespace():
    assert clean_text("Environmental   Impact    Assessment") == (
        "Environmental Impact Assessment"
    )


def test_clean_text_handles_newlines_and_tabs():
    assert clean_text("Environmental\nImpact\tAssessment") == (
        "Environmental Impact Assessment"
    )


def test_clean_value_preserves_empty_string_by_default():
    assert clean_value("   ") == ""


def test_clean_value_removes_empty_string_when_configured():
    assert clean_value("   ", remove_empty=True) is None


def test_clean_value_preserves_numbers():
    assert clean_value(123.45) == 123.45


def test_clean_value_preserves_booleans():
    assert clean_value(True) is True


def test_clean_value_cleans_nested_dictionary():
    value = {
        "title": "  Environmental Consultant  ",
        "location": " Lagos   Nigeria ",
    }

    assert clean_value(value) == {
        "title": "Environmental Consultant",
        "location": "Lagos Nigeria",
    }


def test_clean_value_cleans_lists():
    value = [
        "  Lagos  ",
        " Abuja ",
        "Port\tHarcourt",
    ]

    assert clean_value(value) == [
        "Lagos",
        "Abuja",
        "Port Harcourt",
    ]


def test_clean_record_cleans_complete_record():
    record = {
        "name": "  UWDE  ",
        "description": " Universal   Web\nData Extractor ",
        "records": 25,
        "active": True,
    }

    assert clean_record(record) == {
        "name": "UWDE",
        "description": "Universal Web Data Extractor",
        "records": 25,
        "active": True,
    }


def test_clean_record_can_remove_empty_values():
    record = {
        "name": "  UWDE  ",
        "description": "   ",
        "location": None,
    }

    assert clean_record(record, remove_empty=True) == {
        "name": "UWDE",
    }