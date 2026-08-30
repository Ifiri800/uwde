from __future__ import annotations

from .models import AIContext, AIReasoning, AISynthesis


def synthesize(
    context: AIContext,
    reasoning: AIReasoning,
) -> AISynthesis:
    """
    Synthesize intelligence observations and reasoning into a
    human-readable intelligence assessment.

    This implementation is provider-independent. An external AI model
    can later enrich the synthesis without changing the contract.
    """

    if not context.observations:
        return AISynthesis(
            summary="Insufficient intelligence data for synthesis.",
            key_findings=(),
            implications=(
                "Additional intelligence observations are required.",
            ),
            confidence=0.0,
        )

    key_findings = tuple(
        observation.statement
        for observation in context.observations
    )

    implications = (
        reasoning.conclusion,
        *reasoning.rationale,
    )

    summary = (
        f"{reasoning.conclusion} "
        f"The assessment identifies {len(key_findings)} "
        f"key intelligence finding(s)."
    )

    confidence = min(
        reasoning.confidence,
        sum(
            observation.confidence
            for observation in context.observations
        ) / len(context.observations),
    )

    return AISynthesis(
        summary=summary,
        key_findings=key_findings,
        implications=implications,
        confidence=confidence,
    )
