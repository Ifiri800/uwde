from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.domain.evidence import Evidence


def test_evidence_requires_source_url():
    with pytest.raises(Exception):
        Evidence(
            evidence_id="evidence-001",
            source_url="not-a-url",
            observed_value="Example",
        )


def test_evidence_validates_confidence():
    with pytest.raises(Exception):
        Evidence(
            evidence_id="evidence-001",
            source_url="https://example.com",
            observed_value="Example",
            confidence=1.5,
        )


def test_evidence_creates_valid_record():
    evidence = Evidence(
        evidence_id="evidence-001",
        source_url="https://example.com/company",
        source_id="page-001",
        entity_id="company-001",
        field_name="employee_count",
        observed_value=250,
        extraction_method="structured_extraction",
        observed_at=datetime.now(timezone.utc),
        confidence=0.94,
        lineage_reference="lineage-001",
    )

    assert evidence.evidence_id == "evidence-001"
    assert evidence.entity_id == "company-001"
    assert evidence.observed_value == 250
    assert evidence.confidence == 0.94
    assert evidence.has_lineage is True
    assert evidence.source == "https://example.com/company"


def test_evidence_defaults_metadata():
    evidence = Evidence(
        evidence_id="evidence-002",
        source_url="https://example.com/product",
        observed_value={"price": 1250},
    )

    assert evidence.metadata == {}
    assert evidence.confidence == 1.0
    assert evidence.has_lineage is False
