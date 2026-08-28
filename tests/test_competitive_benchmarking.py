from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.competitive.benchmarking import (
    CompetitiveBenchmarkDimension,
    CompetitiveBenchmarkEntry,
    CompetitiveBenchmarkResult,
)
from backend.app.services.intelligence.competitive.positioning import (
    CompetitivePositioningResult,
    PositioningAssessment,
    PositioningDimension,
    PositioningLevel,
)
from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal, SignalType


def make_positioning() -> CompetitivePositioningResult:
    return CompetitivePositioningResult(
        company_id="company-1",
        competitor_id="competitor-1",
        overall_score=0.75,
        level=PositioningLevel.STRONG,
        confidence=0.9,
        assessments=(),
        signal_ids=("s1",),
        evidence_ids=("e1",),
        relative_advantages=("product_activity",),
        reasons=("company has stronger product activity",),
    )


def make_entry() -> CompetitiveBenchmarkEntry:
    positioning = make_positioning()

    return CompetitiveBenchmarkEntry(
        competitor_id="competitor-1",
        overall_score=positioning.overall_score,
        level=positioning.level,
        confidence=positioning.confidence,
        positioning=positioning,
    )


def test_benchmark_entry_to_dict():
    entry = make_entry()

    data = entry.to_dict()

    assert data["competitor_id"] == "competitor-1"
    assert data["overall_score"] == 0.75
    assert data["level"] == "strong"
    assert data["confidence"] == 0.9
    assert data["positioning"]["company_id"] == "company-1"


def test_benchmark_entry_requires_competitor_id():
    with pytest.raises(
        ValueError,
        match="competitor_id is required",
    ):
        CompetitiveBenchmarkEntry(
            competitor_id="",
            overall_score=0.5,
            level=PositioningLevel.NEUTRAL,
            confidence=0.5,
            positioning=make_positioning(),
        )


def test_benchmark_entry_score_bounds():
    with pytest.raises(
        ValueError,
        match="overall_score must be between 0.0 and 1.0",
    ):
        CompetitiveBenchmarkEntry(
            competitor_id="competitor-1",
            overall_score=1.5,
            level=PositioningLevel.STRONG,
            confidence=0.5,
            positioning=make_positioning(),
        )


def test_benchmark_entry_confidence_bounds():
    with pytest.raises(
        ValueError,
        match="confidence must be between 0.0 and 1.0",
    ):
        CompetitiveBenchmarkEntry(
            competitor_id="competitor-1",
            overall_score=0.5,
            level=PositioningLevel.NEUTRAL,
            confidence=1.5,
            positioning=make_positioning(),
        )


def test_dimension_to_dict():
    dimension = CompetitiveBenchmarkDimension(
        dimension=PositioningDimension.PRODUCT_ACTIVITY,
        rankings=("competitor-1", "competitor-2"),
    )

    data = dimension.to_dict()

    assert data["dimension"] == "product_activity"
    assert data["rankings"] == [
        "competitor-1",
        "competitor-2",
    ]


def test_result_to_dict():
    result = CompetitiveBenchmarkResult(
        company_id="company-1",
        competitors=(make_entry(),),
        dimensions=(
            CompetitiveBenchmarkDimension(
                dimension=PositioningDimension.PRODUCT_ACTIVITY,
                rankings=("competitor-1",),
            ),
        ),
        overall_ranking=("competitor-1",),
        strongest_dimensions=(
            PositioningDimension.PRODUCT_ACTIVITY,
        ),
        weakest_dimensions=(
            PositioningDimension.PRICING_ACTIVITY,
        ),
        signal_ids=("s1",),
        evidence_ids=("e1",),
        confidence=0.9,
        reasons=("product activity leads benchmark",),
    )

    data = result.to_dict()

    assert data["company_id"] == "company-1"
    assert data["overall_ranking"] == ["competitor-1"]
    assert data["strongest_dimensions"] == [
        "product_activity",
    ]
    assert data["weakest_dimensions"] == [
        "pricing_activity",
    ]
    assert data["signal_ids"] == ["s1"]
    assert data["evidence_ids"] == ["e1"]
    assert data["confidence"] == 0.9
    assert data["reasons"] == [
        "product activity leads benchmark",
    ]


def test_result_requires_company_id():
    with pytest.raises(
        ValueError,
        match="company_id is required",
    ):
        CompetitiveBenchmarkResult(
            company_id="",
            competitors=(),
            dimensions=(),
            overall_ranking=(),
        )


def test_result_confidence_bounds():
    with pytest.raises(
        ValueError,
        match="confidence must be between 0.0 and 1.0",
    ):
        CompetitiveBenchmarkResult(
            company_id="company-1",
            competitors=(),
            dimensions=(),
            overall_ranking=(),
            confidence=1.5,
        )
