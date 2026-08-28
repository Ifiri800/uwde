import pytest

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.scoring.scorer import (
    SignalScorer,
    score_signal,
)


def make_signal(
    *,
    confidence: float = 0.90,
    strength: float = 0.80,
    evidence_ids: list[str] | None = None,
) -> Signal:
    return Signal(
        signal_id="signal-001",
        signal_type=SignalType.BUYER_INTENT,
        entity_id="company-001",
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or [],
    )


def make_evidence(
    evidence_id: str,
    confidence: float = 0.90,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_url="https://example.com/source",
        entity_id="company-001",
        field_name="intent",
        observed_value="procurement activity",
        confidence=confidence,
    )


def test_score_signal_without_evidence():
    result = score_signal(
        make_signal()
    )

    assert result.score > 0.0
    assert result.evidence_component == 0.0
    assert result.corroboration_component == 0.0


def test_high_quality_evidence_increases_score():
    signal = make_signal(
        evidence_ids=["evidence-001"]
    )

    without_evidence = score_signal(signal)

    with_evidence = score_signal(
        signal,
        [
            make_evidence(
                "evidence-001",
                confidence=0.95,
            )
        ],
    )

    assert with_evidence.score > without_evidence.score
    assert with_evidence.evidence_component == 0.95


def test_multiple_evidence_records_create_corroboration():
    signal = make_signal(
        evidence_ids=[
            "evidence-001",
            "evidence-002",
        ]
    )

    result = score_signal(
        signal,
        [
            make_evidence("evidence-001"),
            make_evidence("evidence-002"),
        ],
    )

    assert result.corroboration_component == 1.0


def test_unrelated_evidence_does_not_corroborate_signal():
    signal = make_signal(
        evidence_ids=["evidence-001"]
    )

    result = score_signal(
        signal,
        [
            make_evidence("evidence-999")
        ],
    )

    assert result.corroboration_component == 0.0


def test_score_is_bounded():
    result = score_signal(
        make_signal(
            confidence=1.0,
            strength=1.0,
            evidence_ids=[
                "evidence-001",
                "evidence-002",
            ],
        ),
        [
            make_evidence("evidence-001", 1.0),
            make_evidence("evidence-002", 1.0),
        ],
    )

    assert result.score == 1.0


def test_scorer_rejects_invalid_signal():
    with pytest.raises(TypeError):
        SignalScorer().score("not-a-signal")
