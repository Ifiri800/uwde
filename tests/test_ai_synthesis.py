from backend.app.services.intelligence.ai.context import build_ai_context
from backend.app.services.intelligence.ai.models import AIObservation, AIReasoning
from backend.app.services.intelligence.ai.synthesis import synthesize


def test_synthesize_empty_context():
    context = build_ai_context()

    reasoning = AIReasoning(
        conclusion="No usable intelligence.",
        confidence=0.0,
    )

    result = synthesize(context, reasoning)

    assert result.confidence == 0.0
    assert "Insufficient intelligence data" in result.summary
    assert result.key_findings == ()


def test_synthesize_single_observation():
    observation = AIObservation(
        source="market",
        category="expansion",
        statement="Market expansion detected.",
        confidence=0.8,
    )

    context = build_ai_context([observation])

    reasoning = AIReasoning(
        conclusion="The market shows expansion activity.",
        rationale=("Expansion signal detected.",),
        confidence=0.8,
    )

    result = synthesize(context, reasoning)

    assert result.confidence == 0.8
    assert result.key_findings == (
        "Market expansion detected.",
    )
    assert "The market shows expansion activity." in result.summary
    assert "Expansion signal detected." in result.implications


def test_synthesize_multiple_observations():
    observations = (
        AIObservation(
            source="market",
            category="expansion",
            statement="Market expansion detected.",
            confidence=0.9,
        ),
        AIObservation(
            source="competitive",
            category="threat",
            statement="Competitive pressure increased.",
            confidence=0.7,
        ),
    )

    context = build_ai_context(observations)

    reasoning = AIReasoning(
        conclusion="The market is becoming more competitive.",
        rationale=(
            "Expansion activity is increasing.",
            "Competitive pressure is elevated.",
        ),
        confidence=0.8,
    )

    result = synthesize(context, reasoning)

    assert result.confidence == 0.8
    assert len(result.key_findings) == 2
    assert len(result.implications) == 3


def test_synthesis_confidence_is_bounded_by_reasoning():
    observation = AIObservation(
        source="forecasting",
        category="forecast",
        statement="Growth is expected.",
        confidence=0.6,
    )

    context = build_ai_context([observation])

    reasoning = AIReasoning(
        conclusion="Growth is likely.",
        confidence=0.9,
    )

    result = synthesize(context, reasoning)

    assert result.confidence == 0.6
