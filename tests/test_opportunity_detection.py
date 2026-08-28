import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.opportunity.detection import (
    OpportunityDetectionEngine,
    OpportunityDetectionType,
    detect_opportunities,
)


def make_signal(
    signal_id: str,
    signal_type: SignalType,
    *,
    company_id: str = "company-001",
    confidence: float = 0.90,
    strength: float = 0.80,
    evidence_ids: list[str] | None = None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=company_id,
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or ["evidence-001"],
    )


def test_buyer_intent_creates_buyer_intent_opportunity():
    signal = make_signal(
        "signal-001",
        SignalType.BUYER_INTENT,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert len(result.opportunities) == 1
    opportunity = result.opportunities[0]

    assert opportunity.company_id == "company-001"
    assert opportunity.opportunity_type == (
        OpportunityDetectionType.BUYER_INTENT
    )
    assert opportunity.confidence == 0.90
    assert opportunity.strength == 0.80


def test_procurement_signal_creates_procurement_opportunity():
    signal = make_signal(
        "signal-002",
        SignalType.PROCUREMENT_SIGNAL,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.PROCUREMENT
    )


def test_expansion_signal_creates_expansion_opportunity():
    signal = make_signal(
        "signal-003",
        SignalType.COMPANY_EXPANSION,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.EXPANSION
    )


def test_hiring_signal_creates_service_demand_opportunity():
    signal = make_signal(
        "signal-004",
        SignalType.HIRING_SIGNAL,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.SERVICE_DEMAND
    )


def test_funding_and_market_growth_create_growth_opportunity():
    signals = [
        make_signal(
            "signal-005",
            SignalType.FUNDING_SIGNAL,
        ),
        make_signal(
            "signal-006",
            SignalType.MARKET_GROWTH,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert len(result.opportunities) == 1
    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.GROWTH
    )

    assert result.opportunities[0].signal_ids == (
        "signal-005",
        "signal-006",
    )


def test_technology_adoption_creates_technology_opportunity():
    signal = make_signal(
        "signal-007",
        SignalType.TECHNOLOGY_ADOPTION,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.TECHNOLOGY
    )


def test_product_signals_create_project_opportunity():
    signals = [
        make_signal(
            "signal-008",
            SignalType.NEW_PRODUCT,
        ),
        make_signal(
            "signal-009",
            SignalType.PRODUCT_LAUNCH,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert len(result.opportunities) == 1
    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.PROJECT
    )

    assert result.opportunities[0].signal_ids == (
        "signal-008",
        "signal-009",
    )


def test_competitor_change_creates_competitive_opportunity():
    signal = make_signal(
        "signal-010",
        SignalType.COMPETITOR_CHANGE,
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.COMPETITIVE
    )


def test_irrelevant_signals_are_excluded():
    signals = [
        make_signal(
            "signal-011",
            SignalType.NEW_COMPANY,
        ),
        make_signal(
            "signal-012",
            SignalType.PRICE_CHANGE,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert result.opportunities == ()
    assert result.signals_evaluated == 2


def test_signals_for_other_companies_are_excluded():
    signals = [
        make_signal(
            "signal-014",
            SignalType.BUYER_INTENT,
            company_id="company-001",
        ),
        make_signal(
            "signal-015",
            SignalType.PROCUREMENT_SIGNAL,
            company_id="company-002",
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert len(result.opportunities) == 1
    assert result.opportunities[0].company_id == "company-001"
    assert result.opportunities[0].opportunity_type == (
        OpportunityDetectionType.BUYER_INTENT
    )


def test_multiple_opportunity_types_are_sorted_deterministically():
    signals = [
        make_signal(
            "signal-016",
            SignalType.BUYER_INTENT,
            confidence=0.80,
            strength=0.60,
        ),
        make_signal(
            "signal-017",
            SignalType.PROCUREMENT_SIGNAL,
            confidence=0.95,
            strength=0.95,
        ),
        make_signal(
            "signal-018",
            SignalType.TECHNOLOGY_ADOPTION,
            confidence=0.90,
            strength=0.75,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert [
        opportunity.opportunity_type
        for opportunity in result.opportunities
    ] == [
        OpportunityDetectionType.PROCUREMENT,
        OpportunityDetectionType.TECHNOLOGY,
        OpportunityDetectionType.BUYER_INTENT,
    ]


def test_evidence_ids_are_deduplicated_and_preserved():
    signals = [
        make_signal(
            "signal-019",
            SignalType.FUNDING_SIGNAL,
            evidence_ids=[
                "evidence-001",
                "evidence-002",
            ],
        ),
        make_signal(
            "signal-020",
            SignalType.MARKET_GROWTH,
            evidence_ids=[
                "evidence-002",
                "evidence-003",
            ],
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert result.opportunities[0].evidence_ids == (
        "evidence-001",
        "evidence-002",
        "evidence-003",
    )


def test_highest_confidence_and_strength_are_used():
    signals = [
        make_signal(
            "signal-021",
            SignalType.BUYER_INTENT,
            confidence=0.70,
            strength=0.50,
        ),
        make_signal(
            "signal-022",
            SignalType.BUYER_INTENT,
            confidence=0.98,
            strength=0.91,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    opportunity = result.opportunities[0]

    assert opportunity.confidence == 0.98
    assert opportunity.strength == 0.91


def test_signals_evaluated_counts_all_input_signals():
    signals = [
        make_signal(
            "signal-023",
            SignalType.BUYER_INTENT,
        ),
        make_signal(
            "signal-024",
            SignalType.NEW_COMPANY,
        ),
        make_signal(
            "signal-025",
            SignalType.PRICE_CHANGE,
        ),
    ]

    result = detect_opportunities(
        "company-001",
        signals,
    )

    assert result.signals_evaluated == 3


def test_invalid_company_id_is_rejected():
    engine = OpportunityDetectionEngine()

    with pytest.raises(ValueError):
        engine.detect(
            "   ",
            [],
        )


def test_invalid_company_id_type_is_rejected():
    engine = OpportunityDetectionEngine()

    with pytest.raises(TypeError):
        engine.detect(
            123,
            [],
        )


def test_invalid_signals_argument_is_rejected():
    engine = OpportunityDetectionEngine()

    with pytest.raises(TypeError):
        engine.detect(
            "company-001",
            "not-a-list",
        )


def test_invalid_signal_items_are_rejected():
    engine = OpportunityDetectionEngine()

    with pytest.raises(TypeError):
        engine.detect(
            "company-001",
            ["not-a-signal"],
        )


def test_to_dict_is_explainable():
    signal = make_signal(
        "signal-026",
        SignalType.BUYER_INTENT,
        evidence_ids=["evidence-026"],
    )

    result = detect_opportunities(
        "company-001",
        [signal],
    )

    payload = result.to_dict()

    assert payload["company_id"] == "company-001"
    assert payload["signals_evaluated"] == 1
    assert len(payload["opportunities"]) == 1

    opportunity = payload["opportunities"][0]

    assert opportunity["opportunity_type"] == "buyer_intent"
    assert opportunity["signal_ids"] == ["signal-026"]
    assert opportunity["evidence_ids"] == ["evidence-026"]
    assert opportunity["confidence"] == 0.90
    assert opportunity["strength"] == 0.80
    assert opportunity["reasons"] == [
        "buyer_intent signal detected"
    ]

