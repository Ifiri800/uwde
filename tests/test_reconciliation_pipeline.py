from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.reconciliation.pipeline import (
    ReconciliationResult,
    reconcile,
    reconcile_records,
)
from backend.app.services.reconciliation.provenance import (
    SourcedValue,
    create_provenance,
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


def test_reconcile_non_conflicting_fields():
    observations = {
        "title": [
            make_sourced_value(
                "Environmental Consultant",
                "https://source-a.example",
                confidence=0.90,
            ),
        ],
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
                confidence=0.95,
            ),
        ],
    }

    result = reconcile(observations)

    assert isinstance(result, ReconciliationResult)
    assert result.values["title"] == "Environmental Consultant"
    assert result.values["country"] == "Nigeria"
    assert result.conflict_count == 0
    assert result.resolved_count == 0
    assert result.unresolved_count == 0
    assert result.requires_review is False


def test_reconcile_detects_and_resolves_conflict():
    observations = {
        "salary": [
            make_sourced_value(
                100000,
                "https://source-a.example",
                confidence=0.70,
            ),
            make_sourced_value(
                125000,
                "https://source-b.example",
                confidence=0.95,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="highest_confidence",
    )

    assert result.conflict_count == 1
    assert result.resolved_count == 1
    assert result.values["salary"] == 125000
    assert result.requires_review is True


def test_reconcile_preserves_conflict_information():
    observations = {
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
                confidence=0.80,
            ),
            make_sourced_value(
                "Ghana",
                "https://source-b.example",
                confidence=0.90,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="highest_confidence",
    )

    assert len(result.conflicts) == 1

    conflict = result.conflicts[0]

    assert conflict.field_name == "country"
    assert conflict.values == ("Nigeria", "Ghana")
    assert len(conflict.observations) == 2


def test_reconcile_calculates_uncertainty_for_conflict():
    observations = {
        "concentration": [
            make_sourced_value(
                420,
                "https://source-a.example",
                confidence=0.80,
            ),
            make_sourced_value(
                418,
                "https://source-b.example",
                confidence=0.90,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="highest_confidence",
    )

    uncertainty = result.uncertainties[
        "concentration"
    ]

    assert uncertainty.confidence == pytest.approx(0.90)
    assert uncertainty.uncertainty == pytest.approx(0.10)
    assert uncertainty.supporting_sources == 1
    assert uncertainty.conflicting_sources == 1
    assert uncertainty.requires_review is True


def test_reconcile_majority_strategy():
    observations = {
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
                confidence=0.60,
            ),
            make_sourced_value(
                "Nigeria",
                "https://source-b.example",
                confidence=0.70,
            ),
            make_sourced_value(
                "Ghana",
                "https://source-c.example",
                confidence=0.95,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="majority",
    )

    assert result.values["country"] == "Nigeria"


def test_reconcile_weighted_strategy():
    observations = {
        "value": [
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
        ],
    }

    result = reconcile(
        observations,
        strategy="weighted",
    )

    assert result.values["value"] == "A"


def test_reconcile_latest_strategy():
    now = datetime.now(timezone.utc)

    observations = {
        "value": [
            make_sourced_value(
                "old",
                "https://source-a.example",
                confidence=0.95,
                extracted_at=now - timedelta(hours=2),
            ),
            make_sourced_value(
                "new",
                "https://source-b.example",
                confidence=0.60,
                extracted_at=now,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="latest",
    )

    assert result.values["value"] == "new"


def test_reconcile_manual_strategy_requires_review():
    observations = {
        "value": [
            make_sourced_value(
                "A",
                "https://source-a.example",
                confidence=0.90,
            ),
            make_sourced_value(
                "B",
                "https://source-b.example",
                confidence=0.80,
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="manual",
    )

    assert "value" not in result.values
    assert result.conflict_count == 1
    assert result.resolved_count == 0
    assert result.unresolved_count == 1
    assert result.requires_review is True


def test_reconcile_none_strategy_preserves_conflict():
    observations = {
        "value": [
            make_sourced_value(
                "A",
                "https://source-a.example",
            ),
            make_sourced_value(
                "B",
                "https://source-b.example",
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="none",
    )

    assert "value" not in result.values
    assert result.conflict_count == 1
    assert result.resolved_count == 0
    assert result.unresolved_count == 0
    assert result.requires_review is True


def test_reconcile_multiple_fields_independently():
    observations = {
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
        "salary": [
            make_sourced_value(
                100000,
                "https://source-a.example",
                confidence=0.60,
            ),
            make_sourced_value(
                125000,
                "https://source-b.example",
                confidence=0.90,
            ),
        ],
        "country": [
            make_sourced_value(
                "Nigeria",
                "https://source-a.example",
            ),
        ],
    }

    result = reconcile(
        observations,
        strategy="highest_confidence",
    )

    assert result.values["title"] == (
        "Environmental Consultant"
    )
    assert result.values["salary"] == 125000
    assert result.values["country"] == "Nigeria"

    assert result.conflict_count == 1
    assert result.resolved_count == 1
    assert result.requires_review is True


def test_reconcile_empty_input():
    result = reconcile({})

    assert result.values == {}
    assert result.conflicts == []
    assert result.resolutions == []
    assert result.uncertainties == {}
    assert result.conflict_count == 0
    assert result.resolved_count == 0
    assert result.unresolved_count == 0
    assert result.requires_review is False


def test_reconcile_records_processes_each_record_independently():
    records = [
        {
            "country": [
                make_sourced_value(
                    "Nigeria",
                    "https://source-a.example",
                ),
            ],
        },
        {
            "country": [
                make_sourced_value(
                    "Ghana",
                    "https://source-b.example",
                ),
            ],
        },
    ]

    results = reconcile_records(records)

    assert len(results) == 2
    assert results[0].values["country"] == "Nigeria"
    assert results[1].values["country"] == "Ghana"


def test_reconcile_records_preserves_individual_conflicts():
    records = [
        {
            "value": [
                make_sourced_value(
                    100,
                    "https://source-a.example",
                ),
                make_sourced_value(
                    200,
                    "https://source-b.example",
                    confidence=0.90,
                ),
            ],
        },
        {
            "value": [
                make_sourced_value(
                    300,
                    "https://source-c.example",
                ),
            ],
        },
    ]

    results = reconcile_records(
        records,
        strategy="highest_confidence",
    )

    assert len(results) == 2

    assert results[0].conflict_count == 1
    assert results[0].values["value"] == 200

    assert results[1].conflict_count == 0
    assert results[1].values["value"] == 300


def test_reconcile_raises_for_unsupported_strategy():
    observations = {
        "value": [
            make_sourced_value(
                "A",
                "https://source-a.example",
            ),
            make_sourced_value(
                "B",
                "https://source-b.example",
            ),
        ],
    }

    with pytest.raises(ValueError):
        reconcile(
            observations,
            strategy="unsupported",
        )