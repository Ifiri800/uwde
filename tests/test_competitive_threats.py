from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningEngine,
)
from backend.app.services.intelligence.competitive.threats import (
    CompetitiveThreatEngine,
    ThreatDimension,
    ThreatLevel,
)
from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)


def make_company(entity_id: str) -> Company:
    return Company(
        entity_id=entity_id,
        name=entity_id,
        industry="technology",
        country="Nigeria",
        region="West Africa",
        city="Lagos",
    )


def make_signal(
    signal_id: str,
    entity_id: str,
    signal_type: SignalType,
    confidence: float = 0.90,
    strength: float = 0.90,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        confidence=confidence,
        strength=strength,
        detected_at=datetime.now(timezone.utc),
        evidence_ids=[],
    )


def test_product_activity_creates_product_threat():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    signal = make_signal(
        "signal-1",
        competitor.entity_id,
        SignalType.PRODUCT_LAUNCH,
    )

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        [signal],
    )

    result = CompetitiveThreatEngine().assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        [signal],
    )

    assert result.competitor_id == competitor.entity_id
    assert ThreatDimension.PRODUCT in result.dimensions
    assert result.threat_score > 0.0
    assert result.threat_level in ThreatLevel


def test_pricing_activity_creates_pricing_threat():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    signal = make_signal(
        "signal-1",
        competitor.entity_id,
        SignalType.PRICE_CHANGE,
    )

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        [signal],
    )

    result = CompetitiveThreatEngine().assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        [signal],
    )

    assert ThreatDimension.PRICING in result.dimensions
    assert "pricing activity detected" in result.reasons


def test_multiple_signal_types_create_multiple_threat_dimensions():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    signals = [
        make_signal(
            "signal-product",
            competitor.entity_id,
            SignalType.PRODUCT_LAUNCH,
        ),
        make_signal(
            "signal-price",
            competitor.entity_id,
            SignalType.PRICE_CHANGE,
        ),
        make_signal(
            "signal-tech",
            competitor.entity_id,
            SignalType.TECHNOLOGY_ADOPTION,
        ),
        make_signal(
            "signal-funding",
            competitor.entity_id,
            SignalType.FUNDING_SIGNAL,
        ),
    ]

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        signals,
    )

    result = CompetitiveThreatEngine().assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        signals,
    )

    assert ThreatDimension.PRODUCT in result.dimensions
    assert ThreatDimension.PRICING in result.dimensions
    assert ThreatDimension.TECHNOLOGY in result.dimensions
    assert ThreatDimension.FUNDING in result.dimensions


def test_threat_level_is_deterministic():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    signals = [
        make_signal(
            "signal-1",
            competitor.entity_id,
            SignalType.PRODUCT_LAUNCH,
        ),
        make_signal(
            "signal-2",
            competitor.entity_id,
            SignalType.COMPANY_EXPANSION,
        ),
        make_signal(
            "signal-3",
            competitor.entity_id,
            SignalType.TECHNOLOGY_ADOPTION,
        ),
    ]

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        signals,
    )

    engine = CompetitiveThreatEngine()

    first = engine.assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        signals,
    )

    second = engine.assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        signals,
    )

    assert first.threat_score == second.threat_score
    assert first.threat_level == second.threat_level
    assert first.dimensions == second.dimensions


def test_assess_many_ranks_competitors_by_threat():
    company = make_company("company-a")
    competitor_a = make_company("competitor-a")
    competitor_b = make_company("competitor-b")

    signals = [
        make_signal(
            "signal-a1",
            competitor_a.entity_id,
            SignalType.PRODUCT_LAUNCH,
        ),
        make_signal(
            "signal-a2",
            competitor_a.entity_id,
            SignalType.TECHNOLOGY_ADOPTION,
        ),
        make_signal(
            "signal-a3",
            competitor_a.entity_id,
            SignalType.COMPANY_EXPANSION,
        ),
        make_signal(
            "signal-b1",
            competitor_b.entity_id,
            SignalType.PRICE_CHANGE,
            confidence=0.50,
            strength=0.40,
        ),
    ]

    positioning_engine = CompetitivePositioningEngine()

    positionings = [
        positioning_engine.evaluate(
            company,
            competitor_a,
            signals,
        ),
        positioning_engine.evaluate(
            company,
            competitor_b,
            signals,
        ),
    ]

    result = CompetitiveThreatEngine().assess_many(
        company.entity_id,
        positionings,
        signals,
    )

    assert len(result.threats) == 2
    assert result.threats[0].threat_score >= result.threats[1].threat_score
    assert result.highest_threat_level == result.threats[0].threat_level


def test_invalid_positioning_is_rejected():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    with pytest.raises(TypeError):
        CompetitiveThreatEngine().assess(
            company.entity_id,
            competitor.entity_id,
            object(),
            [],
        )


def test_company_and_competitor_ids_must_match_positioning():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        [],
    )

    with pytest.raises(ValueError):
        CompetitiveThreatEngine().assess(
            company.entity_id,
            "wrong-competitor",
            positioning,
            [],
        )


def test_to_dict_is_explainable():
    company = make_company("company-a")
    competitor = make_company("competitor-a")

    signal = make_signal(
        "signal-1",
        competitor.entity_id,
        SignalType.PRODUCT_LAUNCH,
    )

    positioning = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        [signal],
    )

    result = CompetitiveThreatEngine().assess(
        company.entity_id,
        competitor.entity_id,
        positioning,
        [signal],
    )

    data = result.to_dict()

    assert data["company_id"] == company.entity_id
    assert data["competitor_id"] == competitor.entity_id
    assert "threat_score" in data
    assert "threat_level" in data
    assert "dimensions" in data
    assert "signal_ids" in data
    assert "reasons" in data
