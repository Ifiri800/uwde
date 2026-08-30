from __future__ import annotations

from collections import defaultdict

from .models import AIContext, AIReasoning


def reason(context: AIContext) -> AIReasoning:
    """
    Produce a deterministic reasoning result from normalized AI context.

    This implementation is provider-independent. An external AI model
    can later enrich or replace the reasoning implementation without
    changing the AI data contracts.
    """

    if not context.observations:
        return AIReasoning(
            conclusion="Insufficient intelligence observations for reasoning.",
            rationale=("No observations were supplied to the AI context.",),
            confidence=0.0,
        )

    grouped: dict[str, list[str]] = defaultdict(list)

    for observation in context.observations:
        grouped[observation.category].append(observation.statement)

    categories = tuple(grouped)

    average_confidence = sum(
        observation.confidence
        for observation in context.observations
    ) / len(context.observations)

    rationale = tuple(
        f"{category}: {len(statements)} observation(s)"
        for category, statements in grouped.items()
    )

    conclusion = (
        f"Reasoning is based on {len(context.observations)} observation(s) "
        f"across {len(categories)} intelligence "
        f"categor{'y' if len(categories) == 1 else 'ies'}."
    )

    supporting = tuple(
        observation.statement
        for observation in context.observations
    )

    return AIReasoning(
        conclusion=conclusion,
        rationale=rationale,
        confidence=average_confidence,
        supporting_observations=supporting,
    )
