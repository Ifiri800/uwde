import pytest

from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
    LeadSignalType,
)


def test_lead_signal_creates_valid_record():
    signal = LeadSignal(
        signal_id="lead-signal-001",
        signal_type=LeadSignalType.HIRING,
        company_id="company-001",
        confidence=0.92,
        strength=0.85,
        evidence_ids=["evidence-001"],
    )

    assert signal.signal_id == "lead-signal-001"
    assert signal.signal_type == LeadSignalType.HIRING
    assert signal.company_id == "company-001"
    assert signal.confidence == 0.92
    assert signal.strength == 0.85
    assert signal.is_supported is True


def test_lead_signal_without_evidence_is_not_supported():
    signal = LeadSignal(
        signal_id="lead-signal-002",
        signal_type=LeadSignalType.EXPANSION,
        company_id="company-002",
        confidence=0.90,
        strength=0.80,
    )

    assert signal.is_supported is False


def test_lead_signal_commercial_strength():
    signal = LeadSignal(
        signal_id="lead-signal-003",
        signal_type=LeadSignalType.PROCUREMENT,
        company_id="company-003",
        confidence=0.90,
        strength=0.80,
        evidence_ids=["evidence-003"],
    )

    assert signal.commercial_strength == 0.85


def test_lead_signal_rejects_invalid_confidence():
    with pytest.raises(ValueError):
        LeadSignal(
            signal_id="lead-signal-004",
            signal_type=LeadSignalType.FUNDING,
            company_id="company-004",
            confidence=1.5,
        )


def test_lead_signal_rejects_invalid_strength():
    with pytest.raises(ValueError):
        LeadSignal(
            signal_id="lead-signal-005",
            signal_type=LeadSignalType.GROWTH,
            company_id="company-005",
            strength=-0.1,
        )


def test_lead_signal_requires_company():
    with pytest.raises(ValueError):
        LeadSignal(
            signal_id="lead-signal-006",
            signal_type=LeadSignalType.HIRING,
            company_id="",
        )
