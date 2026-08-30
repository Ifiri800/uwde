from __future__ import annotations

from dataclasses import asdict, dataclass

from .context import build_ai_context, observation_from_mapping
from .entities import EntityRecognitionResult, recognize_entities
from .evaluation import AIEvaluation, evaluate_intelligence_result
from .normalization import EntityNormalizationResult, normalize_entities
from .relationships import RelationshipExtractionResult, extract_relationships
from .reasoning import reason
from .recommendation import recommend
from .semantic import SemanticAnalysis, analyze_semantics
from .synthesis import AISynthesis, synthesize
from .models import AIContext, AIRecommendation, AIReasoning


@dataclass(frozen=True)
class AIOrchestrationResult:
    """Complete deterministic AI-layer processing result."""

    semantic: SemanticAnalysis
    recognition: EntityRecognitionResult
    normalization: EntityNormalizationResult
    relationships: RelationshipExtractionResult
    context: AIContext
    reasoning: AIReasoning
    synthesis: AISynthesis
    recommendation: AIRecommendation
    evaluation: AIEvaluation

    def to_dict(self) -> dict:
        """Return a JSON-serializable representation of the AI result."""
        return asdict(self)


def orchestrate_context(context: AIContext) -> AIOrchestrationResult:
    """
    Execute the downstream AI intelligence pipeline from an existing
    normalized AI context.

    This entry point is used when another UWDE subsystem has already
    produced structured intelligence observations and should not be
    converted back into raw text.
    """

    if not isinstance(context, AIContext):
        raise TypeError("context must be an AIContext")

    reasoning_result = reason(context)

    synthesis_result = synthesize(
        context,
        reasoning_result,
    )

    recommendation_result = recommend(
        context,
        reasoning_result,
        synthesis_result,
    )

    evaluation_result = evaluate_intelligence_result(
        context,
        reasoning_result,
        synthesis_result,
        recommendation_result,
    )

    return AIOrchestrationResult(
        semantic=SemanticAnalysis(
            topics=(),
            concepts=(),
            confidence=0.0,
        ),
        recognition=EntityRecognitionResult(
            entities=(),
        ),
        normalization=EntityNormalizationResult(
            entities=(),
        ),
        relationships=RelationshipExtractionResult(
            relationships=(),
        ),
        context=context,
        reasoning=reasoning_result,
        synthesis=synthesis_result,
        recommendation=recommendation_result,
        evaluation=evaluation_result,
    )


def orchestrate(text: str) -> AIOrchestrationResult:
    """
    Execute the complete provider-independent AI intelligence pipeline.

    The orchestrator coordinates semantic analysis, entity recognition,
    normalization, relationship extraction, context construction,
    reasoning, synthesis, and recommendation.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    semantic = analyze_semantics(text)

    recognition = recognize_entities(text)

    normalization = normalize_entities(
        recognition.entities
    )

    relationships = extract_relationships(
        text,
        normalization.entities,
    )

    observations = []

    for concept in semantic.concepts:
        observations.append(
            {
                "source": "semantic",
                "category": concept.category,
                "statement": concept.name,
                "confidence": concept.confidence,
            }
        )

    for entity in normalization.entities:
        observations.append(
            {
                "source": "entity",
                "category": entity.entity_type,
                "statement": entity.canonical_value,
                "confidence": entity.confidence,
                "evidence": entity.source_texts,
            }
        )

    for relationship in relationships.relationships:
        observations.append(
            {
                "source": "relationship",
                "category": relationship.predicate,
                "statement": (
                    f"{relationship.subject.canonical_value} "
                    f"{relationship.predicate} "
                    f"{relationship.object.canonical_value}"
                ),
                "confidence": relationship.confidence,
                "evidence": (relationship.evidence,),
            }
        )

    ai_observations = tuple(
        observation_from_mapping(item, source=str(item["source"]), category=str(item["category"]))
        for item in observations
    )

    context = build_ai_context(
        ai_observations,
        entities=(
            {
                "entity_type": entity.entity_type,
                "canonical_value": entity.canonical_value,
                "aliases": entity.aliases,
                "confidence": entity.confidence,
            }
            for entity in normalization.entities
        ),
        signals=(
            {
                "predicate": relationship.predicate,
                "subject": relationship.subject.canonical_value,
                "object": relationship.object.canonical_value,
                "confidence": relationship.confidence,
            }
            for relationship in relationships.relationships
        ),
        metadata={
            "semantic_confidence": semantic.confidence,
            "entity_count": recognition.entity_count,
            "normalized_entity_count": normalization.entity_count,
            "relationship_count": relationships.relationship_count,
        },
    )

    reasoning_result = reason(context)

    synthesis_result = synthesize(
        context,
        reasoning_result,
    )

    recommendation_result = recommend(
        context,
        reasoning_result,
        synthesis_result,
    )

    evaluation_result = evaluate_intelligence_result(
        context,
        reasoning_result,
        synthesis_result,
        recommendation_result,
    )

    return AIOrchestrationResult(
        semantic=semantic,
        recognition=recognition,
        normalization=normalization,
        relationships=relationships,
        context=context,
        reasoning=reasoning_result,
        synthesis=synthesis_result,
        recommendation=recommendation_result,
        evaluation=evaluation_result,
    )
