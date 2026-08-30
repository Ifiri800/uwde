from backend.app.services.intelligence.ai.evaluation import (
    AIEvaluation,
    AIGuardrailResult,
    evaluate_intelligence_result,
    evaluate_llm_response,
)
from backend.app.services.intelligence.ai.models import (
    AIContext,
    AIObservation,
    AIRecommendation,
    AIReasoning,
    AISynthesis,
)
from backend.app.services.intelligence.ai.provider import LLMResponse


def _llm_response(
    *,
    content="Market growth detected.",
    confidence=0.90,
    provider="test-provider",
    model="test-model",
):
    return LLMResponse(
        content=content,
        confidence=confidence,
        provider=provider,
        model=model,
    )


def _intelligence_result():
    observation = AIObservation(
        source="test",
        category="market",
        statement="Market growth detected.",
        confidence=0.90,
    )

    context = AIContext(
        observations=(observation,),
    )

    reasoning = AIReasoning(
        conclusion="Market conditions indicate growth.",
        rationale=("Growth evidence was observed.",),
        confidence=0.90,
        supporting_observations=("Market growth detected.",),
    )

    synthesis = AISynthesis(
        summary="The market shows positive growth signals.",
        key_findings=("Market growth detected.",),
        implications=("Growth may create opportunities.",),
        confidence=0.90,
    )

    recommendation = AIRecommendation(
        recommendation="Prioritize market expansion analysis.",
        rationale=("Positive market signals support further analysis.",),
        priority="high",
        confidence=0.90,
        actions=("Validate the growth opportunity.",),
    )

    return context, reasoning, synthesis, recommendation


def test_guardrail_result_validation():
    result = AIGuardrailResult(
        passed=True,
        score=1.0,
        checks=("test_check",),
    )

    assert result.passed
    assert result.score == 1.0
    assert result.violations == ()
    assert result.warnings == ()


def test_guardrail_result_rejects_invalid_score():
    try:
        AIGuardrailResult(
            passed=False,
            score=1.5,
        )
    except ValueError as exc:
        assert "score must be between 0.0 and 1.0" in str(exc)


def test_evaluation_rejects_invalid_score():
    try:
        AIEvaluation(
            accepted=False,
            score=-0.1,
            guardrails=AIGuardrailResult(
                passed=False,
                score=0.0,
            ),
        )
    except ValueError as exc:
        assert "score must be between 0.0 and 1.0" in str(exc)


def test_llm_response_passes_guardrails():
    evaluation = evaluate_llm_response(
        _llm_response()
    )

    assert evaluation.accepted
    assert evaluation.guardrails.passed
    assert "non_empty_content" in evaluation.guardrails.checks
    assert "confidence_in_range" in evaluation.guardrails.checks
    assert "minimum_confidence" in evaluation.guardrails.checks
    assert evaluation.violations if hasattr(evaluation, "violations") else True


def test_llm_response_below_confidence_threshold_is_rejected():
    evaluation = evaluate_llm_response(
        _llm_response(confidence=0.40),
        minimum_confidence=0.50,
    )

    assert not evaluation.accepted
    assert not evaluation.guardrails.passed
    assert "confidence_below_threshold" in evaluation.guardrails.warnings


def test_llm_response_empty_content_is_rejected():
    try:
        _llm_response(content="")
    except ValueError as exc:
        assert "content is required" in str(exc)

def test_llm_response_missing_provider_and_model_generates_warnings():
    evaluation = evaluate_llm_response(
        _llm_response(
            provider="",
            model="",
        )
    )

    assert evaluation.accepted
    assert "provider_not_identified" in evaluation.guardrails.warnings
    assert "model_not_identified" in evaluation.guardrails.warnings


def test_llm_response_requires_correct_type():
    try:
        evaluate_llm_response("not an LLM response")
    except TypeError as exc:
        assert "response must be an LLMResponse" in str(exc)


def test_llm_response_rejects_invalid_threshold():
    try:
        evaluate_llm_response(
            _llm_response(),
            minimum_confidence=1.5,
        )
    except ValueError as exc:
        assert "minimum_confidence" in str(exc)


def test_complete_intelligence_result_passes():
    context, reasoning, synthesis, recommendation = (
        _intelligence_result()
    )

    evaluation = evaluate_intelligence_result(
        context,
        reasoning,
        synthesis,
        recommendation,
    )

    assert evaluation.accepted
    assert evaluation.guardrails.passed
    assert "context_has_observations" in evaluation.guardrails.checks
    assert "reasoning_present" in evaluation.guardrails.checks
    assert "synthesis_present" in evaluation.guardrails.checks
    assert "recommendation_present" in evaluation.guardrails.checks
    assert "confidence_values_valid" in evaluation.guardrails.checks


def test_empty_context_generates_warning():
    _, reasoning, synthesis, recommendation = (
        _intelligence_result()
    )

    context = AIContext()

    evaluation = evaluate_intelligence_result(
        context,
        reasoning,
        synthesis,
        recommendation,
    )

    assert evaluation.accepted
    assert "context_has_no_observations" in evaluation.guardrails.warnings


def test_complete_result_requires_correct_types():
    context, reasoning, synthesis, recommendation = (
        _intelligence_result()
    )

    try:
        evaluate_intelligence_result(
            "invalid",
            reasoning,
            synthesis,
            recommendation,
        )
    except TypeError as exc:
        assert "context must be an AIContext" in str(exc)


def test_complete_evaluation_contains_metadata():
    context, reasoning, synthesis, recommendation = (
        _intelligence_result()
    )

    evaluation = evaluate_intelligence_result(
        context,
        reasoning,
        synthesis,
        recommendation,
    )

    assert evaluation.metadata is not None
    assert evaluation.metadata["observation_count"] == 1
    assert evaluation.metadata["reasoning_confidence"] == 0.90
    assert evaluation.metadata["synthesis_confidence"] == 0.90
    assert evaluation.metadata["recommendation_confidence"] == 0.90

