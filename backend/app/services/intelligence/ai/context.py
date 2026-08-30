from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import AIContext, AIObservation


def _to_float(value: Any, default: float = 1.0) -> float:
    """Safely normalize a confidence value to the [0, 1] range."""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return default

    return max(0.0, min(1.0, confidence))


def observation_from_mapping(
    data: Mapping[str, Any],
    *,
    source: str,
    category: str,
) -> AIObservation:
    """
    Convert a deterministic intelligence result into an AI observation.

    The AI layer consumes normalized observations rather than depending
    directly on the internal implementation of individual intelligence
    domains.
    """

    statement = (
        data.get("statement")
        or data.get("description")
        or data.get("conclusion")
        or data.get("message")
        or data.get("name")
    )

    if not statement:
        statement = str(dict(data))

    evidence_value = data.get("evidence", ())
    if isinstance(evidence_value, str):
        evidence = (evidence_value,)
    elif isinstance(evidence_value, Iterable):
        evidence = tuple(str(item) for item in evidence_value)
    else:
        evidence = ()

    return AIObservation(
        source=source,
        category=category,
        statement=str(statement),
        confidence=_to_float(data.get("confidence", 1.0)),
        evidence=evidence,
    )


def build_ai_context(
    observations: Iterable[AIObservation] = (),
    *,
    entities: Iterable[Mapping[str, Any]] = (),
    signals: Iterable[Mapping[str, Any]] = (),
    metadata: Mapping[str, Any] | None = None,
) -> AIContext:
    """
    Build the normalized context consumed by the AI reasoning layer.

    This function deliberately accepts generic mappings so Market,
    Competitive, Forecasting, Risk, Leads, Opportunities, and Scoring
    can remain independent of the AI implementation.
    """

    return AIContext(
        observations=tuple(observations),
        entities=tuple(dict(entity) for entity in entities),
        signals=tuple(dict(signal) for signal in signals),
        metadata=dict(metadata or {}),
    )


def add_observation(
    context: AIContext,
    observation: AIObservation,
) -> AIContext:
    """Return a new context with one additional observation."""

    return AIContext(
        observations=context.observations + (observation,),
        entities=context.entities,
        signals=context.signals,
        metadata=dict(context.metadata),
    )
