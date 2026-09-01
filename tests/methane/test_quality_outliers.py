from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)
from backend.app.services.intelligence.methane.quality.outliers import (
    assess_outliers,
)


def test_no_outliers_pass():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": 11},
            {"emissions": 12},
            {"emissions": 13},
            {"emissions": 14},
        ),
        fields=("emissions",),
    )

    assert result.dimension == QualityDimension.OUTLIERS
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_extreme_value_is_detected():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": 11},
            {"emissions": 12},
            {"emissions": 13},
            {"emissions": 1000},
        ),
        fields=("emissions",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1
    assert result.issues[0].field == "emissions"


def test_multiple_fields_are_assessed():
    result = assess_outliers(
        records=(
            {"emissions": 10, "throughput": 100},
            {"emissions": 11, "throughput": 101},
            {"emissions": 12, "throughput": 102},
            {"emissions": 13, "throughput": 103},
            {"emissions": 1000, "throughput": 10000},
        ),
        fields=("emissions", "throughput"),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 2


def test_non_numeric_value_is_reported():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": "invalid"},
            {"emissions": 12},
        ),
        fields=("emissions",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1
    assert result.issues[0].code == "non_numeric_value"


def test_missing_value_is_reported():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {},
            {"emissions": 12},
        ),
        fields=("emissions",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1
    assert result.issues[0].code == "missing_value"


def test_insufficient_values_are_not_assessed():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": 11},
        ),
        fields=("emissions",),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_empty_records_are_not_assessed():
    result = assess_outliers(
        records=(),
        fields=("emissions",),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_no_fields_are_not_assessed():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": 11},
            {"emissions": 12},
        ),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_custom_iqr_multiplier_is_supported():
    result = assess_outliers(
        records=(
            {"emissions": 10},
            {"emissions": 11},
            {"emissions": 12},
            {"emissions": 13},
            {"emissions": 100},
        ),
        fields=("emissions",),
        iqr_multiplier=1.5,
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1
