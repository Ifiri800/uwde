from backend.app.services.intelligence.methane.quality.completeness import (
    assess_completeness,
)
from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)


def test_complete_records_pass():
    result = assess_completeness(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "B", "emissions": 20},
        ),
        required_fields=("facility", "emissions"),
    )

    assert result.dimension == QualityDimension.COMPLETENESS
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_missing_required_field_is_detected():
    result = assess_completeness(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "B"},
        ),
        required_fields=("facility", "emissions"),
    )

    assert result.status == QualityStatus.WARNING
    assert result.score == 75.0
    assert result.issue_count == 1
    assert result.issues[0].field == "emissions"


def test_severe_incompleteness_fails():
    result = assess_completeness(
        records=(
            {"facility": "A"},
            {},
        ),
        required_fields=("facility", "emissions"),
    )

    assert result.status == QualityStatus.FAIL
    assert result.score == 25.0


def test_empty_dataset_is_not_assessed():
    result = assess_completeness(
        records=(),
        required_fields=("facility",),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_empty_required_fields_is_not_assessed():
    result = assess_completeness(
        records=({"facility": "A"},),
        required_fields=(),
    )

    assert result.status == QualityStatus.NOT_ASSESSED


def test_invalid_records_type_fails():
    result = assess_completeness(
        records="invalid",
        required_fields=("facility",),
    )

    assert result.status == QualityStatus.FAIL
    assert result.score == 0.0


def test_invalid_record_is_reported():
    result = assess_completeness(
        records=(
            {"facility": "A"},
            "invalid",
        ),
        required_fields=("facility",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.score == 50.0
    assert result.issue_count == 1
    assert result.issues[0].code == "invalid_record"
