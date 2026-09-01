from backend.app.services.intelligence.methane.quality.accuracy import (
    assess_accuracy,
)
from backend.app.services.intelligence.methane.quality.models import (
    QualityDimension,
    QualityStatus,
)


def test_valid_numeric_values_pass():
    result = assess_accuracy(
        records=(
            {"emissions": 10.0},
            {"emissions": 20.0},
        ),
        numeric_fields=("emissions",),
    )

    assert result.dimension == QualityDimension.ACCURACY
    assert result.status == QualityStatus.PASS
    assert result.score == 100.0
    assert result.issue_count == 0


def test_invalid_numeric_value_is_warning():
    result = assess_accuracy(
        records=(
            {"emissions": 10.0},
            {"emissions": "invalid"},
        ),
        numeric_fields=("emissions",),
    )

    assert result.status == QualityStatus.WARNING
    assert result.score == 50.0
    assert result.issue_count == 1


def test_value_below_minimum_is_detected():
    result = assess_accuracy(
        records=(
            {"emissions": 10.0},
            {"emissions": -5.0},
        ),
        numeric_fields=("emissions",),
        minimums={"emissions": 0.0},
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_value_above_maximum_is_detected():
    result = assess_accuracy(
        records=(
            {"emissions": 10.0},
            {"emissions": 150.0},
        ),
        numeric_fields=("emissions",),
        maximums={"emissions": 100.0},
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_tolerance_check():
    result = assess_accuracy(
        records=(
            {"emissions": 100.0},
            {"emissions": 101.0},
        ),
        reference_values={"emissions": 100.0},
        tolerances={"emissions": 0.5},
    )

    assert result.status == QualityStatus.WARNING
    assert result.issue_count == 1


def test_missing_accuracy_configuration_is_not_assessed():
    result = assess_accuracy(
        records=(
            {"facility": "A"},
            {"facility": "B"},
        )
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None


def test_empty_records_are_not_assessed():
    result = assess_accuracy(
        records=(),
        numeric_fields=("emissions",),
    )

    assert result.status == QualityStatus.NOT_ASSESSED
    assert result.score is None
