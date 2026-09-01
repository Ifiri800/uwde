from backend.app.services.intelligence.methane.quality.models import (
    QualityAssessment,
    QualityDimension,
    QualityStatus,
)
from backend.app.services.intelligence.methane.quality.scoring import (
    calculate_quality_score,
)


def assessment(
    dimension,
    status=QualityStatus.PASS,
    score=100.0,
):
    return QualityAssessment(
        dimension=dimension,
        status=status,
        score=score,
    )


def test_all_dimensions_are_aggregated():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                score=90.0,
            ),
            assessment(
                QualityDimension.ACCURACY,
                score=80.0,
            ),
        )
    )

    assert result.overall == 85.0
    assert result.dimension_count == 2
    assert (
        result.dimensions[QualityDimension.COMPLETENESS]
        == 90.0
    )
    assert (
        result.dimensions[QualityDimension.ACCURACY]
        == 80.0
    )


def test_equal_weights_are_used_by_default():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                score=100.0,
            ),
            assessment(
                QualityDimension.ACCURACY,
                score=60.0,
            ),
            assessment(
                QualityDimension.CONSISTENCY,
                score=80.0,
            ),
        )
    )

    assert result.overall == 80.0


def test_custom_weights_are_supported():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                score=100.0,
            ),
            assessment(
                QualityDimension.ACCURACY,
                score=50.0,
            ),
        ),
        weights={
            QualityDimension.COMPLETENESS: 3.0,
            QualityDimension.ACCURACY: 1.0,
        },
    )

    assert result.overall == 87.5


def test_not_assessed_dimensions_are_excluded():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                score=100.0,
            ),
            assessment(
                QualityDimension.ACCURACY,
                status=QualityStatus.NOT_ASSESSED,
                score=None,
            ),
        )
    )

    assert result.overall == 100.0
    assert result.dimension_count == 1


def test_none_score_is_excluded():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                status=QualityStatus.WARNING,
                score=None,
            ),
            assessment(
                QualityDimension.ACCURACY,
                score=80.0,
            ),
        )
    )

    assert result.overall == 80.0
    assert result.dimension_count == 1


def test_failed_assessment_can_still_contribute_score():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.ACCURACY,
                status=QualityStatus.FAIL,
                score=40.0,
            ),
        )
    )

    assert result.overall == 40.0


def test_empty_assessments_return_zero():
    result = calculate_quality_score(
        assessments=()
    )

    assert result.overall == 0.0
    assert result.dimension_count == 0


def test_scores_are_rounded():
    result = calculate_quality_score(
        assessments=(
            assessment(
                QualityDimension.COMPLETENESS,
                score=33.3333,
            ),
            assessment(
                QualityDimension.ACCURACY,
                score=66.6666,
            ),
        )
    )

    assert result.overall == 50.0


def test_duplicate_dimensions_are_rejected():
    try:
        calculate_quality_score(
            assessments=(
                assessment(
                    QualityDimension.ACCURACY,
                    score=80.0,
                ),
                assessment(
                    QualityDimension.ACCURACY,
                    score=90.0,
                ),
            )
        )
    except ValueError as exc:
        assert "duplicate" in str(exc).lower()
    else:
        raise AssertionError(
            "duplicate dimensions should be rejected"
        )


def test_invalid_assessment_type_is_rejected():
    try:
        calculate_quality_score(
            assessments=("invalid",)
        )
    except TypeError:
        pass
    else:
        raise AssertionError(
            "invalid assessment should raise TypeError"
        )


def test_invalid_score_is_rejected():
    try:
        calculate_quality_score(
            assessments=(
                assessment(
                    QualityDimension.ACCURACY,
                    score=101.0,
                ),
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "score above 100 should be rejected"
        )


def test_negative_score_is_rejected():
    try:
        calculate_quality_score(
            assessments=(
                assessment(
                    QualityDimension.ACCURACY,
                    score=-1.0,
                ),
            )
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "negative score should be rejected"
        )


def test_invalid_weight_is_rejected():
    try:
        calculate_quality_score(
            assessments=(
                assessment(
                    QualityDimension.ACCURACY,
                    score=80.0,
                ),
            ),
            weights={
                QualityDimension.ACCURACY: -1.0,
            },
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "negative weight should be rejected"
        )
