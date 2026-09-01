from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    PERSON = "person"
    PRODUCT = "product"
    INDUSTRY = "industry"


class EntitySource(str, Enum):
    DETERMINISTIC = "deterministic"
    NLP = "nlp"
    LLM = "llm"
    EXTERNAL = "external"


@dataclass(frozen=True)
class RecognizedEntity:
    """An entity identified and normalized from source content."""

    text: str
    entity_type: EntityType
    normalized_value: str
    confidence: float = 1.0
    start: int = 0
    end: int = 0
    source: EntitySource = EntitySource.DETERMINISTIC

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("text is required")

        if not self.normalized_value.strip():
            raise ValueError("normalized_value is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.start < 0:
            raise ValueError("start cannot be negative")

        if self.end < self.start:
            raise ValueError("end cannot be before start")


@dataclass(frozen=True)
class EntityRecognitionResult:
    """Structured entity recognition output."""

    entities: tuple[RecognizedEntity, ...] = ()

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def has_entities(self) -> bool:
        return bool(self.entities)

    def by_type(
        self,
        entity_type: EntityType,
    ) -> tuple[RecognizedEntity, ...]:
        return tuple(
            entity
            for entity in self.entities
            if entity.entity_type == entity_type
        )


_PERCENTAGE_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)?\s*%"
)

_CURRENCY_PATTERN = re.compile(
    r"(?:"
    r"\b(?:USD|EUR|GBP|NGN)\s*\d+(?:,\d{3})*(?:\.\d+)?"
    r"|"
    r"\$\s*\d+(?:,\d{3})*(?:\.\d+)?"
    r"|"
    r"€\s*\d+(?:,\d{3})*(?:\.\d+)?"
    r"|"
    r"£\s*\d+(?:,\d{3})*(?:\.\d+)?"
    r")",
    re.IGNORECASE,
)

_DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"|"
    r"\d{1,2}/\d{1,2}/\d{2,4}"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)"
    r"\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)

_LOCATION_PATTERN = re.compile(
    r"\b(?:"
    r"Nigeria|Ghana|Kenya|South Africa|"
    r"United States|United Kingdom|"
    r"Abuja|Lagos|Port Harcourt|London|New York"
    r")\b",
    re.IGNORECASE,
)

_COMPANY_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*)*"
    r"\s+(?:Ltd|Limited|Inc|Incorporated|Corp|Corporation|"
    r"PLC|LLC|LLP|GmbH|S\.A\.|AG)\b"
)


def _normalize(value: str) -> str:
    return " ".join(value.strip().split())


def _entity(
    text: str,
    entity_type: EntityType,
    start: int,
    end: int,
    confidence: float = 0.90,
) -> RecognizedEntity:
    return RecognizedEntity(
        text=text,
        entity_type=entity_type,
        normalized_value=_normalize(text),
        confidence=confidence,
        start=start,
        end=end,
        source=EntitySource.DETERMINISTIC,
    )


def _find_entities(
    pattern: re.Pattern[str],
    text: str,
    entity_type: EntityType,
    confidence: float,
) -> list[RecognizedEntity]:
    return [
        _entity(
            match.group(0),
            entity_type,
            match.start(),
            match.end(),
            confidence,
        )
        for match in pattern.finditer(text)
    ]


def _overlaps(
    left: RecognizedEntity,
    right: RecognizedEntity,
) -> bool:
    return left.start < right.end and right.start < left.end


def _priority(entity_type: EntityType) -> int:
    priorities = {
        EntityType.ORGANIZATION: 100,
        EntityType.LOCATION: 90,
        EntityType.DATE: 80,
        EntityType.CURRENCY: 70,
        EntityType.PERCENTAGE: 60,
        EntityType.PERSON: 50,
        EntityType.PRODUCT: 40,
        EntityType.INDUSTRY: 30,
    }

    return priorities.get(entity_type, 0)


def _resolve_overlaps(
    entities: list[RecognizedEntity],
) -> tuple[RecognizedEntity, ...]:
    ranked = sorted(
        entities,
        key=lambda entity: (
            -_priority(entity.entity_type),
            -(entity.end - entity.start),
            entity.start,
        ),
    )

    selected: list[RecognizedEntity] = []

    for entity in ranked:
        if any(_overlaps(entity, existing) for existing in selected):
            continue

        selected.append(entity)

    return tuple(
        sorted(
            selected,
            key=lambda entity: (entity.start, entity.end),
        )
    )


def recognize_entities(text: str) -> EntityRecognitionResult:
    """
    Recognize common business and intelligence entities.

    Deterministic and provider-independent. Future NLP and LLM
    providers can produce the same entity contract.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if not text.strip():
        return EntityRecognitionResult()

    entities: list[RecognizedEntity] = []

    entities.extend(
        _find_entities(
            _COMPANY_PATTERN,
            text,
            EntityType.ORGANIZATION,
            0.90,
        )
    )

    entities.extend(
        _find_entities(
            _LOCATION_PATTERN,
            text,
            EntityType.LOCATION,
            0.95,
        )
    )

    entities.extend(
        _find_entities(
            _DATE_PATTERN,
            text,
            EntityType.DATE,
            0.95,
        )
    )

    entities.extend(
        _find_entities(
            _PERCENTAGE_PATTERN,
            text,
            EntityType.PERCENTAGE,
            0.98,
        )
    )

    entities.extend(
        _find_entities(
            _CURRENCY_PATTERN,
            text,
            EntityType.CURRENCY,
            0.95,
        )
    )

    return EntityRecognitionResult(
        entities=_resolve_overlaps(entities)
    )
