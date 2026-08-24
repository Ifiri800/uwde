from datetime import datetime, timezone

import pytest

from backend.app.services.reconciliation.conflicts import Conflict
from backend.app.services.reconciliation.provenance import (
    SourcedValue,
    create_provenance,
)
from backend.app.services.reconciliation.uncertainty import (
    Uncertainty,
    calculate_conflict_uncertainty,
    calculate_source_confidence,
    calculate_uncertainty,
)


def make_sourced_value(
    value,
    source_url,
    *,
    confidence=None,
    field_name="value",
):
    provenance = create_provenance(
        source_url,
        field_name=field_name,
        confidence=confidence,
    )

    return SourcedValue(
        value=value,
        provenance=provenance,
    )


def test_calculate_uncertainty_from_confidence():
    result = calculate_uncertainty(0.80)

    assert isinstance(result, Uncertainty)
    assert result.confidence == 0.80
    assert result.uncertainty == pytest.approx(0.20)
    assert result.level == "high"


def test_zero_confidence_has_complete_uncertainty():
    result = calculate_uncertainty(0.0)

    assert result.confidence == 0.0
    assert result.uncertainty == 1.0
    assert result.level == "very_low"


def test_full_confidence_has_zero_uncertainty():
    result = calculate_uncertainty(1.0)

    assert result.confidence == 1.0
    assert result.uncertainty == 0.0
    assert result.level == "very_high"


def test_confidence_level_boundaries():
    assert calculate_uncertainty(0.19).level == "very_low"
    assert calculate_uncertainty(0.20).level == "low"
    assert calculate_uncertainty(0.39).level == "low"
    assert calculate_uncertainty(0.40).level == "medium"
    assert calculate_uncertainty(0.69).level == "medium"
    assert calculate_uncertainty(0.70).level == "high"
    assert calculate_uncertainty(0.89).level == "high"
    assert calculate_uncertainty(0.90).level == "very_high"


def test_low_confidence_requires_review():
    result = calculate_uncertainty(
        0.30,
        review_threshold=0.50,
    )

    assert result.requires_review is True


def test_high_confidence_does_not_require_review_without_conflict():
    result = calculate_uncertainty(
        0.90,
        review_threshold=0.50,
    )

    assert result.requires_review is False


def test_conflicting_sources_require_review():
    result = calculate_uncertainty(
        0.95,
        supporting_sources=3,
        conflicting_sources=1,
    )

    assert result.requires_review is True
    assert result.supporting_sources == 3
    assert result.conflicting_sources == 1


def test_source_counts_are_preserved():
    result = calculate_uncertainty(
        0.75,
        supporting_sources=4,
        conflicting_sources=2,
    )

    assert result.supporting_sources == 4
    assert result.conflicting_sources == 2


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValueError):
        calculate_uncertainty(-0.01)

    with pytest.raises(ValueError):
        calculate_uncertainty(1.01)


def test_invalid_source_counts_are_rejected():
    with pytest.raises(ValueError):
        calculate_uncertainty(
            0.80,
            supporting_sources=-1,
        )

    with pytest.raises(ValueError):
        calculate_uncertainty(
            0.80,
            conflicting_sources=-1,
        )


def test_invalid_review_threshold_is_rejected():
    with pytest.raises(ValueError):
        calculate_uncertainty(
            0.80,
            review_threshold=-0.1,
        )

    with pytest.raises(ValueError):
        calculate_uncertainty(
            0.80,
            review_threshold=1.1,
        )


def test_calculate_source_confidence_returns_average():
    observations = [
        make_sourced_value(
            100,
            "https://source-a.example",
            confidence=0.60,
        ),
        make_sourced_value(
            100,
            "https://source-b.example",
            confidence=0.80,
        ),
    ]

    result = calculate_source_confidence(observations)

    assert result == pytest.approx(0.70)


def test_missing_confidence_is_treated_as_zero():
    observations = [
        make_sourced_value(
            100,
            "https://source-a.example",
            confidence=None,
        ),
        make_sourced_value(
            100,
            "https://source-b.example",
            confidence=0.80,
        ),
    ]

    result = calculate_source_confidence(observations)

    assert result == pytest.approx(0.40)


def test_empty_observations_have_zero_confidence():
    result = calculate_source_confidence([])

    assert result == 0.0


def test_conflict_uncertainty_uses_strongest_confidence():
    observations = [
        make_sourced_value(
            420,
            "https://source-a.example",
            confidence=0.70,
        ),
        make_sourced_value(
            420,
            "https://source-b.example",
            confidence=0.90,
        ),
        make_sourced_value(
            418,
            "https://source-c.example",
            confidence=0.60,
        ),
    ]

    conflict = Conflict(
        field_name="concentration",
        values=(420, 418),
        observations=tuple(observations),
    )

    result = calculate_conflict_uncertainty(conflict)

    assert result.confidence == pytest.approx(0.90)
    assert result.uncertainty == pytest.approx(0.10)
    assert result.supporting_sources == 2
    assert result.conflicting_sources == 1
    assert result.requires_review is True


def test_conflict_with_all_sources_agree_has_no_conflicting_sources():
    observations = [
        make_sourced_value(
            "Nigeria",
            "https://source-a.example",
            confidence=0.80,
        ),
        make_sourced_value(
            "Nigeria",
            "https://source-b.example",
            confidence=0.90,
        ),
    ]

    conflict = Conflict(
        field_name="country",
        values=("Nigeria",),
        observations=tuple(observations),
    )

    result = calculate_conflict_uncertainty(conflict)

    assert result.supporting_sources == 2
    assert result.conflicting_sources == 0
    assert result.requires_review is False


def test_empty_conflict_has_zero_confidence():
    conflict = Conflict(
        field_name="value",
        values=(),
        observations=(),
    )

    result = calculate_conflict_uncertainty(conflict)

    assert result.confidence == 0.0
    assert result.uncertainty == 1.0
    assert result.supporting_sources == 0
    assert result.conflicting_sources == 0
    assert result.requires_review is True