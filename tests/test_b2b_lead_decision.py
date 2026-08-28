from backend.app.services.intelligence.b2b.lead_decision import (
    LeadDecision,
    decide_lead,
)

from backend.app.services.intelligence.b2b.lead_signals import (
    LeadSignal,
    LeadSignalType,
)


def make_signal(
    signal_id: str,
    signal_type: LeadSignalType,
    *,
    confidence: float = 0.90,
    strength: float = 0.85,
    evidence_ids: list[str] | None = None,
) -> LeadSignal:
    return LeadSignal(
        signal_id=signal_id,
        company_id="company-001",
        signal_type=signal_type,
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or ["evidence-001"],
    )


def test_decide_high_priority_lead():
    signals = [
        make_signal(
            "signal-001",
            LeadSignalType.BUYER_INTENT,
            confidence=0.95,
            strength=0.90,
        ),
        make_signal(
            "signal-002",
            LeadSignalType.EXPANSION,
            confidence=0.92,
            strength=0.88,
        ),
    ]

    decision = decide_lead(
        company_id="company-001",
        signals=signals,
        qualification_score=0.90,
    )

    assert isinstance(decision, LeadDecision)
    assert decision.company_id == "company-001"
    assert decision.priority == "high"
    assert decision.qualified is True
    assert decision.confidence > 0.80
    assert decision.recommended_action


def test_decide_medium_priority_lead():
    signal = make_signal(
        "signal-003",
        LeadSignalType.HIRING,
        confidence=0.80,
        strength=0.70,
    )

    decision = decide_lead(
        company_id="company-001",
        signals=[signal],
        qualification_score=0.70,
    )

    assert decision.qualified is True
    assert decision.priority == "medium"


def test_unqualified_lead_requires_no_action():
    signal = make_signal(
        "signal-004",
        LeadSignalType.EXPANSION,
        confidence=0.40,
        strength=0.30,
        evidence_ids=[],
    )

    decision = decide_lead(
        company_id="company-001",
        signals=[signal],
        qualification_score=0.20,
    )

    assert decision.qualified is False
    assert decision.priority == "low"
    assert decision.recommended_action == "monitor"


def test_decision_preserves_signal_evidence():
    signal = make_signal(
        "signal-005",
        LeadSignalType.BUYER_INTENT,
        evidence_ids=[
            "evidence-001",
            "evidence-002",
        ],
    )

    decision = decide_lead(
        company_id="company-001",
        signals=[signal],
        qualification_score=0.90,
    )

    assert "evidence-001" in decision.evidence_ids
    assert "evidence-002" in decision.evidence_ids


def test_decision_rejects_mixed_companies():
    signal_a = make_signal(
        "signal-006",
        LeadSignalType.BUYER_INTENT,
    )

    signal_b = LeadSignal(
        signal_id="signal-007",
        company_id="company-002",
        signal_type=LeadSignalType.EXPANSION,
        confidence=0.90,
        strength=0.85,
        evidence_ids=["evidence-002"],
    )

    import pytest

    with pytest.raises(ValueError):
        decide_lead(
            company_id="company-001",
            signals=[signal_a, signal_b],
            qualification_score=0.90,
        )