from backend.app.services.intelligence.competitive.benchmarking import (
    CompetitiveBenchmarkingEngine,
    benchmark_competitive_positioning,
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


def test_benchmark_ranks_multiple_competitors():
    company = make_company("company-1")
    competitor_1 = make_company("competitor-1")
    competitor_2 = make_company("competitor-2")

    signals = [
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
            "competitor-1",
            confidence=1.0,
            strength=1.0,
        ),
        make_signal(
            "s2",
            SignalType.PRODUCT_LAUNCH,
            "competitor-2",
            confidence=0.5,
            strength=0.5,
        ),
    ]

    result = benchmark_competitive_positioning(
        company,
        [competitor_1, competitor_2],
        signals,
    )

    assert len(result.competitors) == 2
    assert result.overall_ranking == (
        "competitor-1",
        "competitor-2",
    )


def test_benchmark_preserves_pairwise_positioning():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [make_company("competitor-1")],
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
            ),
        ],
    )

    entry = result.competitors[0]

    assert entry.competitor_id == "competitor-1"
    assert entry.positioning.company_id == "company-1"
    assert entry.positioning.competitor_id == "competitor-1"


def test_dimension_rankings_are_generated_for_all_dimensions():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-1"),
            make_company("competitor-2"),
        ],
        [],
    )

    assert len(result.dimensions) == len(
        PositioningDimension
    )

    dimensions = {
        item.dimension
        for item in result.dimensions
    }

    assert dimensions == set(PositioningDimension)


def test_dimension_ranking_follows_dimension_score():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-1"),
            make_company("competitor-2"),
        ],
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
                confidence=1.0,
                strength=1.0,
            ),
            make_signal(
                "s2",
                SignalType.PRODUCT_LAUNCH,
                "competitor-2",
                confidence=0.5,
                strength=0.5,
            ),
        ],
    )

    dimension = next(
        item
        for item in result.dimensions
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert dimension.rankings == (
        "competitor-1",
        "competitor-2",
    )


def test_dimension_ties_are_deterministic():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-z"),
            make_company("competitor-a"),
        ],
        [],
    )

    dimension = next(
        item
        for item in result.dimensions
        if item.dimension
        == PositioningDimension.PRODUCT_ACTIVITY
    )

    assert dimension.rankings == (
        "competitor-a",
        "competitor-z",
    )


def test_strongest_and_weakest_dimensions_are_identified():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [make_company("competitor-1")],
        [],
    )

    assert result.strongest_dimensions
    assert result.weakest_dimensions


def test_signal_ids_are_consolidated_across_competitors():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-1"),
            make_company("competitor-2"),
        ],
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
            ),
            make_signal(
                "s2",
                SignalType.PRICE_CHANGE,
                "competitor-2",
            ),
        ],
    )

    assert result.signal_ids == ("s1", "s2")


def test_evidence_ids_are_consolidated_across_competitors():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-1"),
            make_company("competitor-2"),
        ],
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                "competitor-1",
                evidence_ids=["e1", "e2"],
            ),
            make_signal(
                "s2",
                SignalType.PRICE_CHANGE,
                "competitor-2",
                evidence_ids=["e2", "e3"],
            ),
        ],
        [
            make_evidence("e1"),
            make_evidence("e2"),
            make_evidence("e3"),
        ],
    )

    assert result.evidence_ids == (
        "e1",
        "e2",
        "e3",
    )


def test_benchmark_confidence_is_aggregated():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [
            make_company("competitor-1"),
            make_company("competitor-2"),
        ],
        [],
    )

    assert 0.0 <= result.confidence <= 1.0


def test_empty_competitor_list_is_valid():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [],
        [],
    )

    assert result.competitors == ()
    assert result.overall_ranking == ()
    assert result.dimensions
    assert result.confidence == 0.0


def test_company_cannot_be_a_competitor():
    with pytest.raises(
        ValueError,
        match="company cannot appear in competitors",
    ):
        benchmark_competitive_positioning(
            make_company("company-1"),
            [make_company("company-1")],
            [],
        )


def test_duplicate_competitors_are_rejected():
    with pytest.raises(
        ValueError,
        match="competitors must have unique entity IDs",
    ):
        benchmark_competitive_positioning(
            make_company("company-1"),
            [
                make_company("competitor-1"),
                make_company("competitor-1"),
            ],
            [],
        )


def test_invalid_competitor_list_type():
    with pytest.raises(
        TypeError,
        match="competitors must be a list",
    ):
        benchmark_competitive_positioning(
            make_company("company-1"),
            "invalid",  # type: ignore[arg-type]
            [],
        )


def test_invalid_competitor_items():
    with pytest.raises(
        TypeError,
        match="competitors must contain only Company objects",
    ):
        benchmark_competitive_positioning(
            make_company("company-1"),
            ["invalid"],  # type: ignore[list-item]
            [],
        )


def test_benchmark_reasons_are_explainable():
    result = benchmark_competitive_positioning(
        make_company("company-1"),
        [make_company("competitor-1")],
        [],
    )

    assert result.reasons
    assert "ranks first overall" in result.reasons[0]


def test_class_and_function_api_are_equivalent():
    company = make_company("company-1")
    competitors = [
        make_company("competitor-1"),
        make_company("competitor-2"),
    ]

    signals = [
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
            "competitor-1",
        ),
    ]

    function_result = benchmark_competitive_positioning(
        company,
        competitors,
        signals,
    )

    class_result = CompetitiveBenchmarkingEngine().benchmark(
        company,
        competitors,
        signals,
    )

    assert function_result.to_dict() == class_result.to_dict()
