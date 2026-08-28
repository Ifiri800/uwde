from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningEngine,
    CompetitivePositioningResult,
    PositioningAssessment,
    PositioningDimension,
    PositioningLevel,
    evaluate_competitive_positioning,
)
from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)


NOW = datetime(2026, 8, 28, tzinfo=timezone.utc)


def make_company(
    company_id: str,
    *,
    industry: str | None = "technology",
    country: str | None = "Nigeria",
    region: str | None = "Rivers",
    city: str | None = "Port Harcourt",
) -> Company:
    return Company(
        entity_id=company_id,
        name=company_id.replace("-", " ").title(),
        industry=industry,
        country=country,
        region=region,
        city=city,
    )


def make_signal(
    signal_id: str,
    signal_type: SignalType,
    company_id: str,
    *,
    confidence: float = 0.8,
    strength: float = 0.8,
    evidence_ids: list[str] | None = None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=company_id,
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or [],
        detected_at=NOW,
    )


def make_evidence(
    evidence_id: str,
    *,
    confidence: float = 0.9,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_url="https://example.com/source",
        observed_value="competitive evidence",
        confidence=confidence,
    )


def test_result_is_structured():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    assert isinstance(result, CompetitivePositioningResult)
    assert result.company_id == "company-1"
    assert result.competitor_id == "competitor-1"
    assert len(result.assessments) == 9


def test_all_positioning_dimensions_are_present():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    dimensions = {
        assessment.dimension
        for assessment in result.assessments
    }

    assert dimensions == set(PositioningDimension)


def test_market_alignment_same_industry_and_geography():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.MARKET_ALIGNMENT
    )

    assert assessment.score == 1.0
    assert "same industry" in assessment.reasons
    assert "same country" in assessment.reasons
    assert "same region" in assessment.reasons


def test_market_alignment_is_lower_without_industry_match():
    result = evaluate_competitive_positioning(
        make_company("company-1", industry="energy"),
        make_company("competitor-1", industry="technology"),
        [],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.MARKET_ALIGNMENT
    )

    assert assessment.score == 0.3


def test_geographic_presence_detects_same_location():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.GEOGRAPHIC_PRESENCE
    )

    assert assessment.score == 1.0
    assert "same country presence" in assessment.reasons
    assert "same regional presence" in assessment.reasons
    assert "same city presence" in assessment.reasons


def test_product_activity_uses_company_relative_to_competitor():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert assessment.score > 0.5
    assert assessment.signal_ids == ("s1",)
    assert "company has stronger product activity" in assessment.reasons


def test_competitor_product_activity_reduces_relative_score():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert assessment.score < 0.5
    assert "competitor has stronger product activity" in assessment.reasons


def test_pricing_activity_is_evaluated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRICE_CHANGE,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRICING_ACTIVITY
    )

    assert assessment.score > 0.5


def test_technology_adoption_is_evaluated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.TECHNOLOGY_ADOPTION,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.TECHNOLOGY_ADOPTION
    )

    assert assessment.score > 0.5


def test_company_expansion_uses_company_expansion_signal():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.COMPANY_EXPANSION,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.COMPANY_EXPANSION
    )

    assert assessment.score > 0.5


def test_market_growth_contributes_to_expansion():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.MARKET_GROWTH,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.COMPANY_EXPANSION
    )

    assert assessment.score > 0.5


def test_hiring_growth_is_evaluated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.HIRING_SIGNAL,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.HIRING_GROWTH
    )

    assert assessment.score > 0.5


def test_funding_activity_is_evaluated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.FUNDING_SIGNAL,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.FUNDING_ACTIVITY
    )

    assert assessment.score > 0.5


def test_competitive_activity_is_evaluated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.COMPETITOR_CHANGE,
                "company-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.COMPETITIVE_ACTIVITY
    )

    assert assessment.score > 0.5


def test_equal_activity_is_neutral():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRICE_CHANGE,
                "company-1",
            ),
            make_signal(
                "s2",
                SignalType.PRICE_CHANGE,
                "competitor-1",
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRICING_ACTIVITY
    )

    assert assessment.score == 0.5
    assert assessment.level == PositioningLevel.NEUTRAL


def test_signal_strength_is_relative():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
                confidence=1.0,
                strength=1.0,
            ),
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
                confidence=0.5,
                strength=0.5,
            ),
        ],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert assessment.score > 0.5


def test_evidence_is_preserved():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
                evidence_ids=["e1"],
            ),
        ],
        [make_evidence("e1")],
    )

    assessment = next(
        item
        for item in result.assessments
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert assessment.evidence_ids == ("e1",)
    assert result.evidence_ids == ("e1",)


def test_unknown_evidence_ids_are_excluded():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
                evidence_ids=["e1", "missing"],
            ),
        ],
        [make_evidence("e1")],
    )

    assert result.evidence_ids == ("e1",)


def test_signal_ids_are_consolidated():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
            ),
            make_signal(
                "s2",
                SignalType.PRICE_CHANGE,
                "competitor-1",
            ),
        ],
    )

    assert result.signal_ids == ("s1", "s2")


def test_relative_advantages_are_structured():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
                confidence=1.0,
                strength=1.0,
            ),
        ],
    )

    assert (
        PositioningDimension.PRODUCT_ACTIVITY.value
        in result.relative_advantages
    )


