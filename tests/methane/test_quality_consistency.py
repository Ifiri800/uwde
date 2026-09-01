from backend.app.services.intelligence.methane.quality.consistency import (
    assess_consistency,
)
from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)


def test_consistent_records_pass():
    result = assess_consistency(
        records=(
            {"facility": "A", "status": "active"},
            {"facility": "B", "status": "active"},
        ),
        field_types={"status": str},
    )

    assert result.dimension == QualityDimension.CONSISTENCY
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_inconsistent_field_type_is_detected():
    result = assess_consistency(
        records=(
            {"facility": "A", "status": "active"},
            {"facility": "B", "status": 1},
        ),
        field_types={"status": str},
    )

    assert result.status == QualityStatus.WARNING
    assert result.score == 50.0
    assert result.issue_count == 1


def test_allowed_values_are_enforced():
    result = assess_consistency(
        records=(
            {"facility": "A", "status": "active"},
            {"facility": "B", "status": "closed"},
        ),
        allowed_values={
            "status": ("active", "inactive"),
        },
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_missing_field_is_reported():
    result = assess_consistency(
        records=(
            {"facility": "A", "status": "active"},
            {"facility": "B"},
        ),
        field_types={"status": str},
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_invalid_record_is_reported():
    result = assess_consistency(
        records=(
            {"facility": "A"},
            "invalid",
        ),
        field_types={"facility": str},
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_no_configuration_is_not_assessed():
    result = assess_consistency(
        records=(
            {"facility": "A"},
            {"facility": "B"},
        ),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_empty_records_are_not_assessed():
    result = assess_consistency(
        records=(),
        field_types={"facility": str},
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None
