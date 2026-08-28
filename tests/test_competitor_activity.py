from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.competitive.activity import (
    CompetitorActivity,
    CompetitorActivityAnalyzer,
    CompetitorActivityResult,
    CompetitorActivityType,
    analyze_competitor_activity,
)
from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)


def make_company(
    company_id: str = "company-1",
    *,
    industry: str | None = "technology",
) -> Company:
    return Company(
        entity_id=company_id,
        name="Example Company",
        industry=industry,
    )


def make_signal(
    signal_id: str,
    signal_type: SignalType,
    *,
    company_id: str = "company-1",
    confidence: float = 0.8,
    evidence_ids: list[str] | None = None,
    detected_at: datetime | None = None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=company_id,
        confidence=confidence,
        strength=0.7,
        evidence_ids=evidence_ids or [],
        detected_at=detected_at
        or datetime(
            2026,
            8,
            28,
            tzinfo=timezone.utc,
        ),
    )


def make_evidence(
    evidence_id: str,
    *,
    confidence: float = 0.9,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        source_url="https://example.com/source",
        observed_value="activity",
        confidence=confidence,
    )


def test_product_launch_maps_to_product_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
            )
        ],
    )

    assert len(result.activities) == 1
    assert (
        result.activities[0].activity_type
        == CompetitorActivityType.PRODUCT_ACTIVITY
    )


def test_new_product_maps_to_product_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.NEW_PRODUCT,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.PRODUCT_ACTIVITY
    )


def test_price_change_maps_to_pricing_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRICE_CHANGE,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.PRICING_ACTIVITY
    )


def test_hiring_maps_to_hiring_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.HIRING_SIGNAL,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.HIRING_ACTIVITY
    )


def test_funding_maps_to_funding_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.FUNDING_SIGNAL,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.FUNDING_ACTIVITY
    )


def test_expansion_and_market_growth_map_to_expansion_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.COMPANY_EXPANSION,
            ),
            make_signal(
                "s2",
                SignalType.MARKET_GROWTH,
            ),
        ],
    )

    assert len(result.activities) == 1
    assert result.activities[0].activity_type == (
        CompetitorActivityType.EXPANSION_ACTIVITY
    )
    assert result.activities[0].signal_ids == ("s1", "s2")


def test_technology_adoption_maps_to_technology_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.TECHNOLOGY_ADOPTION,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.TECHNOLOGY_ACTIVITY
    )


def test_competitor_change_maps_to_competitive_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.COMPETITOR_CHANGE,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.COMPETITIVE_ACTIVITY
    )


def test_buyer_intent_maps_to_commercial_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.BUYER_INTENT,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.COMMERCIAL_ACTIVITY
    )


def test_procurement_maps_to_procurement_activity():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PROCUREMENT_SIGNAL,
            )
        ],
    )

    assert result.activities[0].activity_type == (
        CompetitorActivityType.PROCUREMENT_ACTIVITY
    )


def test_irrelevant_company_signals_are_ignored():
    result = analyze_competitor_activity(
        make_company("company-1"),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                company_id="company-2",
            )
        ],
    )

    assert result.activities == ()


def test_unmapped_signal_types_are_ignored():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.TENDER_OPPORTUNITY,
            )
        ],
    )

    assert result.activities == ()


def test_multiple_signals_are_grouped_by_activity_type():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
            ),
            make_signal(
                "s2",
                SignalType.NEW_PRODUCT,
            ),
            make_signal(
                "s3",
                SignalType.PRICE_CHANGE,
            ),
        ],
    )

    assert len(result.activities) == 2

    product_activity = next(
        activity
        for activity in result.activities
        if activity.activity_type
        == CompetitorActivityType.PRODUCT_ACTIVITY
    )

    assert product_activity.signal_ids == ("s1", "s2")


def test_strongest_confidence_is_preserved():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                confidence=0.60,
            ),
            make_signal(
                "s2",
                SignalType.NEW_PRODUCT,
                confidence=0.95,
            ),
        ],
    )

    assert result.activities[0].confidence == 0.95


def test_evidence_is_consolidated():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                evidence_ids=["e1", "e2"],
            ),
            make_signal(
                "s2",
                SignalType.NEW_PRODUCT,
                evidence_ids=["e2", "e3"],
            ),
        ],
        [
            make_evidence("e1"),
            make_evidence("e2"),
            make_evidence("e3"),
        ],
    )

    assert result.activities[0].evidence_ids == (
        "e1",
        "e2",
        "e3",
    )


def test_unknown_evidence_ids_are_not_attached():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                evidence_ids=["e1", "missing"],
            )
        ],
        [make_evidence("e1")],
    )

    assert result.activities[0].evidence_ids == ("e1",)


