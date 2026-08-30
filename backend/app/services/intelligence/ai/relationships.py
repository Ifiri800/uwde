from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityReference:
    """Reference to a canonical entity participating in a relationship."""

    entity_type: str
    canonical_value: str

    def __post_init__(self) -> None:
        if not self.entity_type.strip():
            raise ValueError("entity_type is required")

        if not self.canonical_value.strip():
            raise ValueError("canonical_value is required")


@dataclass(frozen=True)
class ExtractedRelationship:
    """A deterministic relationship between two normalized entities."""

    subject: EntityReference
    predicate: str
    object: EntityReference
    confidence: float = 1.0
    evidence: str = ""

    def __post_init__(self) -> None:
        if not self.predicate.strip():
            raise ValueError("predicate is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class RelationshipExtractionResult:
    """Structured relationship extraction output."""

    relationships: tuple[ExtractedRelationship, ...] = ()

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)

    @property
    def has_relationships(self) -> bool:
        return bool(self.relationships)


_RELATIONSHIP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "acquired",
        re.compile(
            r"\b(?P<subject>.+?)\s+(?:acquired|bought|purchased)\s+"
            r"(?P<object>.+?)(?:[.!?]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "competitor",
        re.compile(
            r"\b(?P<subject>.+?)\s+(?:competes with|is a competitor of)\s+"
            r"(?P<object>.+?)(?:[.!?]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "expanded_into",
        re.compile(
            r"\b(?P<subject>.+?)\s+(?:expanded into|entered)\s+"
            r"(?P<object>.+?)(?:[.!?]|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "launched",
        re.compile(
            r"\b(?P<subject>.+?)\s+(?:launched|introduced)\s+"
            r"(?P<object>.+?)(?:[.!?]|$)",
            re.IGNORECASE,
        ),
    ),
)


def _entity_key(entity: object) -> tuple[str, str]:
    entity_type = getattr(entity, "entity_type", None)
    canonical_value = getattr(entity, "canonical_value", None)

    if not isinstance(entity_type, str) or not entity_type.strip():
        raise TypeError("normalized entities must provide entity_type")

    if not isinstance(canonical_value, str) or not canonical_value.strip():
        raise TypeError(
            "normalized entities must provide canonical_value"
        )

    return entity_type, canonical_value


def _reference(entity: object) -> EntityReference:
    entity_type, canonical_value = _entity_key(entity)

    return EntityReference(
        entity_type=entity_type,
        canonical_value=canonical_value,
    )


def extract_relationships(
    text: str,
    entities: tuple[object, ...] | list[object],
) -> RelationshipExtractionResult:
    """
    Extract deterministic relationships from text using normalized entities.

    Only relationships whose subject and object can be matched to supplied
    normalized entities are returned. This prevents arbitrary text spans from
    becoming intelligence relationships.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if entities is None:
        raise TypeError("entities must be a sequence")

    normalized_entities = tuple(entities)

    for entity in normalized_entities:
        _entity_key(entity)

    if not text.strip() or not normalized_entities:
        return RelationshipExtractionResult()

    relationships: list[ExtractedRelationship] = []

    for predicate, pattern in _RELATIONSHIP_PATTERNS:
        for match in pattern.finditer(text):
            subject_text = match.group("subject").strip()
            object_text = match.group("object").strip()

            subject_matches = [
                entity
                for entity in normalized_entities
                if entity.canonical_value.lower() in subject_text.lower()
            ]

            object_matches = [
                entity
                for entity in normalized_entities
                if entity.canonical_value.lower() in object_text.lower()
            ]

            if not subject_matches or not object_matches:
                continue

            subject = subject_matches[0]
            target = object_matches[0]

            relationships.append(
                ExtractedRelationship(
                    subject=_reference(subject),
                    predicate=predicate,
                    object=_reference(target),
                    confidence=0.85,
                    evidence=match.group(0).strip(),
                )
            )

    unique: dict[
        tuple[str, str, str, str, str],
        ExtractedRelationship,
    ] = {}

    for relationship in relationships:
        key = (
            relationship.subject.entity_type,
            relationship.subject.canonical_value.lower(),
            relationship.predicate,
            relationship.object.entity_type,
            relationship.object.canonical_value.lower(),
        )
        unique[key] = relationship

    ordered = tuple(
        sorted(
            unique.values(),
            key=lambda relationship: (
                relationship.subject.canonical_value.lower(),
                relationship.predicate,
                relationship.object.canonical_value.lower(),
            ),
        )
    )

    return RelationshipExtractionResult(
        relationships=ordered,
    )
