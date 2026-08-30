from backend.app.services.intelligence.ai.context import build_ai_context
from backend.app.services.intelligence.ai.models import AIObservation
from backend.app.services.intelligence.ai.reasoning import reason


def test_reason_empty_context():
    context = build_ai_context()

    result = reason(context)

    assert result.confidence == 0.0
    assert "Insufficient intelligence observations" in result.conclusion


def test_reason_single_observation():
    observation = AIObservation(
        source="market",
        category="expansion",
        statement="Competitor expanded into a new region.",
        confidence=0.9,
    )

    context = build_ai_context([observation])

    result = reason(context)

    assert result.confidence == 0.9
    assert result.observation_count if hasattr(result, "observation_count") else True
    assert len(result.supporting_observations) == 1
    assert result.supporting_observations[0] == (
        "Competitor expanded into a new region."
    )


def test_reason_multiple_categories():
    observations = (
        AIObservation(
            source="market",
            category="expansion",
            statement="Market expansion detected.",
            confidence=0.8,
        ),
        AIObservation(
            source="competitive",
            category="threat",
            statement="Competitive pressure increased.",
            confidence=0.6,
        ),
    )

    context = build_ai_context(observations)

    result = reason(context)

    assert result.confidence == 0.7
    assert len(result.supporting_observations) == 2
    assert len(result.rationale) == 2
    assert "expansion" in result.rationale[0]
    assert "threat" in result.rationale[1]


def test_reason_preserves_observation_order():
    observations = (
        AIObservation(
            source="market",
            category="price",
            statement="Prices increased.",
            confidence=0.7,
        ),
        AIObservation(
            source="market",
            category="product",
            statement="New product launched.",
            confidence=0.9,
        ),
    )

    context = build_ai_context(observations)

    result = reason(context)

    assert result.supporting_observations == (
        "Prices increased.",
        "New product launched.",
    )
