from __future__ import annotations

import pytest

from backend.app.services.intelligence.competitive.benchmarking import (
    CompetitiveBenchmarkDimension,
    CompetitiveBenchmarkEntry,
    CompetitiveBenchmarkResult,
)
from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningResult,
    PositioningDimension,
    PositioningLevel,
)
from backend.app.services.intelligence.competitive.synthesis import (
    CompetitiveSynthesisEngine,
    CompetitiveSynthesisInsight,
    CompetitiveSynthesisResult,
    synthesize_competitive_intelligence,
)


def make_positioning(
    competitor_id: str = "competitor-1",
) -> CompetitivePositioningResult:
    return CompetitivePositioningResult(
        company_id="company-1",
        competitor_id=competitor_id,
        overall_score=0.8,
        level=PositioningLevel.STRONG,
        confidence=0.9,
        assessments=(),
        signal_ids=("s1",),
        evidence_ids=("e1",),
        relative_advantages=(),
        reasons=(),
    )


def make_entry(
    competitor_id: str = "competitor-1",
    score: float = 0.8,
) -> CompetitiveBenchmarkEntry:
    positioning = make_positioning(competitor_id)

    return CompetitiveBenchmarkEntry(
        competitor_id=competitor_id,
        overall_score=score,
        level=positioning.level,
        confidence=positioning.confidence,
        positioning=positioning,
    )


def make_benchmark() -> CompetitiveBenchmarkResult:
    return CompetitiveBenchmarkResult(
        company_id="company-1",
        competitors=(
            make_entry("competitor-1", 0.9),
            make_entry("competitor-2", 0.8),
            make_entry("competitor-3", 0.6),
        ),
        dimensions=(
            CompetitiveBenchmarkDimension(
                dimension=PositioningDimension.PRODUCT_ACTIVITY,
                rankings=(
                    "competitor-1",
                    "competitor-2",
                    "competitor-3",
                ),
            ),
        ),
        overall_ranking=(
            "competitor-1",
            "competitor-2",
            "competitor-3",
        ),
        strongest_dimensions=(
            PositioningDimension.PRODUCT_ACTIVITY,
        ),
        weakest_dimensions=(
            PositioningDimension.PRICING_ACTIVITY,
        ),
        signal_ids=("s1",),
        evidence_ids=("e1",),
        confidence=0.9,
        reasons=("benchmark is explainable",),
    )


def test_insight_to_dict():
    insight = CompetitiveSynthesisInsight(
        category="competitive_strength",
        subject_id="competitor-1",
        message="competitor-1 is strongest",
        confidence=0.9,
        signal_ids=("s1",),
        evidence_ids=("e1",),
    )

    assert insight.to_dict() == {
        "category": "competitive_strength",
        "subject_id": "competitor-1",
        "message": "competitor-1 is strongest",
        "confidence": 0.9,
        "signal_ids": ["s1"],
        "evidence_ids": ["e1"],
    }


def test_insight_requires_category():
    with pytest.raises(
        ValueError,
        match="category is required",
    ):
        CompetitiveSynthesisInsight(
            category="",
            subject_id="competitor-1",
            message="message",
            confidence=0.5,
        )


def test_insight_confidence_bounds():
    with pytest.raises(
        ValueError,
        match="confidence must be between 0.0 and 1.0",
    ):
        CompetitiveSynthesisInsight(
            category="test",
            subject_id="competitor-1",
            message="message",
            confidence=1.5,
        )


def test_result_to_dict():
    result = CompetitiveSynthesisResult(
        company_id="company-1",
        strongest_competitors=("competitor-1",),
        strategic_pressures=("competitor-1",),
        strongest_dimensions=(
            PositioningDimension.PRODUCT_ACTIVITY,
        ),
        weakest_dimensions=(
            PositioningDimension.PRICING_ACTIVITY,
        ),
        signal_ids=("s1",),
        evidence_ids=("e1",),
        confidence=0.9,
        reasons=("reason",),
    )

    data = result.to_dict()

    assert data["company_id"] == "company-1"
    assert data["strongest_competitors"] == [
        "competitor-1",
    ]
    assert data["strategic_pressures"] == [
        "competitor-1",
    ]
    assert data["strongest_dimensions"] == [
        "product_activity",
    ]
    assert data["weakest_dimensions"] == [
        "pricing_activity",
    ]


def test_result_requires_company_id():
    with pytest.raises(
        ValueError,
        match="company_id is required",
    ):
        CompetitiveSynthesisResult(company_id="")


def test_engine_requires_benchmark():
    with pytest.raises(
        TypeError,
        match="benchmark must be a CompetitiveBenchmarkResult",
    ):
        CompetitiveSynthesisEngine().synthesize(None)  # type: ignore[arg-type]


def test_engine_identifies_strongest_competitors():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert result.strongest_competitors == (
        "competitor-1",
        "competitor-2",
        "competitor-3",
    )


def test_engine_identifies_strategic_pressure():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert result.strategic_pressures == (
        "competitor-1",
        "competitor-2",
    )


def test_engine_preserves_benchmark_traceability():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert result.signal_ids == ("s1",)
    assert result.evidence_ids == ("e1",)
    assert result.confidence == 0.9


def test_engine_preserves_dimension_extremes():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert result.strongest_dimensions == (
        PositioningDimension.PRODUCT_ACTIVITY,
    )
    assert result.weakest_dimensions == (
        PositioningDimension.PRICING_ACTIVITY,
    )


def test_engine_generates_insights():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert result.insights
    assert result.insights[0].subject_id == "competitor-1"


def test_engine_generates_explainable_reasons():
    result = CompetitiveSynthesisEngine().synthesize(
        make_benchmark()
    )

    assert any(
        "top competitive threat" in reason
        for reason in result.reasons
    )


def test_convenience_function_matches_engine():
    benchmark = make_benchmark()

    expected = CompetitiveSynthesisEngine().synthesize(
        benchmark
    )
    actual = synthesize_competitive_intelligence(
        benchmark
    )

    assert actual == expected