def test_relative_disadvantages_are_structured():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
                confidence=1.0,
                strength=1.0,
            ),
        ],
    )

    assert (
        PositioningDimension.PRODUCT_ACTIVITY.value
        in result.relative_disadvantages
    )


def test_result_has_explainable_reasons():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
            ),
        ],
    )

    assert result.reasons
    assert "product activity" in result.reasons[0]


def test_overall_score_is_bounded():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [
            make_signal(
                f"s{i}",
                SignalType.PRODUCT_LAUNCH,
                "company-1",
                confidence=1.0,
                strength=1.0,
            )
            for i in range(20)
        ],
    )

    assert 0.0 <= result.overall_score <= 1.0


def test_overall_confidence_is_bounded():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    assert 0.0 <= result.confidence <= 1.0


def test_no_activity_produces_neutral_signal_dimensions():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    for assessment in result.assessments:
        if assessment.dimension in {
            PositioningDimension.PRODUCT_ACTIVITY,
            PositioningDimension.PRICING_ACTIVITY,
            PositioningDimension.TECHNOLOGY_ADOPTION,
            PositioningDimension.COMPANY_EXPANSION,
            PositioningDimension.HIRING_GROWTH,
            PositioningDimension.FUNDING_ACTIVITY,
            PositioningDimension.COMPETITIVE_ACTIVITY,
        }:
            assert assessment.score == 0.5


def test_to_dict_contains_all_major_fields():
    result = evaluate_competitive_positioning(
        make_company("company-1"),
        make_company("competitor-1"),
        [],
    )

    data = result.to_dict()

    assert data["company_id"] == "company-1"
    assert data["competitor_id"] == "competitor-1"
    assert "overall_score" in data
    assert "level" in data
    assert "confidence" in data
    assert "assessments" in data
    assert "signal_ids" in data
    assert "evidence_ids" in data
    assert "relative_advantages" in data
    assert "relative_disadvantages" in data
    assert "reasons" in data


def test_assessment_to_dict():
    assessment = PositioningAssessment(
        dimension=PositioningDimension.PRODUCT_ACTIVITY,
        score=0.8,
        level=PositioningLevel.STRONG,
        confidence=0.9,
        signal_ids=("s1",),
        evidence_ids=("e1",),
        reasons=("strong product activity",),
    )

    data = assessment.to_dict()

    assert data["dimension"] == "product_activity"
    assert data["score"] == 0.8
    assert data["level"] == "strong"
    assert data["signal_ids"] == ["s1"]
    assert data["evidence_ids"] == ["e1"]


def test_result_rejects_empty_company_id():
    with pytest.raises(ValueError, match="company_id is required"):
        CompetitivePositioningResult(
            company_id="",
            competitor_id="competitor-1",
            overall_score=0.5,
            level=PositioningLevel.NEUTRAL,
            confidence=0.5,
            assessments=(),
        )


def test_result_rejects_empty_competitor_id():
    with pytest.raises(
        ValueError,
        match="competitor_id is required",
    ):
        CompetitivePositioningResult(
            company_id="company-1",
            competitor_id="",
            overall_score=0.5,
            level=PositioningLevel.NEUTRAL,
            confidence=0.5,
            assessments=(),
        )


def test_result_rejects_same_company_and_competitor():
    with pytest.raises(
        ValueError,
        match="company_id and competitor_id must differ",
    ):
        CompetitivePositioningResult(
            company_id="company-1",
            competitor_id="company-1",
            overall_score=0.5,
            level=PositioningLevel.NEUTRAL,
            confidence=0.5,
            assessments=(),
        )


def test_invalid_company_type():
    with pytest.raises(
        TypeError,
        match="company must be a Company",
    ):
        evaluate_competitive_positioning(
            "invalid",  # type: ignore[arg-type]
            make_company("competitor-1"),
            [],
        )


def test_invalid_competitor_type():
    with pytest.raises(
        TypeError,
        match="competitor must be a Company",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            "invalid",  # type: ignore[arg-type]
            [],
        )


def test_invalid_signals_type():
    with pytest.raises(
        TypeError,
        match="signals must be a list",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            make_company("competitor-1"),
            "invalid",  # type: ignore[arg-type]
        )


def test_invalid_signal_items():
    with pytest.raises(
        TypeError,
        match="signals must contain only Signal objects",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            make_company("competitor-1"),
            ["invalid"],  # type: ignore[list-item]
        )


def test_invalid_evidence_type():
    with pytest.raises(
        TypeError,
        match="evidence must be a list",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            make_company("competitor-1"),
            [],
            "invalid",  # type: ignore[arg-type]
        )


def test_invalid_evidence_items():
    with pytest.raises(
        TypeError,
        match="evidence must contain only Evidence objects",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            make_company("competitor-1"),
            [],
            ["invalid"],  # type: ignore[list-item]
        )


def test_same_company_rejected_by_engine():
    with pytest.raises(
        ValueError,
        match="company and competitor must differ",
    ):
        evaluate_competitive_positioning(
            make_company("company-1"),
            make_company("company-1"),
            [],
        )


def test_class_and_function_api_are_equivalent():
    company = make_company("company-1")
    competitor = make_company("competitor-1")
    signals = [
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
            "company-1",
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
            "competitor-1",
        ),
    ]

    function_result = evaluate_competitive_positioning(
        company,
        competitor,
        signals,
    )

    class_result = CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        signals,
    )

    assert function_result.to_dict() == class_result.to_dict()
