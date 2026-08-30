from __future__ import annotations

from .models import AIContext, AIRecommendation, AIReasoning, AISynthesis


def recommend(
    context: AIContext,
    reasoning: AIReasoning,
    synthesis: AISynthesis,
) -> AIRecommendation:
    """
    Produce a deterministic, provider-independent recommendation.

    The recommendation is based on the available intelligence evidence,
    reasoning confidence, synthesis confidence, and observed signals.
    """

    if not context.observations:
        return AIRecommendation(
            recommendation="Collect additional intelligence before taking action.",
            rationale=(
                "No intelligence observations were supplied.",
                "A reliable decision cannot be made from an empty evidence base.",
            ),
            priority="low",
            confidence=0.0,
            actions=(
                "Collect additional intelligence observations.",
                "Validate the available evidence.",
            ),
        )

    confidence = min(reasoning.confidence, synthesis.confidence)

    if confidence >= 0.80:
        priority = "high"
    elif confidence >= 0.60:
        priority = "medium"
    else:
        priority = "low"

    categories = tuple(
        dict.fromkeys(observation.category for observation in context.observations)
    )

    recommendation = (
        f"Prioritize action based on the identified intelligence across "
        f"{len(categories)} categor{'y' if len(categories) == 1 else 'ies'}."
    )

    rationale = (
        synthesis.summary,
        reasoning.conclusion,
        f"Recommendation confidence is {confidence:.2f}.",
    )

    actions = (
        "Review the supporting intelligence evidence.",
        "Validate the highest-priority findings.",
        "Define and assign follow-up actions.",
    )

    return AIRecommendation(
        recommendation=recommendation,
        rationale=rationale,
        priority=priority,
        confidence=confidence,
        actions=actions,
    )
