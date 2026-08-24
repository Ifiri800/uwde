from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.reconciliation.conflicts import (
    Conflict,
)
from backend.app.services.reconciliation.provenance import (
    SourcedValue,
    create_provenance,
)
from backend.app.services.reconciliation.resolver import (
    Resolution,
    resolve_conflict,
    resolve_conflicts,
)


def make_sourced_value(
    value,
    source_url,
    *,
    confidence=None,
    extracted_at=None,
    field_name="value",
):
    provenance = create_provenance(
        source_url,
        field_name=field_name,
        confidence=confidence,
    )

    if extracted_at is not None:
        provenance = type(provenance)(
            source_url=provenance.source_url,
            source_id=provenance.source_id,
            field_name=provenance.field_name,
            extraction_method=provenance.extraction_method,
            extracted_at=extracted_at,
            confidence=provenance.confidence,
            metadata=provenance.metadata,
        )

    return SourcedValue(
        value=value,
        provenance=provenance,
    )


def make_conflict(observations):
    return Conflict(
        field_name="value",
        values=tuple(
            dict.fromkeys(
                observation.value
                for observation in observations
            )
        ),
        observations=tuple(observations),
    )


def test_majority_strategy_selects_most_supported_value():
    observations = [
        make_sourced_value(
            "Nigeria",
            "https://source-a.example",
            confidence=0.7,
        ),
        make_sourced_value(
            "Nigeria",
            "https://source-b.example",
            confidence=0.8,
        ),
        make_sourced_value(
            "Ghana",
            "https://source-c.example",
            confidence=0.99,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "majority",
    )

    assert isinstance(result, Resolution)
    assert result.value == "Nigeria"
    assert result.strategy == "majority"
    assert result.selected_observation is not None
    assert result.selected_observation.value == "Nigeria"
    assert result.resolved is True
    assert result.requires_review is False


def test_highest_confidence_strategy_selects_highest_confidence():
    observations = [
        make_sourced_value(
            "Nigeria",
            "https://source-a.example",
            confidence=0.70,
        ),
        make_sourced_value(
            "Ghana",
            "https://source-b.example",
            confidence=0.95,
        ),
        make_sourced_value(
            "Kenya",
            "https://source-c.example",
            confidence=0.80,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "highest_confidence",
    )

    assert result.value == "Ghana"
    assert result.selected_observation is not None
    assert result.selected_observation.value == "Ghana"
    assert result.selected_observation.provenance.confidence == 0.95


def test_latest_strategy_selects_latest_observation():
    now = datetime.now(timezone.utc)

    observations = [
        make_sourced_value(
            "old",
            "https://source-a.example",
            confidence=0.99,
            extracted_at=now - timedelta(hours=2),
        ),
        make_sourced_value(
            "new",
            "https://source-b.example",
            confidence=0.50,
            extracted_at=now,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "latest",
    )

    assert result.value == "new"
    assert result.selected_observation is not None
    assert result.selected_observation.value == "new"


def test_weighted_strategy_prefers_value_with_highest_combined_confidence():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
            confidence=0.60,
        ),
        make_sourced_value(
            "A",
            "https://source-b.example",
            confidence=0.70,
        ),
        make_sourced_value(
            "B",
            "https://source-c.example",
            confidence=0.90,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "weighted",
    )

    assert result.value == "A"


def test_manual_strategy_requires_review():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
            confidence=0.8,
        ),
        make_sourced_value(
            "B",
            "https://source-b.example",
            confidence=0.9,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "manual",
    )

    assert result.value is None
    assert result.selected_observation is None
    assert result.requires_review is True
    assert result.resolved is False


def test_none_strategy_preserves_conflict_without_resolution():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
        ),
        make_sourced_value(
            "B",
            "https://source-b.example",
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "none",
    )

    assert result.value is None
    assert result.selected_observation is None
    assert result.requires_review is False
    assert result.resolved is False
    assert result.conflict is conflict


def test_resolution_preserves_original_conflict():
    observations = [
        make_sourced_value(
            100,
            "https://source-a.example",
            confidence=0.7,
        ),
        make_sourced_value(
            200,
            "https://source-b.example",
            confidence=0.9,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "highest_confidence",
    )

    assert result.conflict is conflict
    assert result.conflict.observations == tuple(observations)
    assert result.conflict.values == (100, 200)


def test_missing_confidence_is_treated_as_zero():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
            confidence=None,
        ),
        make_sourced_value(
            "B",
            "https://source-b.example",
            confidence=0.5,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "highest_confidence",
    )

    assert result.value == "B"


def test_highest_confidence_tie_uses_latest_observation():
    now = datetime.now(timezone.utc)

    observations = [
        make_sourced_value(
            "old",
            "https://source-a.example",
            confidence=0.9,
            extracted_at=now - timedelta(hours=1),
        ),
        make_sourced_value(
            "new",
            "https://source-b.example",
            confidence=0.9,
            extracted_at=now,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "highest_confidence",
    )

    assert result.value == "new"


def test_majority_tie_uses_confidence():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
            confidence=0.60,
        ),
        make_sourced_value(
            "B",
            "https://source-b.example",
            confidence=0.95,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "majority",
    )

    assert result.value == "B"


def test_weighted_strategy_sums_confidence_by_value():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
            confidence=0.40,
        ),
        make_sourced_value(
            "A",
            "https://source-b.example",
            confidence=0.40,
        ),
        make_sourced_value(
            "B",
            "https://source-c.example",
            confidence=0.70,
        ),
    ]

    conflict = make_conflict(observations)

    result = resolve_conflict(
        conflict,
        "weighted",
    )

    assert result.value == "A"


def test_resolve_multiple_conflicts():
    first_observations = [
        make_sourced_value(
            "Nigeria",
            "https://source-a.example",
            confidence=0.9,
        ),
        make_sourced_value(
            "Ghana",
            "https://source-b.example",
            confidence=0.7,
        ),
    ]

    second_observations = [
        make_sourced_value(
            100,
            "https://source-a.example",
            confidence=0.6,
        ),
        make_sourced_value(
            200,
            "https://source-b.example",
            confidence=0.95,
        ),
    ]

    first_conflict = Conflict(
        field_name="country",
        values=("Nigeria", "Ghana"),
        observations=tuple(first_observations),
    )

    second_conflict = Conflict(
        field_name="score",
        values=(100, 200),
        observations=tuple(second_observations),
    )

    results = resolve_conflicts(
        [first_conflict, second_conflict],
        "highest_confidence",
    )

    assert len(results) == 2
    assert results[0].field_name == "country"
    assert results[0].value == "Nigeria"
    assert results[1].field_name == "score"
    assert results[1].value == 200


def test_unsupported_strategy_raises_value_error():
    observations = [
        make_sourced_value(
            "A",
            "https://source-a.example",
        ),
        make_sourced_value(
            "B",
            "https://source-b.example",
        ),
    ]

    conflict = make_conflict(observations)

    with pytest.raises(ValueError):
        resolve_conflict(
            conflict,
            "unsupported",
        )