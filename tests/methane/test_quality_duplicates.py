from backend.app.services.intelligence.methane.quality.duplicates import (
    assess_duplicates,
)
from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)


def test_unique_records_pass():
    result = assess_duplicates(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "B", "emissions": 20},
        ),
    )

    assert result.dimension == QualityDimension.DUPLICATES
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_exact_duplicate_is_detected():
    result = assess_duplicates(
        records=(
            {"facility": "A", "emissions": 10},
            {"facility": "A", "emissions": 10},
        ),
    )

    assert result.status == QualityStatus.WARNING
    assert result.score == 50.0
    assert result.issue_count == 1


def test_identity_fields_detect_duplicates():
    result = assess_duplicates(
        records=(
            {"facility": "A", "date": "2026-01-01", "emissions": 10},
            {"facility": "A", "date": "2026-01-01", "emissions": 12},
        ),
        identity_fields=("facility", "date"),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_different_identity_fields_are_not_duplicates():
    result = assess_duplicates(
        records=(
            {"facility": "A", "date": "2026-01-01"},
            {"facility": "A", "date": "2026-01-02"},
        ),
        identity_fields=("facility", "date"),
    )

    assert result.status == QualityStatus.PASS
    assert result.score == 100.0


def test_invalid_record_is_reported():
    result = assess_duplicates(
        records=(
            {"facility": "A"},
            "invalid",
        ),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_empty_records_are_not_assessed():
    result = assess_duplicates(records=())

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_duplicate_configuration_can_be_disabled():
    result = assess_duplicates(
        records=(
            {"facility": "A"},
            {"facility": "A"},
        ),
        enabled=False,
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None
