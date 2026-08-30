from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import AIContext, AIRecommendation, AIReasoning, AISynthesis
from .provider import LLMResponse


@dataclass(frozen=True)
class AIGuardrailResult:
    """Result of deterministic validation applied to an AI output."""

    passed: bool
    score: float
    checks: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class AIEvaluation:
    """Structured evaluation of an AI intelligence result."""

    accepted: bool
    score: float
    guardrails: AIGuardrailResult
    rationale: tuple[str, ...] = ()
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")


def evaluate_llm_response(
    response: LLMResponse,
    *,
    minimum_confidence: float = 0.50,
) -> AIEvaluation:
    """
    Deterministically evaluate an external LLM response.

    This evaluator does not claim that a response is factually correct.
    It validates basic output quality and confidence requirements before
    the response is allowed deeper into the intelligence pipeline.
    """

    if not isinstance(response, LLMResponse):
        raise TypeError("response must be an LLMResponse")

    if not 0.0 <= minimum_confidence <= 1.0:
        raise ValueError(
            "minimum_confidence must be between 0.0 and 1.0"
        )

    checks: list[str] = []
    violations: list[str] = []
    warnings: list[str] = []

    if response.content.strip():
        checks.append("non_empty_content")
    else:
        violations.append("empty_content")

    if 0.0 <= response.confidence <= 1.0:
        checks.append("confidence_in_range")
    else:
        violations.append("confidence_out_of_range")

    if response.confidence >= minimum_confidence:
        checks.append("minimum_confidence")
    else:
        warnings.append("confidence_below_threshold")

    if response.provider.strip():
        checks.append("provider_identified")
    else:
        warnings.append("provider_not_identified")

    if response.model.strip():
        checks.append("model_identified")
    else:
        warnings.append("model_not_identified")

    score = len(checks) / (
        len(checks) + len(violations) + len(warnings)
    ) if (checks or violations or warnings) else 0.0

    passed = not violations and response.confidence >= minimum_confidence

    rationale = (
        "LLM output passed deterministic structural validation."
        if passed
        else "LLM output requires review before acceptance."
    )

    guardrails = AIGuardrailResult(
        passed=passed,
        score=score,
        checks=tuple(checks),
        violations=tuple(violations),
        warnings=tuple(warnings),
    )

    return AIEvaluation(
        accepted=passed,
        score=score,
        guardrails=guardrails,
        rationale=(rationale,),
        metadata={
            "minimum_confidence": minimum_confidence,
            "provider": response.provider,
            "model": response.model,
        },
    )


def evaluate_intelligence_result(
    context: AIContext,
    reasoning: AIReasoning,
    synthesis: AISynthesis,
    recommendation: AIRecommendation,
) -> AIEvaluation:
    """
    Evaluate the complete deterministic AI intelligence result.

    This validates that downstream intelligence outputs remain internally
    consistent and confidence-bounded.
    """

    if not isinstance(context, AIContext):
        raise TypeError("context must be an AIContext")

    if not isinstance(reasoning, AIReasoning):
        raise TypeError("reasoning must be an AIReasoning")

    if not isinstance(synthesis, AISynthesis):
        raise TypeError("synthesis must be an AISynthesis")

    if not isinstance(recommendation, AIRecommendation):
        raise TypeError(
            "recommendation must be an AIRecommendation"
        )

    checks: list[str] = []
    violations: list[str] = []
    warnings: list[str] = []

    if context.observations:
        checks.append("context_has_observations")
    else:
        warnings.append("context_has_no_observations")

    if reasoning.conclusion.strip():
        checks.append("reasoning_present")
    else:
        violations.append("reasoning_missing")

    if synthesis.summary.strip():
        checks.append("synthesis_present")
    else:
        violations.append("synthesis_missing")

    if recommendation.recommendation.strip():
        checks.append("recommendation_present")
    else:
        violations.append("recommendation_missing")

    confidence_values = (
        reasoning.confidence,
        synthesis.confidence,
        recommendation.confidence,
    )

    if all(0.0 <= value <= 1.0 for value in confidence_values):
        checks.append("confidence_values_valid")
    else:
        violations.append("confidence_values_invalid")

    score = len(checks) / (
        len(checks) + len(violations) + len(warnings)
    ) if (checks or violations or warnings) else 0.0

    passed = not violations

    guardrails = AIGuardrailResult(
        passed=passed,
        score=score,
        checks=tuple(checks),
        violations=tuple(violations),
        warnings=tuple(warnings),
    )

    return AIEvaluation(
        accepted=passed,
        score=score,
        guardrails=guardrails,
        rationale=(
            "Complete AI intelligence output passed deterministic "
            "structural evaluation."
            if passed
            else "Complete AI intelligence output requires review."
        ,),
        metadata={
            "observation_count": context.observation_count,
            "reasoning_confidence": reasoning.confidence,
            "synthesis_confidence": synthesis.confidence,
            "recommendation_confidence": recommendation.confidence,
        },
    )
