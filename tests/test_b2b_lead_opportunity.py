import pytest

from backend.app.services.intelligence.leads.opportunity import (
    LeadOpportunityType,
    create_lead_opportunity,
)
from backend.app.services.intelligence.leads.qualification import (
    LeadQualification,
)
from backend.app.services.intelligence.leads.scoring import (
    LeadScore,
)
from backend.app.services.intelligence.leads.signals import (
    LeadSignal,
    LeadSignalType,
)


def make_signal(
    signal_id,
    signal_type,
    *,
    confidence=0.90,
    strength=0.80,
    evidence_ids=None,
):
    return LeadSignal(
        signal_id=signal_id,
        signal_type=signal_type,
        company_id="company-001",
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or ["evidence-001"],
    )


def make_qualification(score=0.85):
    return LeadQualification(
        company_id="company-001",
        qualified=True,
        score=score,
        reasons=["Lead meets the commercial qualification threshold"],
    )


def make_score(score=0.85, priority="high"):
    return LeadScore(
        company_id="company-001",
        score=score,
        priority=priority,
        signal_score=0.90,
        qualification_score=0.85,
        diversity_score=0.33,
    )


def test_qualified_procurement_lead_creates_procurement_opportunity():
    signal = make_signal(
        "signal-001",
        LeadSignalType.PROCUREMENT,
    )

    opportunity = create_lead_opportunity(
        qualification=make_qualification(),
        lead_score=make_score(),
        signals=[signal],
    )

    assert opportunity.company_id == "company-001"
    assert opportunity.opportunity_type == LeadOpportunityType.PROCUREMENT_OPPORTUNITY
    assert opportunity.priority == "high"
    assert opportunity.score == 0.85


def test_expansion_signal_creates_expansion_opportunity():
    signal = make_signal(
        "signal-002",
        LeadSignalType.EXPANSION,
    )

    opportunity = create_lead_opportunity(
        qualification=make_qualification(),
        lead_score=make_score(),
        signals=[signal],
    )

    assert opportunity.opportunity_type == LeadOpportunityType.EXPANSION_OPPORTUNITY


def test_strongest_signal_determines_primary_opportunity():
    weak_signal = make_signal(
        "signal-003",
        LeadSignalType.HIRING,
        confidence=0.70,
        strength=0.60,
    )

    strong_signal = make_signal(
        "signal-004",
        LeadSignalType.PROCUREMENT,
        confidence=0.98,
        strength=0.95,
    )

    opportunity = create_lead_opportunity(
        qualification=make_qualification(),
        lead_score=make_score(),
        signals=[
            weak_signal,
            strong_signal,
        ],
    )

    assert opportunity.opportunity_type == LeadOpportunityType.PROCUREMENT_OPPORTUNITY


def test_opportunity_preserves_evidence_ids():
    signal = make_signal(
        "signal-005",
        LeadSignalType.FUNDING,
        evidence_ids=[
            "evidence-001",
            "evidence-002",
        ],
    )

    opportunity = create_lead_opportunity(
        qualification=make_qualification(),
        lead_score=make_score(),
        signals=[signal],
    )

    assert opportunity.evidence_ids == [
        "evidence-001",
        "evidence-002",
    ]


def test_unsupported_signals_do_not_create_opportunity():
    signal = make_signal(
        "signal-006",
        LeadSignalType.GROWTH,
        evidence_ids=[],
    )

    qualification = LeadQualification(
        company_id="company-001",
        qualified=False,
        score=0.0,
        reasons=["No supported lead signals"],
    )

    with pytest.raises(ValueError):
        create_lead_opportunity(
            qualification=qualification,
            lead_score=make_score(score=0.0, priority="low"),
            signals=[signal],
        )


def test_mixed_company_signals_are_rejected():
    signal_one = make_signal(
        "signal-007",
        LeadSignalType.PROCUREMENT,
    )

    signal_two = LeadSignal(
        signal_id="signal-008",
        signal_type=LeadSignalType.EXPANSION,
        company_id="company-002",
        confidence=0.90,
        strength=0.80,
        evidence_ids=["evidence-002"],
    )

    with pytest.raises(ValueError):
        create_lead_opportunity(
            qualification=make_qualification(),
            lead_score=make_score(),
            signals=[
                signal_one,
                signal_two,
            ],
        )
