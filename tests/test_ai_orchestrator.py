from backend.app.services.intelligence.ai.orchestrator import (
    AIOrchestrationResult,
    orchestrate,
)


def test_orchestrate_returns_complete_result():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria. "
        "Revenue increased by 15% to NGN 2,500,000."
    )

    assert isinstance(result, AIOrchestrationResult)

    assert result.semantic is not None
    assert result.recognition is not None
    assert result.normalization is not None
    assert result.relationships is not None
    assert result.context is not None
    assert result.reasoning is not None
    assert result.synthesis is not None
    assert result.recommendation is not None


def test_orchestrate_recognition_flows_into_normalization():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert result.recognition.has_entities
    assert result.normalization.has_entities

    organizations = [
        entity
        for entity in result.normalization.entities
        if entity.entity_type == "organization"
    ]

    locations = [
        entity
        for entity in result.normalization.entities
        if entity.entity_type == "location"
    ]

    assert any(
        entity.canonical_value == "Acme Energy Ltd"
        for entity in organizations
    )

    assert any(
        entity.canonical_value == "Nigeria"
        for entity in locations
    )


def test_orchestrate_builds_relationships():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert result.relationships.has_relationships

    relationship = result.relationships.relationships[0]

    assert relationship.predicate == "expanded_into"
    assert relationship.subject.canonical_value == "Acme Energy Ltd"
    assert relationship.object.canonical_value == "Nigeria"


def test_orchestrate_builds_ai_context():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria. "
        "Revenue increased by 15%."
    )

    assert result.context.observation_count > 0
    assert len(result.context.entities) > 0
    assert result.context.signals is not None

    assert "entity_count" in result.context.metadata
    assert "relationship_count" in result.context.metadata


def test_orchestrate_produces_reasoning():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert result.reasoning.conclusion
    assert result.reasoning.confidence >= 0.0
    assert result.reasoning.confidence <= 1.0


def test_orchestrate_produces_synthesis():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert result.synthesis.summary
    assert result.synthesis.key_findings


def test_orchestrate_produces_recommendation():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert result.recommendation.recommendation
    assert result.recommendation.priority in {
        "low",
        "medium",
        "high",
        "critical",
    }


def test_orchestrate_empty_text():
    result = orchestrate("")

    assert result.semantic.topics == ()
    assert result.recognition.entities == ()
    assert result.normalization.entities == ()
    assert result.relationships.relationships == ()
    assert result.context.observation_count == 0
    assert result.reasoning.confidence == 0.0
    assert result.synthesis.confidence == 0.0
    assert result.recommendation.confidence == 0.0


def test_orchestrate_is_deterministic():
    text = (
        "Acme Energy Ltd expanded into Nigeria. "
        "Revenue increased by 15%."
    )

    first = orchestrate(text)
    second = orchestrate(text)

    assert first == second


def test_orchestrate_rejects_non_string_input():
    try:
        orchestrate(None)
    except TypeError as exc:
        assert "text must be a string" in str(exc)
    else:
        raise AssertionError("Expected TypeError")

def test_orchestrate_produces_evaluation():
    from backend.app.services.intelligence.ai.evaluation import (
        AIEvaluation,
    )

    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    assert isinstance(result.evaluation, AIEvaluation)
    assert result.evaluation.accepted
    assert result.evaluation.guardrails.passed


def test_orchestrate_evaluation_matches_result():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria. "
        "Revenue increased by 15%."
    )

    assert result.evaluation.metadata is not None
    assert (
        result.evaluation.metadata["observation_count"]
        == result.context.observation_count
    )
    assert (
        result.evaluation.metadata["reasoning_confidence"]
        == result.reasoning.confidence
    )
    assert (
        result.evaluation.metadata["synthesis_confidence"]
        == result.synthesis.confidence
    )
    assert (
        result.evaluation.metadata["recommendation_confidence"]
        == result.recommendation.confidence
    )

def test_ai_orchestration_result_is_serializable():
    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria. "
        "Revenue increased by 15% to NGN 2,500,000."
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert "semantic" in data
    assert "context" in data
    assert "reasoning" in data
    assert "synthesis" in data
    assert "recommendation" in data
    assert "evaluation" in data


def test_ai_orchestration_result_is_json_serializable():
    import json

    result = orchestrate(
        "Acme Energy Ltd expanded into Nigeria."
    )

    serialized = json.dumps(result.to_dict())

    assert serialized
