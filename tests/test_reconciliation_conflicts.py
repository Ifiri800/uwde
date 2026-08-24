from backend.app.services.reconciliation.conflicts import (
    Conflict,
    detect_conflict,
    detect_conflicts,
)
from backend.app.services.reconciliation.provenance import (
    SourcedValue,
    create_provenance,
)


def make_sourced_value(
    value,
    source_url,
    field_name="value",
    confidence=0.9,
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


def test_no_conflict_with_single_observation():
    observation = make_sourced_value(
        "420",
        "https://source-a.example",
    )

    result = detect_conflict(
        "concentration",
        [observation],
    )

    assert result is None


def test_no_conflict_when_values_are_identical():
    observations = [
        make_sourced_value(
            420,
            "https://source-a.example",
        ),
        make_sourced_value(
            420,
            "https://source-b.example",
        ),
    ]

    result = detect_conflict(
        "concentration",
        observations,
    )

    assert result is None


def test_detects_two_value_conflict():
    observations = [
        make_sourced_value(
            420,
            "https://source-a.example",
        ),
        make_sourced_value(
            418,
            "https://source-b.example",
        ),
    ]

    result = detect_conflict(
        "concentration",
        observations,
    )

    assert isinstance(result, Conflict)
    assert result.field_name == "concentration"
    assert result.values == (420, 418)
    assert result.source_count == 2
    assert result.value_count == 2
    assert result.is_conflict is True


def test_detects_multiple_value_conflict():
    observations = [
        make_sourced_value(
            420,
            "https://source-a.example",
        ),
        make_sourced_value(
            418,
            "https://source-b.example",
        ),
        make_sourced_value(
            421,
            "https://source-c.example",
        ),
    ]

    result = detect_conflict(
        "concentration",
        observations,
    )

    assert result is not None
    assert result.values == (420, 418, 421)
    assert result.source_count == 3
    assert result.value_count == 3


def test_duplicate_values_are_counted_once_as_distinct_values():
    observations = [
        make_sourced_value(
            420,
            "https://source-a.example",
        ),
        make_sourced_value(
            420,
            "https://source-b.example",
        ),
        make_sourced_value(
            418,
            "https://source-c.example",
        ),
    ]

    result = detect_conflict(
        "concentration",
        observations,
    )

    assert result is not None
    assert result.values == (420, 418)
    assert result.source_count == 3
    assert result.value_count == 2


def test_conflict_preserves_observations():
    observations = [
        make_sourced_value(
            "Nigeria",
            "https://source-a.example",
            field_name="country",
        ),
        make_sourced_value(
            "Ghana",
            "https://source-b.example",
            field_name="country",
        ),
    ]

    result = detect_conflict(
        "country",
        observations,
    )

    assert result is not None
    assert result.observations == tuple(observations)
    assert result.observations[0].value == "Nigeria"
    assert result.observations[1].value == "Ghana"


def test_conflict_preserves_provenance():
    observations = [
        make_sourced_value(
            100,
            "https://source-a.example",
            confidence=0.95,
        ),
        make_sourced_value(
            200,
            "https://source-b.example",
            confidence=0.75,
        ),
    ]

    result = detect_conflict(
        "value",
        observations,
    )

    assert result is not None

    assert (
        result.observations[0].provenance.source_url
        == "https://source-a.example"
    )

    assert (
        result.observations[0].provenance.confidence
        == 0.95
    )

    assert (
        result.observations[1].provenance.source_url
        == "https://source-b.example"
    )

    assert (
        result.observations[1].provenance.confidence
        == 0.75
    )


def test_detect_conflicts_across_multiple_fields():
    observations_by_field = {
        "title": [
            make_sourced_value(
                "Environmental Consultant",
                "https://source-a.example",
                field_name="title",
            ),
            make_sourced_value(
                "Environmental Specialist",
                "https://source-b.example",
                field_name="title",
            ),
        ],
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
                field_name="country",
            ),
            make_sourced_value(
                "Nigeria",
                "https://source-b.example",
                field_name="country",
            ),
        ],
        "salary": [
            make_sourced_value(
                125000,
                "https://source-a.example",
                field_name="salary",
            ),
            make_sourced_value(
                150000,
                "https://source-b.example",
                field_name="salary",
            ),
        ],
    }

    conflicts = detect_conflicts(
        observations_by_field
    )

    assert len(conflicts) == 2

    field_names = {
        conflict.field_name
        for conflict in conflicts
    }

    assert field_names == {
        "title",
        "salary",
    }


def test_detect_conflicts_returns_empty_list_when_no_conflicts():
    observations_by_field = {
        "title": [
            make_sourced_value(
                "Environmental Consultant",
                "https://source-a.example",
            ),
            make_sourced_value(
                "Environmental Consultant",
                "https://source-b.example",
            ),
        ],
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
            ),
            make_sourced_value(
                "Nigeria",
                "https://source-b.example",
            ),
        ],
    }

    conflicts = detect_conflicts(
        observations_by_field
    )

    assert conflicts == []


def test_empty_observation_list_has_no_conflict():
    result = detect_conflict(
        "value",
        [],
    )

    assert result is None


def test_unhashable_values_can_be_compared():
    observations = [
        make_sourced_value(
            {"value": 100},
            "https://source-a.example",
        ),
        make_sourced_value(
            {"value": 200},
            "https://source-b.example",
        ),
    ]

    result = detect_conflict(
        "measurement",
        observations,
    )

    assert result is not None
    assert result.is_conflict is True
    assert result.value_count == 2


def test_identical_unhashable_values_are_not_conflicts():
    observations = [
        make_sourced_value(
            {"value": 100},
            "https://source-a.example",
        ),
        make_sourced_value(
            {"value": 100},
            "https://source-b.example",
        ),
    ]

    result = detect_conflict(
        "measurement",
        observations,
    )

    assert result is None