from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalStatus,
    SignalType,
)
from backend.app.services.intelligence.market.validation import (
    MarketSignalValidator,
    SignalValidationResult,
    validate_market_signal,
    validate_market_signals,
)


def make_signal(
    signal_id: str = "signal-1",
    *,
    confidence: float = 0.8,
    strength: float = 0.7,
    evidence_ids: list[str] | None = None,
    status: SignalStatus = SignalStatus.DETECTED,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=SignalType.MARKET_GROWTH,
        entity_id="market-1",
        detected_at=datetime.now(timezone.utc),
        confidence=confidence,
        strength=strength,
        evidence_ids=["e1"] if evidence_ids is None else evidence_ids,
        status=status,
    )


def make_evidence(
    evidence_id: str = "e1",
    *,
    confidence: float = 0.9,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_url="https://example.com/source",
        entity_id="market-1",
        observed_value={"value": True},
        confidence=confidence,
    )


def test_valid_signal_passes_validation():
    result = validate_market_signal(
        make_signal(),
        [make_evidence()],
    )

    assert result.is_valid is True
    assert result.signal_id == "signal-1"
    assert "signal passed all validation checks" in result.reasons


def test_validation_returns_score():
    result = validate_market_signal(
        make_signal(),
        [make_evidence()],
    )

    assert result.score is not None
    assert 0.0 <= result.score.score <= 1.0


def test_missing_evidence_ids_invalidates_signal():
    signal = make_signal(evidence_ids=[])

    result = validate_market_signal(signal)

    assert result.is_valid is False
    assert "signal has no supporting evidence IDs" in result.reasons


def test_unmatched_evidence_invalidates_signal():
    result = validate_market_signal(
        make_signal(evidence_ids=["missing"]),
        [make_evidence("e1")],
    )

    assert result.is_valid is False
    assert (
        "signal evidence IDs do not match supplied evidence"
        in result.reasons
    )


def test_low_confidence_invalidates_signal():
    result = validate_market_signal(
        make_signal(confidence=0.49),
        [make_evidence()],
    )

    assert result.is_valid is False
    assert "confidence is below 0.50" in result.reasons


def test_low_strength_invalidates_signal():
    result = validate_market_signal(
        make_signal(strength=0.29),
        [make_evidence()],
    )

    assert result.is_valid is False
    assert "strength is below 0.30" in result.reasons


def test_dismissed_signal_invalid():
    result = validate_market_signal(
        make_signal(status=SignalStatus.DISMISSED),
        [make_evidence()],
    )

    assert result.is_valid is False
    assert "signal status is dismissed" in result.reasons


def test_expired_signal_invalid():
    result = validate_market_signal(
        make_signal(status=SignalStatus.EXPIRED),
        [make_evidence()],
    )

    assert result.is_valid is False
    assert "signal status is expired" in result.reasons


def test_validated_signal_can_pass():
    result = validate_market_signal(
        make_signal(status=SignalStatus.VALIDATED),
        [make_evidence()],
    )

    assert result.is_valid is True


def test_multiple_validation_failures_are_reported():
    result = validate_market_signal(
        make_signal(
            confidence=0.1,
            strength=0.1,
            evidence_ids=[],
            status=SignalStatus.DISMISSED,
        )
    )

    assert result.is_valid is False
    assert len(result.reasons) >= 4


def test_validate_many():
    signals = [
        make_signal("s1"),
        make_signal("s2"),
    ]

    results = validate_market_signals(
        signals,
        [make_evidence()],
    )

    assert len(results) == 2
    assert all(
        isinstance(result, SignalValidationResult)
        for result in results
    )


def test_validator_rejects_invalid_signal_type():
    with pytest.raises(TypeError, match="signal must be a Signal"):
        MarketSignalValidator().validate("invalid")  # type: ignore[arg-type]


def test_validator_rejects_invalid_evidence_list():
    with pytest.raises(TypeError, match="evidence must be a list"):
        MarketSignalValidator().validate(
            make_signal(),
            "not-a-list",  # type: ignore[arg-type]
        )


def test_to_dict():
    result = validate_market_signal(
        make_signal(),
        [make_evidence()],
    )

    data = result.to_dict()

    assert data["signal_id"] == "signal-1"
    assert data["is_valid"] is True
    assert isinstance(data["reasons"], list)
    assert data["score"]["score"] == result.score.score
