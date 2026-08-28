from __future__ import annotations

import pytest

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from backend.app.services.intelligence.market.deduplication import (
    SignalDeduplicator,
    SignalDeduplicationResult,
    deduplicate_signals,
)


def make_signal(
    signal_id: str,
    *,
    signal_type: SignalType = SignalType.MARKET_GROWTH,
    entity_id: str = "market-1",
    previous_value: object | None = None,
    current_value: object | None = "growth",
    confidence: float = 0.8,
    strength: float = 0.7,
    evidence_ids: list[str] | None = None,
) -> Signal:
    return Signal(
        signal_id=signal_id,
        signal_type=signal_type,
        entity_id=entity_id,
        previous_value=previous_value,
        current_value=current_value,
        confidence=confidence,
        strength=strength,
        evidence_ids=evidence_ids or [],
    )


def test_exact_duplicate_is_suppressed():
    signals = [
        make_signal("s1", evidence_ids=["e1"]),
        make_signal("s2", evidence_ids=["e2"]),
    ]

    result = deduplicate_signals(signals)

    assert len(result.signals) == 1
    assert result.duplicates_removed == 1
    assert result.groups_merged == 1


def test_duplicate_evidence_is_merged():
    signals = [
        make_signal("s1", evidence_ids=["e1"]),
        make_signal("s2", evidence_ids=["e2", "e3"]),
    ]

    result = deduplicate_signals(signals)

    assert list(result.signals[0].evidence_ids) == [
        "e1",
        "e2",
        "e3",
    ]


def test_duplicate_preserves_strongest_confidence():
    signals = [
        make_signal("s1", confidence=0.60),
        make_signal("s2", confidence=0.95),
    ]

    result = deduplicate_signals(signals)

    assert result.signals[0].confidence == 0.95


def test_duplicate_preserves_strongest_strength():
    signals = [
        make_signal("s1", strength=0.40),
        make_signal("s2", strength=0.90),
    ]

    result = deduplicate_signals(signals)

    assert result.signals[0].strength == 0.90


def test_different_current_values_are_not_duplicates():
    signals = [
        make_signal("s1", current_value="growth"),
        make_signal("s2", current_value="decline"),
    ]

    result = deduplicate_signals(signals)

    assert len(result.signals) == 2
    assert result.duplicates_removed == 0


def test_different_signal_types_are_not_duplicates():
    signals = [
        make_signal(
            "s1",
            signal_type=SignalType.MARKET_GROWTH,
        ),
        make_signal(
            "s2",
            signal_type=SignalType.BUYER_INTENT,
        ),
    ]

    result = deduplicate_signals(signals)

    assert len(result.signals) == 2


def test_different_entities_are_not_duplicates():
    signals = [
        make_signal("s1", entity_id="market-1"),
        make_signal("s2", entity_id="market-2"),
    ]

    result = deduplicate_signals(signals)

    assert len(result.signals) == 2


def test_nested_values_can_be_deduplicated():
    signals = [
        make_signal(
            "s1",
            current_value={
                "price": 100,
                "currency": "USD",
            },
        ),
        make_signal(
            "s2",
            current_value={
                "currency": "USD",
                "price": 100,
            },
        ),
    ]

    result = deduplicate_signals(signals)

    assert len(result.signals) == 1


def test_metadata_records_merge_information():
    signals = [
        make_signal("s1"),
        make_signal("s2"),
    ]

    result = deduplicate_signals(signals)
    signal = result.signals[0]

    assert signal.metadata["deduplicated"] is True
    assert signal.metadata["merged_signal_ids"] == ["s1", "s2"]
    assert signal.metadata["duplicate_count"] == 1


def test_first_signal_identity_is_preserved():
    signals = [
        make_signal("first"),
        make_signal("second"),
    ]

    result = deduplicate_signals(signals)

    assert result.signals[0].signal_id == "first"


def test_non_duplicates_preserve_input_order():
    signals = [
        make_signal("s1", current_value="a"),
        make_signal("s2", current_value="b"),
        make_signal("s3", current_value="c"),
    ]

    result = deduplicate_signals(signals)

    assert [
        signal.signal_id
        for signal in result.signals
    ] == ["s1", "s2", "s3"]


def test_empty_input():
    result = deduplicate_signals([])

    assert result.signals == ()
    assert result.duplicates_removed == 0
    assert result.groups_merged == 0


def test_invalid_input_type():
    with pytest.raises(TypeError, match="signals must be a list"):
        deduplicate_signals("invalid")  # type: ignore[arg-type]


def test_invalid_signal_items():
    with pytest.raises(
        TypeError,
        match="signals must contain only Signal objects",
    ):
        deduplicate_signals(
            [make_signal("s1"), "invalid"]  # type: ignore[list-item]
        )


def test_result_is_explainable():
    result = deduplicate_signals(
        [
            make_signal("s1"),
            make_signal("s2"),
        ]
    )

    assert isinstance(result, SignalDeduplicationResult)

    data = result.to_dict()

    assert data["duplicates_removed"] == 1
    assert data["groups_merged"] == 1
    assert len(data["signals"]) == 1


def test_class_and_function_api_are_equivalent():
    signals = [
        make_signal("s1"),
        make_signal("s2"),
    ]

    function_result = deduplicate_signals(signals)
    class_result = SignalDeduplicator().deduplicate(signals)

    assert function_result.to_dict() == class_result.to_dict()
