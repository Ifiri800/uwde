import pytest

from backend.app.services.intelligence.leads.qualification import (
    qualify_lead,
)
from backend.app.services.intelligence.leads.scoring import (
    LeadScore,
    score_lead,
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


def test_score_qualified_lead():
    signal = make_signal(
        "signal-001",
        LeadSignalType.HIRING,
    )

    qualification = qualify_lead([signal])
    result = score_lead(
        qualification,
        [signal],
    )

    assert isinstance(result, LeadScore)
    assert result.company_id == "company-001"
    assert result.score > 0.0
    assert result.priority in {
        "low",
        "medium",
        "high",
    }


def test_high_quality_lead_gets_high_priority():
    signals = [
        make_signal(
            "signal-002",
            LeadSignalType.HIRING,
            confidence=1.0,
            strength=1.0,
        ),
        make_signal(
            "signal-003",
            LeadSignalType.PROCUREMENT,
            confidence=1.0,
            strength=1.0,
        ),
        make_signal(
            "signal-004",
            LeadSignalType.EXPANSION,
            confidence=1.0,
            strength=1.0,
        ),
    ]

    qualification = qualify_lead(signals)
    result = score_lead(
        qualification,
        signals,
    )

    assert result.score >= 0.80
    assert result.priority == "high"


def test_signal_diversity_increases_score():
    first = make_signal(
        "signal-005",
        LeadSignalType.HIRING,
    )

    second = make_signal(
        "signal-006",
        LeadSignalType.PROCUREMENT,
    )

    first_qualification = qualify_lead([first])
    multiple_qualification = qualify_lead(
        [first, second]
    )

    first_result = score_lead(
        first_qualification,
        [first],
    )

    multiple_result = score_lead(
        multiple_qualification,
        [first, second],
    )

    assert multiple_result.diversity_score > first_result.diversity_score
    assert multiple_result.score > first_result.score


def test_unsupported_signals_receive_zero_signal_score():
    signal = make_signal(
        "signal-007",
        LeadSignalType.GROWTH,
        evidence_ids=[],
    )

    qualification = qualify_lead([signal])
    result = score_lead(
        qualification,
        [signal],
    )

    assert result.score == 0.0
    assert result.signal_score == 0.0
    assert result.priority == "low"


def test_scoring_rejects_wrong_qualification_type():
    signal = make_signal(
        "signal-008",
        LeadSignalType.FUNDING,
    )

    with pytest.raises(TypeError):
        score_lead(
            "not-a-qualification",
            [signal],
        )


def test_scoring_rejects_mixed_companies():
    first = make_signal(
        "signal-009",
        LeadSignalType.HIRING,
    )

    second = LeadSignal(
        signal_id="signal-010",
        signal_type=LeadSignalType.FUNDING,
        company_id="company-002",
        confidence=0.90,
        strength=0.80,
        evidence_ids=["evidence-010"],
    )

    qualification = qualify_lead([first])

    with pytest.raises(ValueError):
        score_lead(
            qualification,
            [first, second],
        )
