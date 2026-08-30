from __future__ import annotations

import re
from dataclasses import dataclass

from .entities import RecognizedEntity


@dataclass(frozen=True)
class NormalizedEntity:
    """Canonical representation of a recognized entity."""

    entity_type: str
    canonical_value: str
    aliases: tuple[str, ...] = ()
    confidence: float = 1.0
    source_texts: tuple[str, ...] = ()
    occurrences: int = 1

    def __post_init__(self) -> None:
        if not self.entity_type.strip():
            raise ValueError("entity_type is required")

        if not self.canonical_value.strip():
            raise ValueError("canonical_value is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.occurrences < 1:
            raise ValueError("occurrences must be at least 1")


@dataclass(frozen=True)
class EntityNormalizationResult:
    """Structured entity normalization output."""

    entities: tuple[NormalizedEntity, ...] = ()

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def has_entities(self) -> bool:
        return bool(self.entities)


_ORGANIZATION_SUFFIXES = (
    "corporation",
    "incorporated",
    "limited",
    "company",
    "corp",
    "inc",
    "ltd",
    "plc",
    "llc",
)

_LOCATION_CANONICAL = {
    "nigeria": "Nigeria",
    "ghana": "Ghana",
    "kenya": "Kenya",
    "south africa": "South Africa",
    "united states": "United States",
    "united kingdom": "United Kingdom",
    "abuja": "Abuja",
    "lagos": "Lagos",
    "london": "London",
    "new york": "New York",
}

_CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
}

_CURRENCY_PATTERN = re.compile(
    r"^(?:(USD|EUR|GBP|NGN)\s*)?"
    r"([$€£]?)"
    r"([\d,]+(?:\.\d+)?)"
    r"(?:\s*(USD|EUR|GBP|NGN))?$",
    re.IGNORECASE,
)


def _clean(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_organization(value: str) -> str:
    value = _clean(value)

    parts = value.split()
    if not parts:
        return value

    normalized_parts: list[str] = []

    for part in parts:
        if part.lower() in _ORGANIZATION_SUFFIXES:
            normalized_parts.append(part.lower())
        else:
            normalized_parts.append(part)

    result = " ".join(normalized_parts)

    suffix_map = {
        "corporation": "Corporation",
        "incorporated": "Incorporated",
        "limited": "Limited",
        "company": "Company",
        "corp": "Corp",
        "inc": "Inc",
        "ltd": "Ltd",
        "plc": "PLC",
        "llc": "LLC",
    }

    result_parts = result.split()

    if result_parts:
        suffix = result_parts[-1].lower()
        if suffix in suffix_map:
            result_parts[-1] = suffix_map[suffix]

    return " ".join(result_parts)


def _normalize_location(value: str) -> str:
    cleaned = _clean(value)
    return _LOCATION_CANONICAL.get(cleaned.lower(), cleaned)


def _normalize_percentage(value: str) -> str:
    cleaned = _clean(value).replace(" ", "")
    if cleaned.endswith("%"):
        return cleaned
    return f"{cleaned}%"


def _normalize_currency(value: str) -> str:
    cleaned = _clean(value)
    match = _CURRENCY_PATTERN.match(cleaned)

    if not match:
        return cleaned

    prefix_currency, symbol, amount, suffix_currency = match.groups()

    currency = (
        prefix_currency
        or suffix_currency
        or _CURRENCY_SYMBOLS.get(symbol)
    )

    if currency:
        currency = currency.upper()
        amount = amount.replace(",", "")
        return f"{currency} {amount}"

    return amount.replace(",", "")


def _canonicalize(entity: RecognizedEntity) -> str:
    if entity.entity_type == "organization":
        return _normalize_organization(entity.normalized_value)

    if entity.entity_type == "location":
        return _normalize_location(entity.normalized_value)

    if entity.entity_type == "percentage":
        return _normalize_percentage(entity.normalized_value)

    if entity.entity_type == "currency":
        return _normalize_currency(entity.normalized_value)

    return _clean(entity.normalized_value)


def normalize_entities(
    entities: tuple[RecognizedEntity, ...] | list[RecognizedEntity],
) -> EntityNormalizationResult:
    """
    Normalize recognized entities into deterministic canonical entities.

    Equivalent entities are merged by entity type and canonical value while
    preserving aliases and source occurrences.
    """

    if entities is None:
        raise TypeError("entities must be a sequence")

    grouped: dict[tuple[str, str], list[RecognizedEntity]] = {}

    for entity in entities:
        if not isinstance(entity, RecognizedEntity):
            raise TypeError(
                "entities must contain RecognizedEntity instances"
            )

        canonical = _canonicalize(entity)
        key = (entity.entity_type.lower(), canonical.lower())

        grouped.setdefault(key, []).append(entity)

    normalized: list[NormalizedEntity] = []

    for (entity_type, _), matches in grouped.items():
        canonical = _canonicalize(matches[0])

        aliases: list[str] = []
        source_texts: list[str] = []
        confidences: list[float] = []

        for entity in matches:
            if entity.text not in source_texts:
                source_texts.append(entity.text)

            if entity.text != canonical and entity.text not in aliases:
                aliases.append(entity.text)

            confidences.append(entity.confidence)

        normalized.append(
            NormalizedEntity(
                entity_type=entity_type,
                canonical_value=canonical,
                aliases=tuple(aliases),
                confidence=sum(confidences) / len(confidences),
                source_texts=tuple(source_texts),
                occurrences=len(matches),
            )
        )

    normalized.sort(
        key=lambda entity: (
            entity.entity_type,
            entity.canonical_value.lower(),
        )
    )

    return EntityNormalizationResult(
        entities=tuple(normalized)
    )
