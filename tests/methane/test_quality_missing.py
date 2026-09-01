from backend.app.services.intelligence.methane.quality.missing import (
    assess_missing,
)
from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)


def test_no_missing_values_pass():
    result = assess_missing(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "B", "emissions": 20},
        ),
        fields=("facility", "emissions"),
    )

    assert result.dimension == QualityDimension.MISSING
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_none_value_is_detected():
    result = assess_missing(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "B", "emissions": None},
        ),
        fields=("facility", "emissions"),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_blank_string_is_detected():
    result = assess_missing(
        records=(
            {"facility": "A"},
            {"facility": ""},
        ),
        fields=("facility",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_whitespace_is_detected():
    result = assess_missing(
        records=(
            {"facility": "A"},
            {"facility": "   "},
        ),
        fields=("facility",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_missing_field_is_detected():
    result = assess_missing(
        records=(
            {"facility": "A"},
            {},
        ),
        fields=("facility",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_invalid_record_is_reported():
    result = assess_missing(
        records=(
            {"facility": "A"},
            "invalid",
        ),
        fields=("facility",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_no_fields_is_not_assessed():
    result = assess_missing(
        records=(
            {"facility": "A"},
        ),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_empty_records_are_not_assessed():
    result = assess_missing(
        records=(),
        fields=("facility",),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None