def test_latest_signal_timestamp_is_used():
    first = datetime(
        2026,
        8,
        20,
        tzinfo=timezone.utc,
    )

    latest = datetime(
        2026,
        8,
        28,
        tzinfo=timezone.utc,
    )

    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                detected_at=first,
            ),
            make_signal(
                "s2",
                SignalType.NEW_PRODUCT,
                detected_at=latest,
            ),
        ],
    )

    assert result.activities[0].detected_at == latest


def test_activity_contains_explainable_reasons():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
            )
        ],
    )

    assert result.activities[0].reasons == (
        "product_launch detected",
    )


def test_result_tracks_all_signals_evaluated():
    signals = [
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
        ),
    ]

    result = analyze_competitor_activity(
        make_company(),
        signals,
    )

    assert result.signals_evaluated == 2


def test_empty_signal_list():
    result = analyze_competitor_activity(
        make_company(),
        [],
    )

    assert result.activities == ()
    assert result.signals_evaluated == 0


def test_invalid_company_type():
    with pytest.raises(
        TypeError,
        match="company must be a Company",
    ):
        analyze_competitor_activity(
            "invalid",  # type: ignore[arg-type]
            [],
        )


def test_invalid_signals_type():
    with pytest.raises(
        TypeError,
        match="signals must be a list",
    ):
        analyze_competitor_activity(
            make_company(),
            "invalid",  # type: ignore[arg-type]
        )


def test_invalid_signal_items():
    with pytest.raises(
        TypeError,
        match="signals must contain only Signal objects",
    ):
        analyze_competitor_activity(
            make_company(),
            [
                "invalid",  # type: ignore[list-item]
            ],
        )


def test_invalid_evidence_type():
    with pytest.raises(
        TypeError,
        match="evidence must be a list",
    ):
        analyze_competitor_activity(
            make_company(),
            [],
            "invalid",  # type: ignore[arg-type]
        )


def test_invalid_evidence_items():
    with pytest.raises(
        TypeError,
        match="evidence must contain only Evidence objects",
    ):
        analyze_competitor_activity(
            make_company(),
            [],
            [
                "invalid",  # type: ignore[list-item]
            ],
        )


def test_activity_result_to_dict():
    result = analyze_competitor_activity(
        make_company(),
        [
            make_signal(
                "s1",
                SignalType.PRODUCT_LAUNCH,
                evidence_ids=["e1"],
            )
        ],
        [make_evidence("e1")],
    )

    data = result.to_dict()

    assert data["signals_evaluated"] == 1
    assert len(data["activities"]) == 1
    assert data["activities"][0]["activity_type"] == (
        CompetitorActivityType.PRODUCT_ACTIVITY
    )


def test_activity_model_to_dict():
    activity = CompetitorActivity(
        company_id="company-1",
        activity_type=CompetitorActivityType.PRODUCT_ACTIVITY,
        confidence=0.85,
        signal_ids=("s1",),
        evidence_ids=("e1",),
        reasons=("product_launch detected",),
    )

    data = activity.to_dict()

    assert data["company_id"] == "company-1"
    assert data["confidence"] == 0.85
    assert data["signal_ids"] == ["s1"]
    assert data["evidence_ids"] == ["e1"]


def test_activity_requires_company_id():
    with pytest.raises(
        ValueError,
        match="company_id is required",
    ):
        CompetitorActivity(
            company_id="",
            activity_type=CompetitorActivityType.PRODUCT_ACTIVITY,
            confidence=0.8,
        )


def test_activity_requires_activity_type():
    with pytest.raises(
        ValueError,
        match="activity_type is required",
    ):
        CompetitorActivity(
            company_id="company-1",
            activity_type="",
            confidence=0.8,
        )


def test_activity_confidence_bounds():
    with pytest.raises(
        ValueError,
        match="confidence must be between 0.0 and 1.0",
    ):
        CompetitorActivity(
            company_id="company-1",
            activity_type=CompetitorActivityType.PRODUCT_ACTIVITY,
            confidence=1.5,
        )


def test_result_requires_non_negative_signal_count():
    with pytest.raises(
        ValueError,
        match="signals_evaluated cannot be negative",
    ):
        CompetitorActivityResult(
            activities=(),
            signals_evaluated=-1,
        )


def test_class_and_function_api_are_equivalent():
    company = make_company()

    signals = [
        make_signal(
            "s1",
            SignalType.PRODUCT_LAUNCH,
        ),
        make_signal(
            "s2",
            SignalType.PRICE_CHANGE,
        ),
    ]

    function_result = analyze_competitor_activity(
        company,
        signals,
    )

    class_result = CompetitorActivityAnalyzer().analyze(
        company,
        signals,
    )

    assert function_result.to_dict() == class_result.to_dict()
