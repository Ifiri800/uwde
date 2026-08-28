from backend.app.services.intelligence.detection.engine import (
    SignalDetectionEngine,
    detect_signals,
)
from backend.app.services.intelligence.domain.signals import (
    SignalType,
)


def test_detect_product_price_change():
    signals = detect_signals(
        entity_id="product-001",
        entity_type="product",
        field_name="price",
        previous_value=1000,
        current_value=1200,
        evidence_ids=["evidence-001"],
    )

    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.PRICE_CHANGE
    assert signals[0].previous_value == 1000
    assert signals[0].current_value == 1200
    assert signals[0].is_supported is True


def test_no_signal_when_value_is_unchanged():
    signals = detect_signals(
        entity_id="product-001",
        entity_type="product",
        field_name="price",
        previous_value=1000,
        current_value=1000,
    )

    assert signals == []


def test_detect_new_product():
    signals = detect_signals(
        entity_id="product-002",
        entity_type="product",
        field_name="existence",
        previous_value=None,
        current_value=True,
    )

    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.NEW_PRODUCT


def test_detect_new_company():
    signals = detect_signals(
        entity_id="company-001",
        entity_type="company",
        field_name="existence",
        previous_value=None,
        current_value=True,
    )

    assert len(signals) == 1
    assert signals[0].signal_type == SignalType.NEW_COMPANY


def test_product_appearance_does_not_create_company_signal():
    signals = detect_signals(
        entity_id="product-003",
        entity_type="product",
        field_name="existence",
        previous_value=None,
        current_value=True,
    )

    signal_types = {
        signal.signal_type
        for signal in signals
    }

    assert SignalType.NEW_PRODUCT in signal_types
    assert SignalType.NEW_COMPANY not in signal_types


def test_company_appearance_does_not_create_product_signal():
    signals = detect_signals(
        entity_id="company-002",
        entity_type="company",
        field_name="existence",
        previous_value=None,
        current_value=True,
    )

    signal_types = {
        signal.signal_type
        for signal in signals
    }

    assert SignalType.NEW_COMPANY in signal_types
    assert SignalType.NEW_PRODUCT not in signal_types


def test_price_change_only_applies_to_price_field():
    signals = detect_signals(
        entity_id="product-004",
        entity_type="product",
        field_name="description",
        previous_value="Old description",
        current_value="New description",
    )

    assert signals == []


def test_detection_preserves_evidence():
    engine = SignalDetectionEngine()

    signals = engine.detect(
        entity_id="product-005",
        entity_type="product",
        field_name="price",
        previous_value=100,
        current_value=125,
        evidence_ids=[
            "evidence-001",
            "evidence-002",
        ],
    )

    assert signals[0].evidence_ids == [
        "evidence-001",
        "evidence-002",
    ]
