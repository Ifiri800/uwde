from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RecognizedEntity:
    """An entity identified and normalized from source content."""

    text: str
    entity_type: str
    normalized_value: str
    confidence: float = 1.0
    start: int = 0
    end: int = 0

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("text is required")

        if not self.entity_type.strip():
            raise ValueError("entity_type is required")

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


_PERCENTAGE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_CURRENCY_PATTERN = re.compile(
    r"(?:(?:USD|EUR|GBP|NGN)\s*)?\$?\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:\s*(?:USD|EUR|GBP|NGN))?"
)

_DATE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"|"
    r"\d{1,2}/\d{1,2}/\d{2,4}"
    r"|"
    r"(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)

_LOCATION_PATTERN = re.compile(
    r"\b(?:Nigeria|Ghana|Kenya|South Africa|United States|"
    r"United Kingdom|Abuja|Lagos|London|New York)\b",
    re.IGNORECASE,
)

_COMPANY_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9&.-]*(?:\s+[A-Z][A-Za-z0-9&.-]*)*"
    r"\s+(?:Ltd|Limited|Inc|Incorporated|Corp|Corporation|PLC|LLC)\b"
)


def _normalize(value: str) -> str:
    return " ".join(value.strip().split())


def _entity(
    text: str,
    entity_type: str,
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
    )


def _find_entities(
    pattern: re.Pattern[str],
    text: str,
    entity_type: str,
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


def recognize_entities(text: str) -> EntityRecognitionResult:
    """
    Recognize common business and intelligence entities.

    This deterministic implementation is provider-independent. A future
    NER model or LLM can enrich the same contract without changing
    downstream UWDE consumers.
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
            "organization",
            0.90,
        )
    )

    entities.extend(
        _find_entities(
            _LOCATION_PATTERN,
            text,
            "location",
            0.95,
        )
    )

    entities.extend(
        _find_entities(
            _DATE_PATTERN,
            text,
            "date",
            0.95,
        )
    )

    entities.extend(
        _find_entities(
            _PERCENTAGE_PATTERN,
            text,
            "percentage",
            0.98,
        )
    )

    entities.extend(
        _find_entities(
            _CURRENCY_PATTERN,
            text,
            "currency",
            0.90,
        )
    )

    # Remove exact duplicate spans while preserving detection order.
    unique: dict[tuple[int, int, str], RecognizedEntity] = {}

    for entity in entities:
        unique[(entity.start, entity.end, entity.entity_type)] = entity

    ordered = tuple(
        sorted(
            unique.values(),
            key=lambda entity: (entity.start, entity.end),
        )
    )

    return EntityRecognitionResult(entities=ordered)
