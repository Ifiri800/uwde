from __future__ import annotations

from collections.abc import Mapping

from .models import (
    QualityAssessment,
    QualityDimension,
    QualityScore,
    QualityStatus,
)


def calculate_quality_score(
    assessments: tuple[QualityAssessment, ...],
    weights: Mapping[QualityDimension, float] | None = None,
) -> QualityScore:
    """
    Aggregate assessed Layer 6 quality dimensions.

    Only assessments with a numeric score contribute to the
    overall score. NOT_ASSESSED dimensions and assessments
    without scores are excluded.

    Scores must be within 0..100.

    By default, every assessed dimension has equal weight.
    """

    if not isinstance(assessments, tuple):
        raise TypeError(
            "assessments must be a tuple"
        )

    configured_weights = weights or {}

    if not isinstance(configured_weights, Mapping):
        raise TypeError(
            "weights must be a mapping"
        )

    dimensions: dict[QualityDimension, float] = {}
    used_weights: dict[QualityDimension, float] = {}

    for assessment in assessments:
        if not isinstance(
            assessment,
            QualityAssessment,
        ):
            raise TypeError(
                "all assessments must be QualityAssessment"
            )

        dimension = assessment.dimension

        if dimension in dimensions:
            raise ValueError(
                f"duplicate quality dimension: {dimension.value}"
            )

        score = assessment.score

        if (
            assessment.status
            == QualityStatus.NOT_ASSESSED
            or score is None
        ):
            continue

        if not isinstance(score, (int, float)):
            raise TypeError(
                "quality score must be numeric"
            )

        if not 0.0 <= float(score) <= 100.0:
            raise ValueError(
                "quality score must be between 0 and 100"
            )

        weight = configured_weights.get(
            dimension,
            1.0,
        )

        if not isinstance(weight, (int, float)):
            raise TypeError(
                "quality weight must be numeric"
            )

        if weight <= 0:
            raise ValueError(
                "quality weight must be greater than zero"
            )

        dimensions[dimension] = round(
            float(score),
            2,
        )
        used_weights[dimension] = float(weight)

    if not dimensions:
        return QualityScore(
            overall=0.0,
            dimensions={},
        )

    weighted_total = sum(
        dimensions[dimension]
        * used_weights[dimension]
        for dimension in dimensions
    )

    total_weight = sum(
        used_weights.values()
    )

    overall = round(
        weighted_total / total_weight,
        2,
    )

    return QualityScore(
        overall=overall,
        dimensions=dict(dimensions),
    )
