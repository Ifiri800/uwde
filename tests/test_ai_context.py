from backend.app.services.intelligence.ai.context import (
    add_observation,
    build_ai_context,
    observation_from_mapping,
)
from backend.app.services.intelligence.ai.models import (
    AIContext,
    AIObservation,
)


def test_empty_context():
    context = build_ai_context()

    assert isinstance(context, AIContext)
    assert context.observations == ()
    assert context.entities == ()
    assert context.signals == ()
    assert context.metadata == {}
    assert context.observation_count == 0


def test_build_context_from_observations():
    observation = AIObservation(
        source="market",
        category="growth",
        statement="Market demand is increasing.",
        confidence=0.9,
    )

    context = build_ai_context([observation])

    assert context.observations == (observation,)
    assert context.observation_count == 1


def test_entities_are_preserved():
    entities = [
        {"text": "Acme Energy Ltd", "type": "organization"},
        {"text": "Nigeria", "type": "location"},
    ]

    context = build_ai_context(entities=entities)

    assert context.entities == tuple(entities)


def test_signals_are_preserved():
    signals = [
        {"type": "market_growth", "confidence": 0.85},
        {"type": "competitive_threat", "confidence": 0.75},
    ]

    context = build_ai_context(signals=signals)

    assert context.signals == tuple(signals)


def test_metadata_is_preserved():
    context = build_ai_context(
        metadata={
            "source_count": 3,
            "domain": "market",
            "request_id": "test-001",
        }
    )

    assert context.metadata["source_count"] == 3
    assert context.metadata["domain"] == "market"
    assert context.metadata["request_id"] == "test-001"


def test_observation_from_mapping_uses_statement():
    observation = observation_from_mapping(
        {
            "statement": "Demand increased.",
            "confidence": 0.8,
            "evidence": ["source-a", "source-b"],
        },
        source="market",
        category="demand",
    )

    assert observation.statement == "Demand increased."
    assert observation.confidence == 0.8
    assert observation.evidence == ("source-a", "source-b")


def test_observation_from_mapping_uses_fallback_fields():
    observation = observation_from_mapping(
        {"description": "Competitor expanded."},
        source="competitive",
        category="activity",
    )

    assert observation.statement == "Competitor expanded."


def test_confidence_is_normalized():
    high = observation_from_mapping(
        {"statement": "High confidence", "confidence": 2},
        source="test",
        category="test",
    )

    low = observation_from_mapping(
        {"statement": "Low confidence", "confidence": -1},
        source="test",
        category="test",
    )

    assert high.confidence == 1.0
    assert low.confidence == 0.0


def test_string_evidence_becomes_single_item():
    observation = observation_from_mapping(
        {
            "statement": "Observed activity.",
            "evidence": "source-a",
        },
        source="test",
        category="activity",
    )

    assert observation.evidence == ("source-a",)


def test_add_observation_does_not_mutate_original():
    first = AIObservation(
        source="market",
        category="growth",
        statement="Growth detected.",
        confidence=0.9,
    )

    second = AIObservation(
        source="forecasting",
        category="forecast",
        statement="Growth expected.",
        confidence=0.8,
    )

    original = build_ai_context([first])
    updated = add_observation(original, second)

    assert original.observations == (first,)
    assert updated.observations == (first, second)
    assert original is not updated


def test_cross_domain_context_can_be_assembled():
    observations = [
        AIObservation(
            source="market",
            category="growth",
            statement="Market demand is increasing.",
            confidence=0.9,
        ),
        AIObservation(
            source="competitive",
            category="threat",
            statement="A competitor expanded.",
            confidence=0.8,
        ),
        AIObservation(
            source="forecasting",
            category="forecast",
            statement="Growth is expected to continue.",
            confidence=0.85,
        ),
    ]

    context = build_ai_context(
        observations,
        entities=[
            {"text": "Acme Energy Ltd", "type": "organization"},
        ],
        signals=[
            {"type": "market_growth", "confidence": 0.9},
        ],
        metadata={
            "domains": (
                "market",
                "competitive",
                "forecasting",
            )
        },
    )

    assert context.observation_count == 3
    assert len(context.entities) == 1
    assert len(context.signals) == 1
    assert context.metadata["domains"] == (
        "market",
        "competitive",
        "forecasting",
    )


def test_context_building_is_deterministic():
    observation = AIObservation(
        source="market",
        category="growth",
        statement="Demand increased.",
        confidence=0.9,
    )

    first = build_ai_context(
        [observation],
        entities=[{"name": "Acme"}],
        signals=[{"type": "growth"}],
        metadata={"domain": "market"},
    )

    second = build_ai_context(
        [observation],
        entities=[{"name": "Acme"}],
        signals=[{"type": "growth"}],
        metadata={"domain": "market"},
    )

    assert first == second


def test_mapping_without_statement_uses_mapping_representation():
    observation = observation_from_mapping(
        {"value": 123},
        source="test",
        category="measurement",
    )

    assert "value" in observation.statement
    assert "123" in observation.statement
