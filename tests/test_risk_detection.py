import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.risk.detection import (
    RiskDetectionType,
    detect_risks,
)


def make_signal(
    signal_id,
    signal_type,
    *,
    company_id="company-001",
    confidence=0.90,
    strength=0.80,
    evidence_ids=None,
):
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=company_id,
        confidence=confidence,
        strength=strength,
        evidence_ids=(
            evidence_ids
            if evidence_ids is not None
            else ["evidence-001"]
        ),
    )


def test_competitor_change_creates_competitive_risk():
    signal = make_signal(
        "signal-001",
        SignalType.COMPETITOR_CHANGE,
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    assert len(result.risks) == 1
    assert result.risks[0].risk_type == (
        RiskDetectionType.COMPETITIVE
    )


def test_price_change_creates_pricing_risk():
    signal = make_signal(
        "signal-002",
        SignalType.PRICE_CHANGE,
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    assert result.risks[0].risk_type == (
        RiskDetectionType.PRICING
    )


def test_product_signals_create_product_risk():
    signals = [
        make_signal(
            "signal-003",
            SignalType.NEW_PRODUCT,
        ),
        make_signal(
            "signal-004",
            SignalType.PRODUCT_LAUNCH,
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert len(result.risks) == 1
    assert result.risks[0].risk_type == (
        RiskDetectionType.PRODUCT
    )


def test_market_growth_creates_market_risk():
    signal = make_signal(
        "signal-005",
        SignalType.MARKET_GROWTH,
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    assert result.risks[0].risk_type == (
        RiskDetectionType.MARKET
    )


def test_technology_adoption_creates_technology_risk():
    signal = make_signal(
        "signal-006",
        SignalType.TECHNOLOGY_ADOPTION,
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    assert result.risks[0].risk_type == (
        RiskDetectionType.TECHNOLOGY
    )


def test_company_expansion_creates_growth_risk():
    signal = make_signal(
        "signal-007",
        SignalType.COMPANY_EXPANSION,
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    assert result.risks[0].risk_type == (
        RiskDetectionType.GROWTH
    )


def test_irrelevant_signals_are_excluded():
    signals = [
        make_signal(
            "signal-008",
            SignalType.BUYER_INTENT,
        ),
        make_signal(
            "signal-009",
            SignalType.PROCUREMENT_SIGNAL,
        ),
        make_signal(
            "signal-010",
            SignalType.TENDER_OPPORTUNITY,
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert result.risks == ()


def test_signals_for_other_companies_are_excluded():
    signals = [
        make_signal(
            "signal-011",
            SignalType.PRICE_CHANGE,
            company_id="company-002",
        ),
        make_signal(
            "signal-012",
            SignalType.COMPETITOR_CHANGE,
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert len(result.risks) == 1
    assert result.risks[0].risk_type == (
        RiskDetectionType.COMPETITIVE
    )


def test_multiple_risk_types_are_sorted_deterministically():
    signals = [
        make_signal(
            "signal-013",
            SignalType.PRICE_CHANGE,
            confidence=0.70,
            strength=0.60,
        ),
        make_signal(
            "signal-014",
            SignalType.COMPETITOR_CHANGE,
            confidence=0.95,
            strength=0.95,
        ),
        make_signal(
            "signal-015",
            SignalType.TECHNOLOGY_ADOPTION,
            confidence=0.85,
            strength=0.80,
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert [
        risk.risk_type
        for risk in result.risks
    ] == [
        RiskDetectionType.COMPETITIVE,
        RiskDetectionType.TECHNOLOGY,
        RiskDetectionType.PRICING,
    ]


def test_evidence_ids_are_deduplicated_and_preserved():
    signals = [
        make_signal(
            "signal-016",
            SignalType.PRICE_CHANGE,
            evidence_ids=[
                "evidence-001",
                "evidence-002",
            ],
        ),
        make_signal(
            "signal-017",
            SignalType.PRICE_CHANGE,
            evidence_ids=[
                "evidence-002",
                "evidence-003",
            ],
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert result.risks[0].evidence_ids == (
        "evidence-001",
        "evidence-002",
        "evidence-003",
    )


def test_highest_confidence_and_strength_are_used():
    signals = [
        make_signal(
            "signal-018",
            SignalType.PRICE_CHANGE,
            confidence=0.60,
            strength=0.50,
        ),
        make_signal(
            "signal-019",
            SignalType.PRICE_CHANGE,
            confidence=0.98,
            strength=0.91,
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    risk = result.risks[0]

    assert risk.confidence == 0.98
    assert risk.strength == 0.91


def test_signals_evaluated_counts_all_input_signals():
    signals = [
        make_signal(
            "signal-020",
            SignalType.PRICE_CHANGE,
        ),
        make_signal(
            "signal-021",
            SignalType.BUYER_INTENT,
        ),
        make_signal(
            "signal-022",
            SignalType.COMPETITOR_CHANGE,
            company_id="company-002",
        ),
    ]

    result = detect_risks(
        "company-001",
        signals,
    )

    assert result.signals_evaluated == 3


def test_invalid_company_id_is_rejected():
    with pytest.raises(ValueError):
        detect_risks(
            "",
            [],
        )


def test_invalid_company_id_type_is_rejected():
    with pytest.raises(TypeError):
        detect_risks(
            123,
            [],
        )


def test_invalid_signals_argument_is_rejected():
    with pytest.raises(TypeError):
        detect_risks(
            "company-001",
            None,
        )


def test_invalid_signal_items_are_rejected():
    with pytest.raises(TypeError):
        detect_risks(
            "company-001",
            ["not-a-signal"],
        )


def test_to_dict_is_explainable():
    signal = make_signal(
        "signal-023",
        SignalType.COMPETITOR_CHANGE,
        evidence_ids=[
            "evidence-001",
            "evidence-002",
        ],
    )

    result = detect_risks(
        "company-001",
        [signal],
    )

    data = result.to_dict()

    assert data["company_id"] == "company-001"
    assert data["signals_evaluated"] == 1
    assert len(data["risks"]) == 1

    risk = data["risks"][0]

    assert risk["risk_type"] == (
        RiskDetectionType.COMPETITIVE
    )
    assert risk["signal_ids"] == ["signal-023"]
    assert risk["evidence_ids"] == [
        "evidence-001",
        "evidence-002",
    ]
    assert risk["confidence"] == 0.90
    assert risk["strength"] == 0.80
    assert risk["reasons"]
