from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SemanticConcept:
    """A concept identified from source content."""

    name: str
    category: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")

        if not self.category.strip():
            raise ValueError("category is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True)
class SemanticAnalysis:
    """Structured semantic interpretation of source content."""

    topics: tuple[str, ...] = ()
    concepts: tuple[SemanticConcept, ...] = ()
    intents: tuple[str, ...] = ()
    sentiment: str = "neutral"
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if self.sentiment not in {"positive", "negative", "neutral", "mixed"}:
            raise ValueError(
                "sentiment must be one of: positive, negative, neutral, mixed"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


_KEYWORD_CONCEPTS: dict[str, tuple[str, str]] = {
    "market": ("market", "market"),
    "industry": ("industry", "market"),
    "competitor": ("competitive activity", "competition"),
    "competition": ("competitive activity", "competition"),
    "price": ("pricing", "commercial"),
    "pricing": ("pricing", "commercial"),
    "revenue": ("revenue", "financial"),
    "sales": ("sales activity", "commercial"),
    "demand": ("demand", "market"),
    "growth": ("growth", "performance"),
    "expansion": ("expansion", "strategy"),
    "launch": ("product launch", "product"),
    "product": ("product", "product"),
    "risk": ("risk", "risk"),
    "threat": ("threat", "risk"),
    "opportunity": ("opportunity", "opportunity"),
    "investment": ("investment", "financial"),
    "partnership": ("partnership", "strategy"),
    "regulation": ("regulation", "regulatory"),
    "policy": ("policy", "regulatory"),
    "forecast": ("forecast", "forecasting"),
    "future": ("future outlook", "forecasting"),
}


_POSITIVE_TERMS = {
    "growth",
    "increase",
    "increased",
    "improve",
    "improved",
    "success",
    "opportunity",
    "expansion",
    "gain",
    "positive",
}

_NEGATIVE_TERMS = {
    "decline",
    "decrease",
    "decreased",
    "loss",
    "risk",
    "threat",
    "negative",
    "drop",
    "reduction",
    "failure",
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower()))


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value.strip()))


def analyze_semantics(text: str) -> SemanticAnalysis:
    """
    Produce deterministic semantic analysis from source text.

    This implementation is intentionally provider-independent. A future
    embedding or LLM provider can enrich the analysis without changing
    the semantic contracts consumed by downstream UWDE intelligence.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")

    normalized = text.strip()

    if not normalized:
        return SemanticAnalysis()

    tokens = _tokens(normalized)

    concepts: list[SemanticConcept] = []

    for keyword, (concept, category) in _KEYWORD_CONCEPTS.items():
        if keyword in tokens:
            concepts.append(
                SemanticConcept(
                    name=concept,
                    category=category,
                    confidence=0.80,
                )
            )

    concepts = list(
        {
            (concept.name, concept.category): concept
            for concept in concepts
        }.values()
    )

    topics = _unique(concept.category for concept in concepts)

    intents: list[str] = []

    if any(word in tokens for word in {"forecast", "future", "predict", "expected"}):
        intents.append("forecast")

    if any(word in tokens for word in {"risk", "threat", "danger"}):
        intents.append("risk_assessment")

    if any(word in tokens for word in {"opportunity", "potential", "invest"}):
        intents.append("opportunity_identification")

    if any(word in tokens for word in {"compare", "competitor", "competition"}):
        intents.append("competitive_analysis")

    positive_hits = len(tokens & _POSITIVE_TERMS)
    negative_hits = len(tokens & _NEGATIVE_TERMS)

    if positive_hits and negative_hits:
        sentiment = "mixed"
    elif positive_hits:
        sentiment = "positive"
    elif negative_hits:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    confidence = min(
        1.0,
        0.50
        + (0.05 * len(concepts))
        + (0.05 * len(intents)),
    )

    return SemanticAnalysis(
        topics=topics,
        concepts=tuple(concepts),
        intents=_unique(intents),
        sentiment=sentiment,
        confidence=confidence,
    )
