import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalStatus,
    SignalType,
)


def test_signal_creates_valid_record():
    signal = Signal(
        signal_id="signal-001",
        signal_type=SignalType.HIRING_SIGNAL,
        entity_id="company-001",
        confidence=0.92,
        strength=0.80,
        evidence_ids=["evidence-001"],
    )

    assert signal.signal_id == "signal-001"
    assert signal.signal_type == SignalType.HIRING_SIGNAL
    assert signal.entity_id == "company-001"
    assert signal.confidence == 0.92
    assert signal.strength == 0.80
    assert signal.is_supported is True


def test_signal_is_not_actionable_when_not_validated():
    signal = Signal(
        signal_id="signal-002",
        signal_type=SignalType.PRICE_CHANGE,
        entity_id="product-001",
        confidence=0.95,
        strength=0.90,
        evidence_ids=["evidence-002"],
    )

    assert signal.status == SignalStatus.DETECTED
    assert signal.is_actionable is False


def test_validated_signal_can_be_actionable():
    signal = Signal(
        signal_id="signal-003",
        signal_type=SignalType.BUYER_INTENT,
        entity_id="company-001",
        confidence=0.90,
        strength=0.85,
        evidence_ids=["evidence-003"],
        status=SignalStatus.VALIDATED,
    )

    assert signal.is_supported is True
    assert signal.is_actionable is True


def test_signal_without_evidence_is_not_supported():
    signal = Signal(
        signal_id="signal-004",
        signal_type=SignalType.MARKET_GROWTH,
        entity_id="market-001",
        confidence=0.90,
        strength=0.80,
    )

    assert signal.is_supported is False
    assert signal.is_actionable is False


def test_signal_validates_confidence():
    with pytest.raises(Exception):
        Signal(
            signal_id="signal-005",
            signal_type=SignalType.NEW_PRODUCT,
            entity_id="product-001",
            confidence=1.5,
        )


def test_signal_validates_strength():
    with pytest.raises(Exception):
        Signal(
            signal_id="signal-006",
            signal_type=SignalType.PRICE_CHANGE,
            entity_id="product-001",
            strength=-0.1,
        )

