from backend.app.services.intelligence.ai.models import (
    AIContext,
    AIObservation,
    AIReasoning,
    AISynthesis,
)
from backend.app.services.intelligence.ai.recommendation import recommend


def _context() -> AIContext:
    return AIContext(
        observations=(
            AIObservation(
                source="market",
                category="competition",
                statement="Competitive activity is increasing.",
                confidence=0.9,
            ),
            AIObservation(
                source="forecast",
                category="demand",
                statement="Demand is expected to increase.",
                confidence=0.8,
            ),
        )
    )


def test_recommendation_is_generated():
    context = _context()

    reasoning = AIReasoning(
        conclusion="The market shows increasing competitive pressure and demand.",
        rationale=("Competition is increasing.", "Demand is increasing."),
        confidence=0.85,
    )

    synthesis = AISynthesis(
        summary="The market presents an active opportunity requiring attention.",
        key_findings=("Competition is increasing.",),
        implications=("Timely action may improve positioning.",),
        confidence=0.80,
    )

    result = recommend(context, reasoning, synthesis)

    assert result.recommendation
    assert result.rationale
    assert result.actions
    assert result.priority == "high"
    assert result.confidence == 0.80


def test_recommendation_uses_lower_confidence():
    context = _context()

    reasoning = AIReasoning(
        conclusion="Evidence supports action.",
        confidence=0.70,
    )

    synthesis = AISynthesis(
        summary="Evidence is moderately strong.",
        confidence=0.60,
    )

    result = recommend(context, reasoning, synthesis)

    assert result.confidence == 0.60
    assert result.priority == "medium"


def test_empty_context_requests_more_intelligence():
    context = AIContext()

    reasoning = AIReasoning(
        conclusion="No conclusion can be established.",
        confidence=0.0,
    )

    synthesis = AISynthesis(
        summary="Insufficient evidence is available.",
        confidence=0.0,
    )

    result = recommend(context, reasoning, synthesis)

    assert result.priority == "low"
    assert result.confidence == 0.0
    assert "additional intelligence" in result.recommendation.lower()
    assert result.actions


def test_recommendation_is_deterministic():
    context = _context()

    reasoning = AIReasoning(
        conclusion="Evidence supports action.",
        confidence=0.75,
    )

    synthesis = AISynthesis(
        summary="The evidence indicates an actionable situation.",
        confidence=0.75,
    )

    first = recommend(context, reasoning, synthesis)
    second = recommend(context, reasoning, synthesis)

    assert first == second
