import pytest

from backend.app.services.intelligence.leads.qualification import (
    LeadQualification,
    qualify_lead,
)
from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
    LeadSignalType,
)


def make_signal(
    signal_id: str,
    signal_type: LeadSignalType,
    *,
    confidence: float = 0.90,
    strength: float = 0.80,
    evidence_ids: list[str] | None = None,
) -> LeadSignal:
    return LeadSignal(
        signal_id=signal_id,
        signal_type=signal_type,
        company_id="company-001",
        confidence=confidence,
        strength=strength,
        evidence_ids=(
            ["evidence-001"]
            if evidence_ids is None
            else evidence_ids
        ),
    )


def test_qualify_supported_lead():
    signal = make_signal(
        "signal-001",
        LeadSignalType.HIRING,
    )

    result = qualify_lead([signal])

    assert isinstance(result, LeadQualification)
    assert result.company_id == "company-001"
    assert result.qualified is True
    assert result.score > 0.60


def test_unsupported_signal_does_not_qualify():
    signal = make_signal(
        "signal-002",
        LeadSignalType.EXPANSION,
        evidence_ids=[],
    )

    result = qualify_lead([signal])

    assert result.qualified is False
    assert result.score == 0.0
    assert "No supported lead signals" in result.reasons


def test_multiple_signals_receive_corroboration_bonus():
    signals = [
        make_signal(
            "signal-003",
            LeadSignalType.HIRING,
        ),
        make_signal(
            "signal-004",
            LeadSignalType.PROCUREMENT,
        ),
    ]

    single = qualify_lead([signals[0]])
    multiple = qualify_lead(signals)

    assert multiple.score > single.score
    assert any(
        "corroborate" in reason
        for reason in multiple.reasons
    )


def test_low_quality_signal_does_not_qualify():
    signal = make_signal(
        "signal-005",
        LeadSignalType.GROWTH,
        confidence=0.30,
        strength=0.20,
    )

    result = qualify_lead([signal])

    assert result.qualified is False
    assert result.score < 0.60


def test_signals_must_belong_to_same_company():
    first = make_signal(
        "signal-006",
        LeadSignalType.HIRING,
    )

    second = LeadSignal(
        signal_id="signal-007",
        signal_type=LeadSignalType.FUNDING,
        company_id="company-002",
        confidence=0.90,
        strength=0.80,
        evidence_ids=["evidence-002"],
    )

    with pytest.raises(ValueError):
        qualify_lead([first, second])


def test_empty_signal_list_is_rejected():
    with pytest.raises(ValueError):
        qualify_lead([])
